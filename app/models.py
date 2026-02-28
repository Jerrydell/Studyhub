"""
Database Models
SQLAlchemy ORM models for the application
"""

from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    avatar_color = db.Column(db.String(7), default='#0d6efd')
    bio = db.Column(db.String(200), default='')

    subjects = db.relationship('Subject', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    exam_dates = db.relationship('ExamDate', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def initials(self):
        return self.username[:2].upper()

    @property
    def unread_notifications_count(self):
        return self.notifications.filter_by(is_read=False).count()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Subject(db.Model):
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#0d6efd')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    notes = db.relationship('Note', backref='subject', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Subject {self.name}>'

    @property
    def note_count(self):
        return self.notes.count()

    @property
    def mastered_count(self):
        return self.notes.filter_by(progress='mastered').count()

    @property
    def progress_percent(self):
        total = self.note_count
        if total == 0:
            return 0
        return int((self.mastered_count / total) * 100)


class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False, nullable=False)
    progress = db.Column(db.String(20), default="unread", nullable=False)
    color = db.Column(db.String(7), default="#ffffff")  # Note background color
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Note {self.title}>'

    @property
    def preview(self):
        if len(self.content) > 100:
            return self.content[:100] + '...'
        return self.content

    @property
    def progress_badge(self):
        badges = {
            'unread': ('secondary', '📖 Unread'),
            'reading': ('warning', '📝 In Progress'),
            'mastered': ('success', '✅ Mastered')
        }
        return badges.get(self.progress, ('secondary', 'Unread'))


class ExamDate(db.Model):
    __tablename__ = 'exam_dates'

    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(100), nullable=False)
    exam_date = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def days_remaining(self):
        delta = self.exam_date - datetime.utcnow()
        return max(0, delta.days)

    @property
    def is_urgent(self):
        return self.days_remaining <= 7

    def __repr__(self):
        return f'<ExamDate {self.subject_name}>'


# ============================================================================
# STUDY GROUPS
# ============================================================================

import random
import string

group_members = db.Table('group_members',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('study_groups.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)


class StudyGroup(db.Model):
    __tablename__ = 'study_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    invite_code = db.Column(db.String(8), unique=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    creator = db.relationship('User', foreign_keys=[created_by])
    members = db.relationship('User', secondary=group_members, lazy='dynamic')
    shared_notes = db.relationship('SharedNote', backref='group', lazy='dynamic', cascade='all, delete-orphan')

    @staticmethod
    def generate_invite_code():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    @property
    def member_count(self):
        return self.members.count()

    def __repr__(self):
        return f'<StudyGroup {self.name}>'


class SharedNote(db.Model):
    __tablename__ = 'shared_notes'

    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('study_groups.id'), nullable=False)
    shared_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shared_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    note = db.relationship('Note')
    sharer = db.relationship('User')

    def __repr__(self):
        return f'<SharedNote {self.note_id}>'


# ============================================================================
# NOTIFICATIONS
# ============================================================================

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(300), nullable=False)
    icon = db.Column(db.String(10), default='🔔')
    link = db.Column(db.String(200), default='')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Notification {self.title}>'
