"""
Utility functions for the tournament bot
"""

import asyncio
import logging
import functools
from datetime import datetime
from typing import Any, Callable, Dict, Optional
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


def format_timestamp(timestamp: Optional[str]) -> str:
    """
    Format ISO timestamp for display
    
    Args:
        timestamp: ISO format timestamp string
        
    Returns:
        Formatted timestamp
    """
    if not timestamp:
        return "Never"
    
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "Invalid date"


def rate_limit(calls_per_minute: int = 30):
    """
    Rate limiting decorator for command handlers
    
    Args:
        calls_per_minute: Maximum calls per minute per user
    """
    user_calls: Dict[int, list] = {}
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id if update.effective_user else 0
            current_time = datetime.now()
            
            # Initialize user tracking
            if user_id not in user_calls:
                user_calls[user_id] = []
            
            # Clean old calls (older than 1 minute)
            user_calls[user_id] = [
                call_time for call_time in user_calls[user_id]
                if (current_time - call_time).seconds < 60
            ]
            
            # Check rate limit
            if len(user_calls[user_id]) >= calls_per_minute:
                logger.warning(f"Rate limit exceeded for user {user_id}")
                await update.message.reply_text("⚠️ Too many requests. Please wait a moment.")
                return
            
            # Add current call
            user_calls[user_id].append(current_time)
            
            # Execute function
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    return decorator


async def send_safe_message(
    update: Update,
    text: str,
    parse_mode: str = None,
    reply_markup: Any = None,
    max_length: int = 4000
) -> bool:
    """
    Safely send a message with length checking
    
    Args:
        update: Telegram update object
        text: Message text
        parse_mode: Parse mode for formatting
        reply_markup: Reply markup
        max_length: Maximum message length
        
    Returns:
        True if sent successfully
    """
    try:
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length-10] + "...[cut]"
        
        await update.message.reply_text(
            text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
        return True
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        try:
            # Fallback without formatting
            await update.message.reply_text("❌ Error sending formatted message.")
        except Exception:
            pass
        return False


def extract_username(text: str) -> Optional[str]:
    """
    Extract username from text (with or without @)
    
    Args:
        text: Text containing username
        
    Returns:
        Clean username or None
    """
    import re
    
    # Look for @username pattern
    match = re.search(r'@(\w+)', text)
    if match:
        return match.group(1)
    
    # Look for standalone username
    words = text.split()
    for word in words:
        if word.startswith('@'):
            return word[1:]
        elif re.match(r'^\w+$', word) and len(word) >= 5:
            return word
    
    return None


def format_player_list(players: Dict[str, Dict[str, Any]], tournament_type: str) -> str:
    """
    Format player list for display
    
    Args:
        players: Player data dictionary
        tournament_type: Tournament type (VSA/H2H)
        
    Returns:
        Formatted player list
    """
    if not players:
        return f"No players registered for {tournament_type} tournament."
    
    lines = [f"🏆 <b>{tournament_type.upper()} Tournament Players:</b>", ""]
    
    # Sort by rating (descending)
    sorted_players = sorted(
        players.items(),
        key=lambda x: x[1].get('stars', 0),
        reverse=True
    )
    
    for i, (username, data) in enumerate(sorted_players, 1):
        status = "✅" if data.get("confirmed") else "⏳"
        team_name = data.get('name', 'Unknown')
        rating = data.get('stars', 0)
        
        lines.append(f"{i}. {status} {username}: <b>{team_name}</b> ({rating} ⭐)")
    
    return "\n".join(lines)


def log_user_action(action: str):
    """
    Decorator to log user actions
    
    Args:
        action: Action description
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user = update.effective_user
            user_info = f"{user.username} ({user.id})" if user else "Unknown"
            
            logger.info(f"User {user_info} performed action: {action}")
            
            result = await func(update, context, *args, **kwargs)
            
            logger.debug(f"Action {action} completed for user {user_info}")
            return result
        
        return wrapper
    return decorator


async def cleanup_old_data(storage, hours: int = 24) -> int:
    """
    Clean up old temporary registrations
    
    Args:
        storage: Data storage instance
        hours: Hours after which data is considered old
        
    Returns:
        Number of entries cleaned up
    """
    try:
        current_time = datetime.now()
        temp_registrations = storage.get_temp_registrations()
        cleaned_count = 0
        
        for user_id, data in list(temp_registrations.items()):
            try:
                registration_time = datetime.fromisoformat(data["timestamp"])
                if (current_time - registration_time).total_seconds() > hours * 3600:
                    del storage.temp_registrations[user_id]
                    cleaned_count += 1
                    logger.info(f"Cleaned up expired registration for user {user_id}")
            except Exception as e:
                logger.error(f"Error processing registration for user {user_id}: {e}")
        
        if cleaned_count > 0:
            storage._save_data()
        
        return cleaned_count
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return 0


def escape_html(text: str) -> str:
    """
    Escape HTML special characters for Telegram
    
    Args:
        text: Text to escape
        
    Returns:
        HTML-escaped text
    """
    if not text:
        return ""
    
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;'
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    return text


def create_progress_bar(current: int, total: int, length: int = 10) -> str:
    """
    Create a text progress bar
    
    Args:
        current: Current value
        total: Total value
        length: Length of progress bar
        
    Returns:
        Progress bar string
    """
    if total == 0:
        return "░" * length
    
    filled = int((current / total) * length)
    bar = "█" * filled + "░" * (length - filled)
    percentage = int((current / total) * 100)
    
    return f"{bar} {percentage}%"


async def retry_async(func: Callable, max_retries: int = 3, delay: float = 1.0):
    """
    Retry async function with exponential backoff
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        
    Returns:
        Function result
    """
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries:
                raise e
            
            wait_time = delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
            await asyncio.sleep(wait_time)
