# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production-2024'
    DEBUG = False
    TESTING = False
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Database settings (using JSON file for simplicity)
    DATABASE_FILE = 'users.json'
    
    # Security settings
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_ATTEMPT_TIMEOUT = 15  # minutes
    PASSWORD_MIN_LENGTH = 8
    
    # Logging settings
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Rate limiting settings
    RATELIMIT_REQUESTS_PER_MINUTE = 60
    RATELIMIT_REQUESTS_PER_HOUR = 1000
    
    # Feature flags
    ENABLE_DARK_MODE = True
    ENABLE_EXPORT = True
    ENABLE_AUDIT_LOGGING = True
    ENABLE_PERFORMANCE_MONITORING = True
    
    # API settings
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # Notification settings
    EMAIL_NOTIFICATIONS_ENABLED = False
    SMS_NOTIFICATIONS_ENABLED = False

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    LOG_LEVEL = 'DEBUG'
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # PythonAnywhere uses HTTPS by default
    LOG_LEVEL = 'WARNING'
    TESTING = False
    PREFERRED_URL_SCHEME = 'https'
    
    # Stricter security in production
    MAX_LOGIN_ATTEMPTS = 3
    LOGIN_ATTEMPT_TIMEOUT = 30

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    DATABASE_FILE = 'test_users.json'
    LOG_LEVEL = 'ERROR'
    RATELIMIT_REQUESTS_PER_MINUTE = 10000  # Disable rate limiting for tests

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
