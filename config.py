import os
from datetime import timedelta

# Base directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration with common settings"""
    
    # Secret key for session management and CSRF protection
    # CRITICAL: Must be changed in production and stored in environment variable
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
     database_url = os.environ.get('DATABASE_URL') or \
    'sqlite:///' + os.path.join(basedir, 'studyhub.db')
	if database_url.startswith('postgres://'):
   	 database_url = database_url.replace('postgres://', 'postgresql://', 1)
	SQLALCHEMY_DATABASE_URI = database_url
        
    
    # Disable modification tracking (saves resources)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration for security
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    
    # WTForms configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_SSL_STRICT = False
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # Require HTTPS in production
    
    # In production, these MUST come from environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Validate that critical production settings exist
    @classmethod
    def init_app(cls, app):
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable must be set in production")


class TestingConfig(Config):
    """Testing environment configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # In-memory database for tests
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing


# Configuration dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
