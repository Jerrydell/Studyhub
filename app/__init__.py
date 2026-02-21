"""
Application Factory Pattern
This creates and configures the Flask application
"""

from flask import Flask, render_template
from config import config
from app.extensions import db, login_manager, migrate, csrf
from werkzeug.middleware.proxy_fix import ProxyFix


def create_app(config_name='default'):
    """
    Application factory function

    Args:
        config_name (str): Configuration to use ('development', 'production', 'testing')

    Returns:
        Flask app instance
    """

    # Create Flask app instance
    app = Flask(__name__)

    # Fix for Railway/proxy CSRF issues
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Load configuration
    app.config.from_object(config[config_name])

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # User loader callback for Flask-Login
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login session management"""
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes import main_bp, auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    # Register error handlers
    register_error_handlers(app)

    # Register custom filters
    register_filters(app)

    # Create database tables (in development)
    with app.app_context():
        db.create_all()

    return app


def register_filters(app):
    """Register custom Jinja2 filters"""
    from datetime import datetime

    @app.template_filter('timeago')
    def timeago_filter(dt):
        """Convert datetime to 'time ago' format"""
        if not dt:
            return ''

        now = datetime.utcnow()
        diff = now - dt
        seconds = diff.total_seconds()

        if seconds < 60:
            return 'just now'
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f'{hours} hour{"s" if hours != 1 else ""} ago'
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f'{days} day{"s" if days != 1 else ""} ago'
        else:
            return dt.strftime('%B %d, %Y')

    @app.template_filter('formatnumber')
    def format_number(value):
        """Format number with commas"""
        try:
            return '{:,}'.format(int(value))
        except (ValueError, TypeError):
            return value


def register_error_handlers(app):
    """Register custom error handlers"""

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
