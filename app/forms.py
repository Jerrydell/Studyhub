"""
WTForms for form handling and validation
All forms include CSRF protection automatically
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import (
    DataRequired, 
    Email, 
    EqualTo, 
    Length, 
    ValidationError
)
from app.models import User


class RegistrationForm(FlaskForm):
    """
    User registration form with comprehensive validation
    """
    
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required'),
            Length(min=3, max=80, message='Username must be between 3 and 80 characters')
        ],
        render_kw={'placeholder': 'Choose a username'}
    )
    
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Please enter a valid email address')
        ],
        render_kw={'placeholder': 'your.email@example.com'}
    )
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required'),
            Length(min=4, message='Password must be at least 4 characters long')
        ],
        render_kw={'placeholder': 'Create a password (min 4 characters)'}
    )
    
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password'),
            EqualTo('password', message='Passwords must match')
        ],
        render_kw={'placeholder': 'Re-enter your password'}
    )
    
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        """
        Custom validator to check if username already exists
        Raised as ValidationError if username is taken
        """
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                'Username already taken. Please choose a different one.'
            )
    
    def validate_email(self, email):
        """
        Custom validator to check if email already exists
        Prevents duplicate accounts
        """
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError(
                'Email already registered. Please use a different email or login.'
            )


class LoginForm(FlaskForm):
    """
    User login form
    Uses email for authentication (more secure than username)
    """
    
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required'),
            Email(message='Please enter a valid email address')
        ],
        render_kw={'placeholder': 'your.email@example.com'}
    )
    
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required')
        ],
        render_kw={'placeholder': 'Enter your password'}
    )
    
    remember_me = BooleanField('Remember Me')
    
    submit = SubmitField('Login')


class SubjectForm(FlaskForm):
    """
    Form for creating and editing subjects
    """
    
    name = StringField(
        'Subject Name',
        validators=[
            DataRequired(message='Subject name is required'),
            Length(min=2, max=100, message='Subject name must be between 2 and 100 characters')
        ],
        render_kw={'placeholder': 'e.g., Mathematics, History, Physics'}
    )
    
    description = TextAreaField(
        'Description',
        validators=[
            Length(max=500, message='Description must be less than 500 characters')
        ],
        render_kw={'placeholder': 'Optional: Brief description of this subject', 'rows': 3}
    )
    
    color = StringField(
        'Color',
        validators=[
            Length(max=7, message='Invalid color format')
        ],
        render_kw={'type': 'color', 'value': '#0d6efd'},
        default='#0d6efd'
    )
    
    submit = SubmitField('Save Subject')


class NoteForm(FlaskForm):
    """
    Form for creating and editing notes
    """
    
    title = StringField(
        'Note Title',
        validators=[
            DataRequired(message='Note title is required'),
            Length(min=2, max=200, message='Title must be between 2 and 200 characters')
        ],
        render_kw={'placeholder': 'e.g., Chapter 5: Linear Equations'}
    )
    
    content = TextAreaField(
        'Content',
        validators=[
            DataRequired(message='Note content is required'),
            Length(min=10, message='Content must be at least 10 characters long')
        ],
        render_kw={'placeholder': 'Write your notes here...', 'rows': 10}
    )
    
    submit = SubmitField('Save Note')

