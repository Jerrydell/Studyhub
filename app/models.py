"""
Database Models
SQLAlchemy ORM models for the application
"""

from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(UserMixin, db.Model):
    """
    User model for authentication and user management
    
    Inherits from UserMixin to get Flask-Login required methods:
    - is_authenticated
    - is_active
    - is_anonymous
    - get_id()
    """
    
    __tablename__ = 'users'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # User credentials
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # User metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    subjects = db.relationship('Subject', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """
        Hash password using Werkzeug's secure method
        Uses pbkdf2:sha256 by default (secure and industry standard)
        
        Args:
            password (str): Plain text password
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Verify password against stored hash
        
        Args:
            password (str): Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        """String representation for debugging"""
        return f'<User {self.username}>'


class Subject(db.Model):
    """
    Subject model for organizing study materials
    
    Relationships:
    - Each subject belongs to one user
    - Each subject can have many notes
    """
    
    __tablename__ = 'subjects'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Subject information
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#0d6efd')  # Hex color code for UI
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    notes = db.relationship('Note', backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        """String representation for debugging"""
        return f'<Subject {self.name}>'
    
    @property
    def note_count(self):
        """Get the number of notes in this subject"""
        return self.notes.count()


class Note(db.Model):
    """
    Note model for storing study notes
    
    Relationships:
    - Each note belongs to one subject
    - Each note belongs to one user (through subject)
    """
    
    __tablename__ = 'notes'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Note content
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False, nullable=False)
    
    # Foreign key
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        """String representation for debugging"""
        return f'<Note {self.title}>'
    
    @property
    def preview(self):
        """Get a preview of the note content (first 100 characters)"""
        if len(self.content) > 100:
            return self.content[:100] + '...'
        return self.content
