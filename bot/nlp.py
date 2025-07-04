"""
Natural Language Processing module for parsing user commands
"""

import re
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class NLPProcessor:
    """Processes natural language commands from users"""
    
    def __init__(self):
        # Define regex patterns for different languages
        self.patterns = {
            "ru": {
                "team_name": [
                    r"бот,?\s*мой\s+ник\s+(.+?)(?:\s*$)",
                    r"бот,?\s*команда\s+(.+?)(?:\s*$)",
                    r"бот,?\s*название\s+команды\s+(.+?)(?:\s*$)"
                ],
                "vsa_rating": [
                    r"бот,?\s*мой\s+рекорд\s+в\s+vsa\s+(\d+)",
                    r"бот,?\s*vsa\s+рейтинг\s+(\d+)",
                    r"бот,?\s*рейтинг\s+vsa\s+(\d+)",
                    r"бот,?\s*мой\s+рекорд\s+в\s+vsa\s+х?\s*(\d+)",
                    r"бот,?\s*vsa\s+х?\s*(\d+)"
                ],
                "h2h_rating": [
                    r"бот,?\s*мой\s+рекорд\s+в\s+h2h\s+(\d+)",
                    r"бот,?\s*h2h\s+рейтинг\s+(\d+)",
                    r"бот,?\s*рейтинг\s+h2h\s+(\d+)",
                    r"бот,?\s*мой\s+рекорд\s+в\s+h2h\s+х?\s*(\d+)",
                    r"бот,?\s*h2h\s+х?\s*(\d+)"
                ],
                "admin_confirm": [
                    r"подтвердить\s+@?(\w+)",
                    r"@?(\w+)\s*\+1",
                    r"@?(\w+)\s*подтвержден"
                ]
            },
            "en": {
                "team_name": [
                    r"bot,?\s*my\s+nick(?:name)?\s+(.+?)(?:\s|$)",
                    r"bot,?\s*team\s+name\s+(.+?)(?:\s|$)",
                    r"bot,?\s*my\s+team\s+(.+?)(?:\s|$)"
                ],
                "vsa_rating": [
                    r"bot,?\s*my\s+vsa\s+(?:rating|record)\s+(\d+)",
                    r"bot,?\s*vsa\s+(\d+)",
                    r"bot,?\s*vsa\s+rating\s+(\d+)"
                ],
                "h2h_rating": [
                    r"bot,?\s*my\s+h2h\s+(?:rating|record)\s+(\d+)",
                    r"bot,?\s*h2h\s+(\d+)",
                    r"bot,?\s*h2h\s+rating\s+(\d+)"
                ],
                "admin_confirm": [
                    r"bot,?\s*@?(\w+)\s*\+1",
                    r"bot,?\s*confirm\s+@?(\w+)",
                    r"bot,?\s*@?(\w+)\s*confirmed"
                ]
            }
        }
    
    def parse_message(self, message: str, language: str = "en") -> Optional[Dict[str, Any]]:
        """
        Parse a message and return the extracted command
        
        Args:
            message: The message text to parse
            language: Language code (en, ru)
            
        Returns:
            Dict with command type and extracted data, or None if no match
        """
        if not message:
            return None
        
        # Remove HTML tags
        import re
        message_clean = re.sub(r'<[^>]+>', '', message)
        
        # Normalize message
        message_lower = message_clean.lower().strip()
        
        # Get patterns for the language (fallback to English)
        lang_patterns = self.patterns.get(language, self.patterns["en"])
        
        # Try each pattern type
        for command_type, patterns in lang_patterns.items():
            result = self._match_patterns(message_lower, patterns, command_type)
            if result:
                logger.info(f"Parsed command: {command_type} from message: {message}")
                return result
        
        # Try fallback language if not English/Russian
        if language not in ["en", "ru"]:
            for lang in ["en", "ru"]:
                lang_patterns = self.patterns[lang]
                for command_type, patterns in lang_patterns.items():
                    result = self._match_patterns(message_lower, patterns, command_type)
                    if result:
                        logger.info(f"Parsed command (fallback): {command_type} from message: {message}")
                        return result
        
        logger.debug(f"No command pattern matched for message: {message}")
        return None
    
    def _match_patterns(
        self, 
        message: str, 
        patterns: List[str], 
        command_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Try to match message against a list of patterns
        
        Args:
            message: Normalized message text
            patterns: List of regex patterns to try
            command_type: Type of command being matched
            
        Returns:
            Dict with parsed command data or None
        """
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return self._extract_command_data(match, command_type)
        
        return None
    
    def _extract_command_data(self, match: re.Match, command_type: str) -> Dict[str, Any]:
        """
        Extract command data from regex match
        
        Args:
            match: Regex match object
            command_type: Type of command
            
        Returns:
            Dict with command data
        """
        if command_type == "team_name":
            team_name = match.group(1).strip()
            return {
                "type": "set_team_name",
                "team_name": team_name
            }
        
        elif command_type == "vsa_rating":
            rating = int(match.group(1))
            return {
                "type": "set_vsa_rating",
                "rating": rating
            }
        
        elif command_type == "h2h_rating":
            rating = int(match.group(1))
            return {
                "type": "set_h2h_rating",
                "rating": rating
            }
        
        elif command_type == "admin_confirm":
            username = match.group(1).strip()
            return {
                "type": "admin_confirm",
                "username": username
            }
        
        return {"type": "unknown"}
    
    def get_examples(self, language: str = "en") -> List[str]:
        """
        Get example commands for a language
        
        Args:
            language: Language code
            
        Returns:
            List of example commands
        """
        if language == "ru":
            return [
                "Бот, мой ник TeamAwesome",
                "Бот, мой рекорд в VSA 42",
                "Бот, мой рекорд в H2H 38",
                "Бот @username +1"
            ]
        else:
            return [
                "Bot, my nick TeamAwesome",
                "Bot, my VSA rating 42",
                "Bot, my H2H rating 38",
                "Bot @username +1"
            ]
    
    def validate_extracted_data(self, command: Dict[str, Any]) -> bool:
        """
        Validate extracted command data
        
        Args:
            command: Parsed command dict
            
        Returns:
            True if valid, False otherwise
        """
        command_type = command.get("type")
        
        if command_type == "set_team_name":
            team_name = command.get("team_name", "")
            return len(team_name) > 0 and len(team_name) <= 50
        
        elif command_type in ["set_vsa_rating", "set_h2h_rating"]:
            rating = command.get("rating", -1)
            return 0 <= rating <= 100
        
        elif command_type == "admin_confirm":
            username = command.get("username", "")
            return len(username) >= 5 and len(username) <= 32
        
        return True
