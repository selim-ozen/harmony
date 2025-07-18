"""
Configuration settings for the Discord Music Bot
"""

import os
from typing import Dict, Any

class Config:
    """Bot configuration"""
    
    # Bot settings
    PREFIX = os.getenv('BOT_PREFIX', '!')
    
    # Discord settings
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    
    # Spotify settings
    SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:5000/callback')
    
    # Database settings
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'music_bot.db')
    
    # Web server settings
    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # Security settings
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-this')
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Feature flags
    ENABLE_ANALYTICS = os.getenv('ENABLE_ANALYTICS', 'false').lower() == 'true'
    ENABLE_NOTIFICATIONS = os.getenv('ENABLE_NOTIFICATIONS', 'true').lower() == 'true'
    
    # Rate limiting
    MAX_REQUESTS_PER_MINUTE = int(os.getenv('MAX_REQUESTS_PER_MINUTE', 60))
    
    # Spotify API limits
    MAX_PLAYLIST_TRACKS = int(os.getenv('MAX_PLAYLIST_TRACKS', 100))
    MAX_RECOMMENDATIONS = int(os.getenv('MAX_RECOMMENDATIONS', 20))
    
    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """Validate configuration and return status"""
        errors = []
        warnings = []
        
        # Required settings
        if not cls.DISCORD_TOKEN:
            errors.append("DISCORD_TOKEN is required")
        
        if not cls.SPOTIFY_CLIENT_ID:
            errors.append("SPOTIFY_CLIENT_ID is required")
        
        if not cls.SPOTIFY_CLIENT_SECRET:
            errors.append("SPOTIFY_CLIENT_SECRET is required")
        
        # Warnings for default values
        if cls.FLASK_SECRET_KEY == 'your-secret-key-change-this':
            warnings.append("FLASK_SECRET_KEY is using default value - change this for production")
        
        if not cls.SPOTIFY_REDIRECT_URI.startswith('https://') and 'localhost' not in cls.SPOTIFY_REDIRECT_URI:
            warnings.append("SPOTIFY_REDIRECT_URI should use HTTPS in production")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        """Get configuration summary (without sensitive data)"""
        return {
            'prefix': cls.PREFIX,
            'database_path': cls.DATABASE_PATH,
            'port': cls.PORT,
            'host': cls.HOST,
            'log_level': cls.LOG_LEVEL,
            'features': {
                'analytics': cls.ENABLE_ANALYTICS,
                'notifications': cls.ENABLE_NOTIFICATIONS
            },
            'limits': {
                'requests_per_minute': cls.MAX_REQUESTS_PER_MINUTE,
                'max_playlist_tracks': cls.MAX_PLAYLIST_TRACKS,
                'max_recommendations': cls.MAX_RECOMMENDATIONS
            }
        }

# Environment-specific configurations
class DevelopmentConfig(Config):
    """Development environment configuration"""
    LOG_LEVEL = 'DEBUG'
    ENABLE_ANALYTICS = False

class ProductionConfig(Config):
    """Production environment configuration"""
    LOG_LEVEL = 'INFO'
    ENABLE_ANALYTICS = True

class TestingConfig(Config):
    """Testing environment configuration"""
    DATABASE_PATH = ':memory:'
    LOG_LEVEL = 'WARNING'
    ENABLE_ANALYTICS = False
    ENABLE_NOTIFICATIONS = False

# Get configuration based on environment
def get_config() -> Config:
    """Get configuration based on environment"""
    env = os.getenv('BOT_ENVIRONMENT', 'development').lower()
    
    if env == 'production':
        return ProductionConfig()
    elif env == 'testing':
        return TestingConfig()
    else:
        return DevelopmentConfig()
