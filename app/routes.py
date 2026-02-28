"""
Application Routes (Blueprints)
Organized by functionality: auth, main, etc.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from datetime import datetime
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User, Subject, Note
from app.forms import RegistrationForm, LoginForm, SubjectForm, NoteForm
from urllib.parse import urlparse as url_parse
from sqlalchemy import or_


# ============================================================================
# AUTHENTICATION BLUEPRINT
# ============================================================================

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration route
    
    GET: Display registration form
    POST: Process registration, create user, redirect to login
    """
    
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        try:
            # Create new user instance
            user = User(
                username=form.username.data,
                email=form.email.data.lower()  # Store email in lowercase
            )
            user.set_password(form.password.data)
            
            # Add to database
            db.session.add(user)
            db.session.commit()
            
            # Success message
            flash('Congratulations! Your account has been created. You can now log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            # Rollback on error
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            print(f"Registration error: {e}")  # Log for debugging
    
    return render_template('auth/register.html', form=form, title='Sign Up')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route
    
    GET: Display login form
    POST: Authenticate user and create session
    """
    
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Query user by email (case-insensitive)
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        # Validate user exists and password is correct
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Log user in (creates session)
        login_user(user, remember=form.remember_me.data)
        
        # Success message
        flash(f'Welcome back, {user.username}!', 'success')
        
        # Redirect to next page if exists, otherwise dashboard
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            # Security: Only redirect to relative URLs (prevent open redirect vulnerability)
            next_page = url_for('main.dashboard')
        
        return redirect(next_page)
    
    return render_template('auth/login.html', form=form, title='Login')


@auth_bp.route('/logout')
@login_required
def logout():
    """
    User logout route
    Destroys session and redirects to home
    """
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))


# ============================================================================
# MAIN APPLICATION BLUEPRINT
# ============================================================================

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    Home page / Landing page
    Shows different content for authenticated vs. non-authenticated users
    """
    return render_template('index.html', title='Home')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """
    User dashboard - main app interface
    Requires authentication (login_required decorator)
    Shows user's subjects and recent notes
    """
    # Get user's subjects ordered by creation date
    subjects = current_user.subjects.order_by(Subject.created_at.desc()).all()
    
    # Get user's recent notes across all subjects
    recent_notes = Note.query.join(Subject).filter(
        Subject.user_id == current_user.id
    ).order_by(Note.updated_at.desc()).limit(5).all()
    
    # Calculate statistics
    total_subjects = current_user.subjects.count()
    total_notes = Note.query.join(Subject).filter(Subject.user_id == current_user.id).count()
    
    return render_template(
        'dashboard.html', 
        title='Dashboard',
        subjects=subjects,
        recent_notes=recent_notes,
        total_subjects=total_subjects,
        total_notes=total_notes
    )


@main_bp.route('/search')
@login_required
def search():
    """
    Search notes and subjects
    Query parameter: q (search query)
    """
    query = request.args.get('q', '').strip()
    
    if not query:
        flash('Please enter a search term.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Search subjects by name or description
    subjects = Subject.query.filter(
        Subject.user_id == current_user.id,
        db.or_(
            Subject.name.ilike(f'%{query}%'),
            Subject.description.ilike(f'%{query}%')
        )
    ).all()
    
    # Search notes by title or content
    notes = Note.query.join(Subject).filter(
        Subject.user_id == current_user.id,
        db.or_(
            Note.title.ilike(f'%{query}%'),
            Note.content.ilike(f'%{query}%')
        )
    ).order_by(Note.updated_at.desc()).all()
    
    return render_template(
        'search_results.html',
        title=f'Search: {query}',
        query=query,
        subjects=subjects,
        notes=notes
    )


# ============================================================================
# SUBJECT MANAGEMENT ROUTES
# ============================================================================

@main_bp.route('/subjects')
@login_required
def subjects():
    """
    Display all subjects for the current user
    """
    subjects = current_user.subjects.order_by(Subject.created_at.desc()).all()
    return render_template('subjects/list.html', title='My Subjects', subjects=subjects)


@main_bp.route('/subject/new', methods=['GET', 'POST'])
@login_required
def create_subject():
    """
    Create a new subject
    """
    form = SubjectForm()
    
    if form.validate_on_submit():
        try:
            subject = Subject(
                name=form.name.data,
                description=form.description.data,
                color=form.color.data,
                user_id=current_user.id
            )
            
            db.session.add(subject)
            db.session.commit()
            
            flash(f'Subject "{subject.name}" created successfully!', 'success')
            return redirect(url_for('main.subjects'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the subject. Please try again.', 'danger')
            print(f"Subject creation error: {e}")
    
    return render_template('subjects/form.html', title='New Subject', form=form, action='Create')


@main_bp.route('/subject/<int:subject_id>')
@login_required
def view_subject(subject_id):
    """
    View a specific subject and its notes
    """
    subject = Subject.query.get_or_404(subject_id)
    
    # Security: Ensure the subject belongs to the current user
    if subject.user_id != current_user.id:
        abort(403)  # Forbidden
    
    # Get all notes for this subject - pinned first, then by update time
    notes = subject.notes.order_by(Note.is_pinned.desc(), Note.updated_at.desc()).all()
    
    return render_template('subjects/view.html', title=subject.name, subject=subject, notes=notes)


@main_bp.route('/subject/<int:subject_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_subject(subject_id):
    """
    Edit an existing subject
    """
    subject = Subject.query.get_or_404(subject_id)
    
    # Security: Ensure the subject belongs to the current user
    if subject.user_id != current_user.id:
        abort(403)
    
    form = SubjectForm()
    
    if form.validate_on_submit():
        try:
            subject.name = form.name.data
            subject.description = form.description.data
            subject.color = form.color.data
            
            db.session.commit()
            
            flash(f'Subject "{subject.name}" updated successfully!', 'success')
            return redirect(url_for('main.view_subject', subject_id=subject.id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the subject. Please try again.', 'danger')
            print(f"Subject update error: {e}")
    
    # Pre-populate form with existing data
    elif request.method == 'GET':
        form.name.data = subject.name
        form.description.data = subject.description
        form.color.data = subject.color
    
    return render_template('subjects/form.html', title='Edit Subject', form=form, action='Update', subject=subject)


@main_bp.route('/subject/<int:subject_id>/delete', methods=['POST'])
@login_required
def delete_subject(subject_id):
    """
    Delete a subject and all its notes (cascade)
    """
    subject = Subject.query.get_or_404(subject_id)
    
    # Security: Ensure the subject belongs to the current user
    if subject.user_id != current_user.id:
        abort(403)
    
    try:
        subject_name = subject.name
        note_count = subject.note_count
        
        db.session.delete(subject)
        db.session.commit()
        
        flash(f'Subject "{subject_name}" and {note_count} note(s) deleted successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the subject. Please try again.', 'danger')
        print(f"Subject deletion error: {e}")
    
    return redirect(url_for('main.subjects'))


# ============================================================================
# NOTE MANAGEMENT ROUTES
# ============================================================================

@main_bp.route('/subject/<int:subject_id>/note/new', methods=['GET', 'POST'])
@login_required
def create_note(subject_id):
    """
    Create a new note in a specific subject
    """
    subject = Subject.query.get_or_404(subject_id)
    
    # Security: Ensure the subject belongs to the current user
    if subject.user_id != current_user.id:
        abort(403)
    
    form = NoteForm()
    
    if form.validate_on_submit():
        try:
            note = Note(
                title=form.title.data,
                content=form.content.data,
                subject_id=subject.id
            )
            
            db.session.add(note)
            db.session.commit()
            
            flash(f'Note "{note.title}" created successfully!', 'success')
            return redirect(url_for('main.view_subject', subject_id=subject.id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the note. Please try again.', 'danger')
            print(f"Note creation error: {e}")
    
    return render_template('notes/form.html', title='New Note', form=form, subject=subject, action='Create')


@main_bp.route('/note/<int:note_id>')
@login_required
def view_note(note_id):
    """
    View a specific note
    """
    note = Note.query.get_or_404(note_id)
    
    # Security: Ensure the note belongs to the current user (through subject)
    if note.subject.user_id != current_user.id:
        abort(403)
    
    return render_template('notes/view.html', title=note.title, note=note)


@main_bp.route('/note/<int:note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    """
    Edit an existing note
    """
    note = Note.query.get_or_404(note_id)
    
    # Security: Ensure the note belongs to the current user
    if note.subject.user_id != current_user.id:
        abort(403)
    
    form = NoteForm()
    
    if form.validate_on_submit():
        try:
            note.title = form.title.data
            note.content = form.content.data
            
            db.session.commit()
            
            flash(f'Note "{note.title}" updated successfully!', 'success')
            return redirect(url_for('main.view_note', note_id=note.id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the note. Please try again.', 'danger')
            print(f"Note update error: {e}")
    
    # Pre-populate form with existing data
    elif request.method == 'GET':
        form.title.data = note.title
        form.content.data = note.content
    
    return render_template('notes/form.html', title='Edit Note', form=form, subject=note.subject, action='Update', note=note)


@main_bp.route('/note/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(note_id):
    """
    Delete a note
    """
    note = Note.query.get_or_404(note_id)
    
    # Security: Ensure the note belongs to the current user
    if note.subject.user_id != current_user.id:
        abort(403)
    
    try:
        note_title = note.title
        subject_id = note.subject_id
        
        db.session.delete(note)
        db.session.commit()
        
        flash(f'Note "{note_title}" deleted successfully.', 'success')
        return redirect(url_for('main.view_subject', subject_id=subject_id))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the note. Please try again.', 'danger')
        print(f"Note deletion error: {e}")
        return redirect(url_for('main.view_note', note_id=note_id))


@main_bp.route('/statistics')
@login_required
def statistics():
    """
    Display user statistics and analytics
    """
    # Get all user's subjects and notes
    subjects = current_user.subjects.all()
    all_notes = Note.query.join(Subject).filter(Subject.user_id == current_user.id).all()
    
    # Calculate statistics
    total_subjects = len(subjects)
    total_notes = len(all_notes)
    
    # Notes per subject
    subject_stats = []
    for subject in subjects:
        note_count = subject.notes.count()
        subject_stats.append({
            'name': subject.name,
            'color': subject.color,
            'note_count': note_count,
            'id': subject.id
        })
    
    # Sort by note count
    subject_stats.sort(key=lambda x: x['note_count'], reverse=True)
    
    # Calculate total word count (approximate)
    total_words = sum(len(note.content.split()) for note in all_notes)
    
    # Average notes per subject
    avg_notes = round(total_notes / total_subjects, 1) if total_subjects > 0 else 0
    
    return render_template(
        'statistics.html',
        title='Statistics',
        total_subjects=total_subjects,
        total_notes=total_notes,
        total_words=total_words,
        avg_notes=avg_notes,
        subject_stats=subject_stats
    )


@main_bp.route('/note/<int:note_id>/export')
@login_required
def export_note(note_id):
    """
    Export a note as a text file
    """
    from flask import Response
    
    note = Note.query.get_or_404(note_id)
    
    # Security check
    if note.subject.user_id != current_user.id:
        abort(403)
    
    # Create text content
    content = f"""
{'='*60}
{note.title}
{'='*60}

Subject: {note.subject.name}
Created: {note.created_at.strftime('%B %d, %Y at %I:%M %p')}
Updated: {note.updated_at.strftime('%B %d, %Y at %I:%M %p')}

{'='*60}

{note.content}

{'='*60}
Exported from StudyHub
{'='*60}
    """.strip()
    
    # Create response with text file
    response = Response(content, mimetype='text/plain')
    response.headers['Content-Disposition'] = f'attachment; filename="{note.title}.txt"'
    
    return response

# ============================================================================
# SEARCH FUNCTIONALITY
# ============================================================================

@main_bp.route('/note/<int:note_id>/pin', methods=['POST'])
@login_required
def toggle_pin_note(note_id):
    """
    Toggle pin status of a note
    """
    note = Note.query.get_or_404(note_id)
    
    # Security check
    if note.subject.user_id != current_user.id:
        abort(403)
    
    note.is_pinned = not note.is_pinned
    db.session.commit()
    
    status = 'pinned' if note.is_pinned else 'unpinned'
    flash(f'Note "{note.title}" {status} successfully!', 'success')
    
    # Redirect to referer or note view
    return redirect(request.referrer or url_for('main.view_note', note_id=note.id))


# ============================================================================
# USER SETTINGS
# ============================================================================

@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """
    User settings and preferences
    """
    if request.method == 'POST':
        # Handle settings update
        username = request.form.get('username', '').strip()
        
        if username and username != current_user.username:
            # Check if username is taken
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already taken.', 'danger')
            else:
                current_user.username = username
                db.session.commit()
                flash('Username updated successfully!', 'success')
        
        return redirect(url_for('main.settings'))
    
    # Get user statistics
    total_subjects = current_user.subjects.count()
    total_notes = Note.query.join(Subject).filter(Subject.user_id == current_user.id).count()
    
    return render_template(
        'settings.html',
        title='Settings',
        total_subjects=total_subjects,
        total_notes=total_notes
    )


# ============================================================================
# AI FEATURES (Google Gemini)
# ============================================================================

from flask import jsonify
from app.ai_service import (
    summarize_note, generate_quiz, explain_topic,
    improve_note, chat_with_note, generate_study_plan
)

@main_bp.route('/note/<int:note_id>/ai/summarize', methods=['POST'])
@login_required
def ai_summarize(note_id):
    note = Note.query.get_or_404(note_id)
    if note.subject.user_id != current_user.id:
        abort(403)
    result = summarize_note(note.title, note.content)
    return jsonify({'result': result})


@main_bp.route('/note/<int:note_id>/ai/quiz', methods=['POST'])
@login_required
def ai_quiz(note_id):
    note = Note.query.get_or_404(note_id)
    if note.subject.user_id != current_user.id:
        abort(403)
    result = generate_quiz(note.title, note.content)
    return jsonify({'result': result})


@main_bp.route('/note/<int:note_id>/ai/explain', methods=['POST'])
@login_required
def ai_explain(note_id):
    note = Note.query.get_or_404(note_id)
    if note.subject.user_id != current_user.id:
        abort(403)
    result = explain_topic(note.title, note.content)
    return jsonify({'result': result})


@main_bp.route('/note/<int:note_id>/ai/improve', methods=['POST'])
@login_required
def ai_improve(note_id):
    note = Note.query.get_or_404(note_id)
    if note.subject.user_id != current_user.id:
        abort(403)
    result = improve_note(note.title, note.content)
    return jsonify({'result': result})


@main_bp.route('/note/<int:note_id>/ai/chat', methods=['POST'])
@login_required
def ai_chat(note_id):
    note = Note.query.get_or_404(note_id)
    if note.subject.user_id != current_user.id:
        abort(403)
    question = request.json.get('question', '').strip()
    if not question:
        return jsonify({'result': 'Please ask a question.'})
    result = chat_with_note(note.title, note.content, question)
    return jsonify({'result': result})


@main_bp.route('/ai/study-plan', methods=['POST'])
@login_required
def ai_study_plan():
    subjects = current_user.subjects.all()
    subjects_data = [
        {'name': s.name, 'note_count': s.note_count}
        for s in subjects
    ]
    if not subjects_data:
        return jsonify({'result': 'You have no subjects yet. Add some subjects and notes first!'})
    result = generate_study_plan(subjects_data)
    return jsonify({'result': result})


# ============================================================================
# PROGRESS TRACKER
# ============================================================================

@main_bp.route('/note/<int:note_id>/progress', methods=['POST'])
@login_required
def update_progress(note_id):
    note = Note.query.get_or_404(note_id)
    if note.subject.user_id != current_user.id:
        abort(403)
    progress = request.json.get('progress', 'unread')
    if progress in ['unread', 'reading', 'mastered']:
        note.progress = progress
        db.session.commit()
    return jsonify({'success': True, 'progress': progress})


# ============================================================================
# EXAM DATES
# ============================================================================

from app.models import ExamDate

@main_bp.route('/exams')
@login_required
def exams():
    exam_list = ExamDate.query.filter_by(user_id=current_user.id).order_by(ExamDate.exam_date).all()
    return render_template('exams.html', title='Exam Dates', exams=exam_list)


@main_bp.route('/exams/add', methods=['POST'])
@login_required
def add_exam():
    subject_name = request.form.get('subject_name', '').strip()
    exam_date_str = request.form.get('exam_date', '')
    notes = request.form.get('notes', '').strip()
    try:
        exam_date = datetime.strptime(exam_date_str, '%Y-%m-%dT%H:%M')
        exam = ExamDate(
            subject_name=subject_name,
            exam_date=exam_date,
            notes=notes,
            user_id=current_user.id
        )
        db.session.add(exam)
        db.session.commit()
        flash('Exam date added!', 'success')
    except Exception as e:
        flash('Error adding exam date.', 'danger')
    return redirect(url_for('main.exams'))


@main_bp.route('/exams/<int:exam_id>/delete', methods=['POST'])
@login_required
def delete_exam(exam_id):
    exam = ExamDate.query.get_or_404(exam_id)
    if exam.user_id != current_user.id:
        abort(403)
    db.session.delete(exam)
    db.session.commit()
    flash('Exam date deleted.', 'success')
    return redirect(url_for('main.exams'))


# ============================================================================
# FLASHCARDS
# ============================================================================

from app.ai_service import call_ai

@main_bp.route('/note/<int:note_id>/flashcards')
@login_required
def flashcards(note_id):
    note = Note.query.get_or_404(note_id)
    if note.subject.user_id != current_user.id:
        abort(403)
    return render_template('flashcards.html', title='Flashcards', note=note)


@main_bp.route('/note/<int:note_id>/flashcards/generate', methods=['POST'])
@login_required
def generate_flashcards(note_id):
    note = Note.query.get_or_404(note_id)
    if note.subject.user_id != current_user.id:
        abort(403)
    prompt = f"""Generate 8 flashcards from this study note. Return ONLY a JSON array like this:
[
  {{"front": "Question or term", "back": "Answer or definition"}},
  ...
]
No extra text, just the JSON array.

Note Title: {note.title}
Note Content: {note.content}"""
    result = call_ai(prompt, max_tokens=1500)
    try:
        import json, re
        match = re.search(r'\[.*\]', result, re.DOTALL)
        if match:
            cards = json.loads(match.group())
            return jsonify({'cards': cards})
    except Exception:
        pass
    return jsonify({'cards': [], 'error': 'Could not generate flashcards. Try again.'})


# ============================================================================
# POMODORO TIMER
# ============================================================================

@main_bp.route('/pomodoro')
@login_required
def pomodoro():
    return render_template('pomodoro.html', title='Pomodoro Timer')


# ============================================================================
# AI EXAM SUGGESTER
# ============================================================================

@main_bp.route('/exams/ai-suggest', methods=['POST'])
@login_required
def ai_suggest_exams():
    from app.ai_service import call_ai
    import json, re

    # Get all user's subjects and notes
    subjects = current_user.subjects.all()
    if not subjects:
        return jsonify({'error': 'No subjects found. Add some subjects and notes first!'})

    subjects_info = []
    for subject in subjects:
        notes = subject.notes.all()
        note_titles = [n.title for n in notes]
        subjects_info.append({
            'subject': subject.name,
            'notes': note_titles,
            'note_count': len(note_titles)
        })

    today = datetime.utcnow().strftime('%Y-%m-%d')
    summary = "\n".join([
        f"- {s['subject']}: {s['note_count']} notes ({', '.join(s['notes'][:3])}{'...' if len(s['notes']) > 3 else ''})"
        for s in subjects_info
    ])

    prompt = f"""You are a study planner. Based on the student's subjects and notes below, suggest realistic exam dates starting from today ({today}).

Subjects and Notes:
{summary}

Return ONLY a JSON array like this (no extra text):
[
  {{
    "subject_name": "Mathematics",
    "exam_date": "2026-03-15T09:00",
    "notes": "Focus on linear equations and measurements"
  }}
]

Generate one exam per subject, spread them out at least 1 week apart, starting 2-4 weeks from today:"""

    result = call_ai(prompt, max_tokens=1000)
    try:
        match = re.search(r'\[.*\]', result, re.DOTALL)
        if match:
            suggestions = json.loads(match.group())
            return jsonify({'suggestions': suggestions})
    except Exception:
        pass
    return jsonify({'error': 'Could not generate suggestions. Please try again.'})


# ============================================================================
# AI NOTE GENERATOR
# ============================================================================

@main_bp.route('/notes/generate', methods=['GET', 'POST'])
@login_required
def ai_generate_note():
    from app.ai_service import call_ai
    subjects = current_user.subjects.all()

    if request.method == 'POST':
        topic = request.form.get('topic', '').strip()
        subject_id = request.form.get('subject_id')
        level = request.form.get('level', 'intermediate')

        prompt = f"""You are an expert teacher. Write a comprehensive and well-structured study note about:

Topic: {topic}
Level: {level}

Structure the note with:
1. A clear introduction
2. Key concepts with explanations
3. Important definitions
4. Examples where relevant
5. Key points to remember

Write it as a proper study note a student can learn from:"""

        generated_content = call_ai(prompt, max_tokens=2000)

        # Clean markdown symbols from generated content
        import re
        generated_content = re.sub(r'\*\*(.+?)\*\*', r'\1', generated_content)  # Remove **bold**
        generated_content = re.sub(r'\*(.+?)\*', r'\1', generated_content)       # Remove *italic*
        generated_content = re.sub(r'^#{1,6}\s+', '', generated_content, flags=re.MULTILINE)  # Remove headers
        generated_content = re.sub(r'^\s*[-*]\s+', '• ', generated_content, flags=re.MULTILINE)  # Clean bullets

        return render_template('ai_note_generator.html',
                               title='AI Note Generator',
                               subjects=subjects,
                               generated_content=generated_content,
                               topic=topic,
                               subject_id=subject_id)

    return render_template('ai_note_generator.html',
                           title='AI Note Generator',
                           subjects=subjects,
                           generated_content=None)


@main_bp.route('/notes/generate/save', methods=['POST'])
@login_required
def save_generated_note():
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    subject_id = request.form.get('subject_id')

    if not title or not content or not subject_id:
        flash('Missing required fields.', 'danger')
        return redirect(url_for('main.ai_generate_note'))

    subject = Subject.query.get_or_404(subject_id)
    if subject.user_id != current_user.id:
        abort(403)

    note = Note(title=title, content=content, subject_id=subject.id)
    db.session.add(note)
    db.session.commit()
    flash('AI generated note saved successfully!', 'success')
    return redirect(url_for('main.view_note', note_id=note.id))


# ============================================================================
# MIND MAP GENERATOR
# ============================================================================

@main_bp.route('/note/<int:note_id>/mindmap')
@login_required
def mindmap(note_id):
    note = Note.query.get_or_404(note_id)
    if note.subject.user_id != current_user.id:
        abort(403)
    return render_template('mindmap.html', title='Mind Map', note=note)


@main_bp.route('/note/<int:note_id>/mindmap/generate', methods=['POST'])
@login_required
def generate_mindmap(note_id):
    from app.ai_service import call_ai
    import json, re

    note = Note.query.get_or_404(note_id)
    if note.subject.user_id != current_user.id:
        abort(403)

    prompt = f"""Analyze this study note and create a mind map structure. Return ONLY a JSON object like this (no extra text):
{{
  "center": "Main Topic",
  "branches": [
    {{
      "name": "Branch 1",
      "color": "#FF6B6B",
      "children": ["subtopic 1", "subtopic 2", "subtopic 3"]
    }},
    {{
      "name": "Branch 2", 
      "color": "#4ECDC4",
      "children": ["subtopic 1", "subtopic 2"]
    }}
  ]
}}

Use 4-6 branches. Colors should be bright hex colors.

Note Title: {note.title}
Note Content: {note.content}"""

    result = call_ai(prompt, max_tokens=1500)
    try:
        match = re.search(r'\{.*\}', result, re.DOTALL)
        if match:
            mindmap_data = json.loads(match.group())
            return jsonify({'mindmap': mindmap_data})
    except Exception:
        pass
    return jsonify({'error': 'Could not generate mind map. Please try again.'})


# ============================================================================
# STUDY GROUPS
# ============================================================================

from app.models import StudyGroup, SharedNote, group_members

@main_bp.route('/groups')
@login_required
def groups():
    my_groups = StudyGroup.query.join(group_members).filter(
        group_members.c.user_id == current_user.id
    ).all()
    created_groups = StudyGroup.query.filter_by(created_by=current_user.id).all()
    all_groups = list({g.id: g for g in my_groups + created_groups}.values())
    return render_template('groups/list.html', title='Study Groups', groups=all_groups)


@main_bp.route('/groups/create', methods=['POST'])
@login_required
def create_group():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    if not name:
        flash('Group name is required.', 'danger')
        return redirect(url_for('main.groups'))

    invite_code = StudyGroup.generate_invite_code()
    while StudyGroup.query.filter_by(invite_code=invite_code).first():
        invite_code = StudyGroup.generate_invite_code()

    group = StudyGroup(
        name=name,
        description=description,
        invite_code=invite_code,
        created_by=current_user.id
    )
    db.session.add(group)
    db.session.flush()
    group.members.append(current_user)
    db.session.commit()
    flash(f'Group created! Invite code: {invite_code}', 'success')
    return redirect(url_for('main.view_group', group_id=group.id))


@main_bp.route('/groups/join', methods=['POST'])
@login_required
def join_group():
    invite_code = request.form.get('invite_code', '').strip().upper()
    group = StudyGroup.query.filter_by(invite_code=invite_code).first()
    if not group:
        flash('Invalid invite code. Please check and try again.', 'danger')
        return redirect(url_for('main.groups'))
    if current_user in group.members.all():
        flash('You are already a member of this group!', 'info')
        return redirect(url_for('main.view_group', group_id=group.id))
    group.members.append(current_user)
    db.session.commit()
    flash(f'You joined {group.name}!', 'success')
    return redirect(url_for('main.view_group', group_id=group.id))


@main_bp.route('/groups/<int:group_id>')
@login_required
def view_group(group_id):
    group = StudyGroup.query.get_or_404(group_id)
    if current_user not in group.members.all() and group.created_by != current_user.id:
        abort(403)
    shared_notes = group.shared_notes.order_by(SharedNote.shared_at.desc()).all()
    user_notes = []
    for subject in current_user.subjects:
        for note in subject.notes:
            user_notes.append(note)
    members = group.members.all()
    return render_template('groups/view.html', title=group.name,
                           group=group, shared_notes=shared_notes,
                           user_notes=user_notes, members=members)


@main_bp.route('/groups/<int:group_id>/share', methods=['POST'])
@login_required
def share_note_to_group(group_id):
    group = StudyGroup.query.get_or_404(group_id)
    if current_user not in group.members.all():
        abort(403)
    note_id = request.form.get('note_id')
    note = Note.query.get_or_404(note_id)
    if note.subject.user_id != current_user.id:
        abort(403)
    existing = SharedNote.query.filter_by(note_id=note.id, group_id=group.id).first()
    if existing:
        flash('This note is already shared in this group!', 'info')
        return redirect(url_for('main.view_group', group_id=group_id))
    shared = SharedNote(note_id=note.id, group_id=group.id, shared_by=current_user.id)
    db.session.add(shared)
    db.session.commit()
    flash(f'Note "{note.title}" shared with the group!', 'success')
    return redirect(url_for('main.view_group', group_id=group_id))


@main_bp.route('/groups/<int:group_id>/leave', methods=['POST'])
@login_required
def leave_group(group_id):
    group = StudyGroup.query.get_or_404(group_id)
    if current_user in group.members.all():
        group.members.remove(current_user)
        db.session.commit()
        flash(f'You left {group.name}.', 'info')
    return redirect(url_for('main.groups'))


# ============================================================================
# LEADERBOARD
# ============================================================================

@main_bp.route('/leaderboard')
@login_required
def leaderboard():
    from app.models import User, Note, Subject
    from sqlalchemy import func

    users = User.query.all()
    leaderboard_data = []

    for user in users:
        total_notes = sum(s.note_count for s in user.subjects)
        total_subjects = user.subjects.count()
        mastered = sum(
            s.notes.filter_by(progress='mastered').count()
            for s in user.subjects
        )
        score = (total_notes * 10) + (total_subjects * 5) + (mastered * 20)
        leaderboard_data.append({
            'username': user.username,
            'total_notes': total_notes,
            'total_subjects': total_subjects,
            'mastered': mastered,
            'score': score,
            'is_me': user.id == current_user.id
        })

    leaderboard_data.sort(key=lambda x: x['score'], reverse=True)
    for i, entry in enumerate(leaderboard_data):
        entry['rank'] = i + 1

    return render_template('leaderboard.html', title='Leaderboard',
                           leaderboard=leaderboard_data)


# ============================================================================
# NOTE COLOR
# ============================================================================

@main_bp.route('/note/<int:note_id>/color', methods=['POST'])
@login_required
def update_note_color(note_id):
    note = Note.query.get_or_404(note_id)
    if note.subject.user_id != current_user.id:
        abort(403)
    color = request.json.get('color', '#ffffff')
    note.color = color
    db.session.commit()
    return jsonify({'success': True, 'color': color})


# ============================================================================
# EXPORT NOTE AS PDF
# ============================================================================

from flask import make_response
import io

@main_bp.route('/note/<int:note_id>/export/pdf')
@login_required
def export_note_pdf(note_id):
    note = Note.query.get_or_404(note_id)
    if note.subject.user_id != current_user.id:
        abort(403)

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib.enums import TA_LEFT, TA_CENTER

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)

        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle('Title', parent=styles['Title'],
                                     fontSize=22, spaceAfter=6,
                                     textColor=colors.HexColor('#1a1a2e'))
        story.append(Paragraph(note.title, title_style))

        # Subtitle info
        info_style = ParagraphStyle('Info', parent=styles['Normal'],
                                    fontSize=10, textColor=colors.grey, spaceAfter=4)
        story.append(Paragraph(f"Subject: {note.subject.name}", info_style))
        story.append(Paragraph(f"Created: {note.created_at.strftime('%B %d, %Y')}", info_style))
        story.append(Paragraph(f"Progress: {note.progress.title()}", info_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0d6efd'), spaceAfter=12))

        # Content
        content_style = ParagraphStyle('Content', parent=styles['Normal'],
                                       fontSize=12, leading=18, spaceAfter=8)
        for line in note.content.split('\n'):
            if line.strip():
                story.append(Paragraph(line.strip(), content_style))
            else:
                story.append(Spacer(1, 6))

        # Footer
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
                                      fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
        story.append(Paragraph("Generated by StudyHub — ABA-TECH", footer_style))

        doc.build(story)
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{note.title}.pdf"'
        return response

    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        return redirect(url_for('main.view_note', note_id=note_id))
