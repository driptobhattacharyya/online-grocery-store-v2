import os

class Config:
    # Secret key for securing session data
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-WTF configuration for forms
    WTF_CSRF_SECRET_KEY = 'a_secret_key_for_csrf'

    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'your_jwt_secret_key'
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_COOKIE_CSRF_PROTECT = False  # Set to True if using cookies and want CSRF protection
    JWT_ACCESS_TOKEN_EXPIRES = False  # Set the expiration time for access tokens (e.g., 15 minutes)
    
    # CORS configuration
    CORS_HEADERS = 'Content-Type'
    # Additional JWT configuration options can be added as needed

    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_HOST = "localhost"
    CACHE_REDIS_PORT = 6379
    CACHE_REDIS_DB = 3
    CACHE_DEFAULT_TIMEOUT = 300
