"""
Input validation module for tournament registrations
"""

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_team_name(team_name: str) -> None:
    """
    Validate team name input
    
    Args:
        team_name: Team name to validate
        
    Raises:
        ValidationError: If validation fails
    """
    if not team_name:
        raise ValidationError("Team name cannot be empty")
    
    # Strip whitespace
    team_name = team_name.strip()
    
    # Check length
    if len(team_name) < 2:
        raise ValidationError("Team name must be at least 2 characters long")
    
    if len(team_name) > 50:
        raise ValidationError("Team name cannot exceed 50 characters")
    
    # Check for valid characters (allow letters, numbers, spaces, and common symbols)
    if not re.match(r'^[a-zA-Z0-9а-яА-Я\s\-_\.\[\]]+$', team_name):
        raise ValidationError("Team name contains invalid characters")
    
    # Check for excessive spaces
    if '  ' in team_name:
        raise ValidationError("Team name cannot contain multiple consecutive spaces")
    
    # Check for reserved words or inappropriate content
    forbidden_words = ['admin', 'bot', 'moderator', 'null', 'undefined']
    if team_name.lower() in forbidden_words:
        raise ValidationError("Team name contains forbidden words")
    
    logger.debug(f"Team name '{team_name}' passed validation")


def validate_rating(rating: Any) -> None:
    """
    Validate rating input
    
    Args:
        rating: Rating to validate
        
    Raises:
        ValidationError: If validation fails
    """
    # Check if it's a number
    try:
        rating_int = int(rating)
    except (ValueError, TypeError):
        raise ValidationError("Rating must be a valid number")
    
    # Check range
    if rating_int < 0:
        raise ValidationError("Rating cannot be negative")
    
    if rating_int > 100:
        raise ValidationError("Rating cannot exceed 100")
    
    logger.debug(f"Rating {rating_int} passed validation")


def validate_username(username: str) -> None:
    """
    Validate Telegram username
    
    Args:
        username: Username to validate
        
    Raises:
        ValidationError: If validation fails
    """
    if not username:
        raise ValidationError("Username cannot be empty")
    
    # Remove @ if present
    clean_username = username.lstrip('@')
    
    # Check length
    if len(clean_username) < 5:
        raise ValidationError("Username must be at least 5 characters long")
    
    if len(clean_username) > 32:
        raise ValidationError("Username cannot exceed 32 characters")
    
    # Check format (Telegram username rules)
    if not re.match(r'^[a-zA-Z0-9_]+$', clean_username):
        raise ValidationError("Username can only contain letters, numbers, and underscores")
    
    # Must start with a letter
    if not clean_username[0].isalpha():
        raise ValidationError("Username must start with a letter")
    
    logger.debug(f"Username '{clean_username}' passed validation")


def validate_tournament_type(tournament_type: str) -> None:
    """
    Validate tournament type
    
    Args:
        tournament_type: Tournament type to validate
        
    Raises:
        ValidationError: If validation fails
    """
    valid_types = ['vsa', 'h2h']
    
    if not tournament_type:
        raise ValidationError("Tournament type cannot be empty")
    
    if tournament_type.lower() not in valid_types:
        raise ValidationError(f"Tournament type must be one of: {', '.join(valid_types)}")
    
    logger.debug(f"Tournament type '{tournament_type}' passed validation")


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent issues
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Strip whitespace and normalize
    sanitized = text.strip()
    
    # Remove null bytes and control characters
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\t')
    
    # Limit length as safety measure
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]
    
    return sanitized


def validate_command_args(args: list, min_args: int = 0, max_args: int = None) -> None:
    """
    Validate command arguments
    
    Args:
        args: List of command arguments
        min_args: Minimum number of arguments required
        max_args: Maximum number of arguments allowed
        
    Raises:
        ValidationError: If validation fails
    """
    if len(args) < min_args:
        raise ValidationError(f"Command requires at least {min_args} arguments")
    
    if max_args is not None and len(args) > max_args:
        raise ValidationError(f"Command accepts at most {max_args} arguments")
    
    logger.debug(f"Command args validation passed: {len(args)} args")
