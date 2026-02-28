import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'

    @staticmethod
    def get_db_url():
        url = os.environ.get('DATABASE_URL') or \
            'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'studyhub.db')
        if 'postgres' in url:
            url = url.split('?')[0]
            if url.startswith('postgres://'):
                url = url.replace('postgres://', 'postgresql+pg8000://', 1)
            elif url.startswith('postgresql://'):
                url = url.replace('postgresql://', 'postgresql+pg8000://', 1)
        return url

    SQLALCHEMY_DATABASE_URI = get_db_url.__func__()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_SSL_STRICT = False


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
