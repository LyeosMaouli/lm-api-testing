"""
Configuration management for Brevo API integration
"""
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

# Load environment variables
load_dotenv()

@dataclass
class Config:
    """Application configuration with validation"""
    
    # Brevo API settings
    brevo_api_key: Optional[str] = None
    brevo_sender_email: Optional[str] = None
    brevo_sender_name: str = "API Integration"
    brevo_base_url: str = "https://api.brevo.com/v3"
    
    # Flask settings
    flask_env: str = "development"
    flask_debug: bool = True
    flask_host: str = "127.0.0.1"
    flask_port: int = 5000
    
    # Security settings
    rate_limit_default: str = "200 per day, 50 per hour"
    rate_limit_email: str = "5 per minute"
    rate_limit_events: str = "10 per minute"
    
    # Request settings
    request_timeout: int = 10
    max_content_length: int = 16 * 1024 * 1024  # 16MB
    
    def __post_init__(self):
        """Load values from environment variables"""
        self.brevo_api_key = os.getenv('BREVO_API_KEY')
        self.brevo_sender_email = os.getenv('BREVO_SENDER_EMAIL')
        self.brevo_sender_name = os.getenv('BREVO_SENDER_NAME', self.brevo_sender_name)
        
        self.flask_env = os.getenv('FLASK_ENV', self.flask_env)
        self.flask_debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
        self.flask_host = os.getenv('FLASK_HOST', self.flask_host)
        self.flask_port = int(os.getenv('FLASK_PORT', self.flask_port))
        
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not self.brevo_api_key:
            errors.append("BREVO_API_KEY is required")
            
        if not self.brevo_sender_email:
            errors.append("BREVO_SENDER_EMAIL is required for email functionality")
            
        return errors
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.flask_env == 'production'

# Global config instance
config = Config()