"""
Configuration management for the Medical Management System.
Supports multiple environments: Development, Production, Testing.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / '.env')


class Config:
    """Base configuration class with common settings."""
    
    # Flask Core
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    _db_uri = os.environ.get('DATABASE_URL')
    if _db_uri and _db_uri.startswith('sqlite:///'):
        # Check if it's a relative path (not starting with / or drive letter after prefix)
        _app_db_path = _db_uri.replace('sqlite:///', '')
        if not os.path.isabs(_app_db_path):
            _db_uri = f'sqlite:///{basedir / _app_db_path}'
            
    SQLALCHEMY_DATABASE_URI = _db_uri or \
        f'sqlite:///{basedir / "instance" / "app.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # File Uploads
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or str(basedir / 'static' / 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'webm', 'ogg', 'wav'}
    
    # API Keys
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # Security
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = int(os.environ.get('PERMANENT_SESSION_LIFETIME', 3600))
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens
    
    # Rate Limiting
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'True').lower() == 'true'
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', str(basedir / 'logs' / 'app.log'))
    
    # Disease Matcher
    DISEASE_CSV_PATH = os.environ.get('DISEASE_CSV', str(basedir / 'data' / 'diseases.csv'))
    
    # Supported Languages
    LANGUAGES = ['en', 'es']

    
    @staticmethod
    def init_app(app):
        """Initialize application with this configuration."""
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Path(Config.LOG_FILE).parent, exist_ok=True)
        os.makedirs(basedir / 'instance', exist_ok=True)
        
        # Validate critical configuration
        if not Config.GEMINI_API_KEY:
            print("WARNING: GEMINI_API_KEY not set. AI features will not work.")


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = False  # Set to True to see SQL queries


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False
    
    # Production should always use secure cookies
    SESSION_COOKIE_SECURE = True
    
    # Stricter rate limiting in production
    RATELIMIT_DEFAULT = "100 per day;20 per hour"
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Additional production checks
        if not Config.SECRET_KEY or Config.SECRET_KEY == 'dev-secret-key-change-in-production':
            raise ValueError("SECRET_KEY must be set in production!")
        
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY must be set in production!")


class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    DEBUG = True
    
    # Use in-memory database for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env_name=None):
    """Get configuration object based on environment name."""
    if env_name is None:
        env_name = os.environ.get('FLASK_ENV', 'development')
    return config.get(env_name, config['default'])
