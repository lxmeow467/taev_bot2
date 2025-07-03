"""
Configuration module for the Esports Tournament Bot
Handles environment variables and application settings
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for bot settings"""
    
    def __init__(self):
        # Telegram Bot Token (required)
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN environment variable is required")
        
        # Admin usernames (without @)
        admins_str = os.getenv("ADMINS", "")
        self.ADMINS: List[str] = [
            admin.strip().lstrip('@') 
            for admin in admins_str.split(',') 
            if admin.strip()
        ]
        
        # Bot settings
        self.MAX_TEAM_NAME_LENGTH = int(os.getenv("MAX_TEAM_NAME_LENGTH", "50"))
        self.MIN_RATING = int(os.getenv("MIN_RATING", "0"))
        self.MAX_RATING = int(os.getenv("MAX_RATING", "100"))
        
        # Data cleanup settings
        self.CLEANUP_INTERVAL_HOURS = int(os.getenv("CLEANUP_INTERVAL_HOURS", "24"))
        self.UNCONFIRMED_DATA_EXPIRY_HOURS = int(os.getenv("UNCONFIRMED_DATA_EXPIRY_HOURS", "24"))
        
        # Logging settings
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE = os.getenv("LOG_FILE", "bot.log")
        
        # Rate limiting
        self.MAX_REGISTRATIONS_PER_USER = int(os.getenv("MAX_REGISTRATIONS_PER_USER", "2"))
        
        # Localization
        self.DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
        self.SUPPORTED_LANGUAGES = ["en", "ru"]
    
    def is_admin(self, username: str) -> bool:
        """Check if user is an admin"""
        if not username:
            return False
        clean_username = username.lstrip('@').lower()
        return clean_username in [admin.lower() for admin in self.ADMINS]
