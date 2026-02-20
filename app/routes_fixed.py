"""
Application Routes (Blueprints)
Organized by functionality: auth, main, etc.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
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
