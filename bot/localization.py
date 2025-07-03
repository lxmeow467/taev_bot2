"""
Localization module for multi-language support
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class Localizer:
    """Handles multi-language text for the bot"""
    
    def __init__(self):
        self.texts = {
            "en": {
                # Welcome and help messages
                "welcome_message": "🏆 <b>Welcome to the Esports Tournament Bot!</b>\n\nI help manage registrations for VSA and H2H tournaments.",
                "instructions": """
📝 <b>How to register:</b>
1. Set your team name: <code>Bot, my nick TeamName</code>
2. Set your VSA rating: <code>Bot, my VSA rating 42</code>
3. Set your H2H rating: <code>Bot, my H2H rating 38</code>

⚠️ Your registration will need admin confirmation to be finalized.

🎮 You can register for both tournaments using the same team name.
                """,
                "help_message": "🤖 <b>Bot Commands:</b>",
                "command_examples": """
📝 <b>Registration Examples:</b>
• <code>Bot, my nick AwesomeTeam</code>
• <code>Bot, my VSA rating 45</code>
• <code>Bot, my H2H rating 38</code>

👑 <b>Admin Commands:</b>
• <code>/list</code> - View all registrations
• <code>/clear confirm</code> - Clear all data
• <code>/export</code> - Export data to JSON
• <code>/stats</code> - View statistics
                """,
                
                # Button texts
                "help_button": "📖 Help",
                "examples_button": "💡 Examples",
                
                # Success messages
                "team_name_saved": "✅ Team name saved: <b>{team_name}</b>",
                "rating_saved": "✅ {tournament} rating saved: <b>{rating} ⭐</b>",
                "next_step_rating": "Now set your tournament rating using:\n• <code>Bot, my VSA rating X</code>\n• <code>Bot, my H2H rating X</code>",
                "awaiting_confirmation": "⏳ Your registration is awaiting admin confirmation.",
                "registration_confirmed": "✅ Registration confirmed for @{username} in {tournament}: {team_name}",
                
                # Error messages
                "error_occurred": "❌ An error occurred. Please try again.",
                "processing_error": "❌ Error processing your message. Please check the format and try again.",
                "validation_error": "❌ Validation error: {error}",
                "team_name_required": "❌ Please set your team name first using: <code>Bot, my nick TeamName</code>",
                "unrecognized_command": "❓ I didn't understand that command. Use /help for examples.",
                
                # Admin messages
                "admin_only": "⛔ This command is only available to administrators.",
                "no_registrations": "📝 No registrations found.",
                "data_cleared": "🗑️ All tournament data has been cleared.",
                "clear_confirmation": "⚠️ This will delete ALL tournament data. Use <code>/clear confirm</code> to proceed.",
                "export_complete": "📄 Tournament data exported successfully.",
                "no_pending_registration": "❌ No pending registration found for @{username}",
                "confirmation_failed": "❌ Failed to confirm registration.",
                "use_admin_command": "ℹ️ Admins should use proper admin commands for confirmations.",
                
                # Status messages
                "bot_starting": "🚀 Bot is starting up...",
                "bot_ready": "✅ Bot is ready and running!"
            },
            
            "ru": {
                # Welcome and help messages
                "welcome_message": "🏆 <b>Добро пожаловать в бота турниров!</b>\n\nЯ помогаю управлять регистрациями на турниры VSA и H2H.",
                "instructions": """
📝 <b>Как зарегистрироваться:</b>
1. Укажите название команды: <code>Бот, мой ник НазваниеКоманды</code>
2. Укажите VSA рейтинг: <code>Бот, мой рекорд в VSA 42</code>
3. Укажите H2H рейтинг: <code>Бот, мой рекорд в H2H 38</code>

⚠️ Ваша регистрация требует подтверждения администратора.

🎮 Вы можете зарегистрироваться в обоих турнирах с одним названием команды.
                """,
                "help_message": "🤖 <b>Команды бота:</b>",
                "command_examples": """
📝 <b>Примеры регистрации:</b>
• <code>Бот, мой ник КрутаяКоманда</code>
• <code>Бот, мой рекорд в VSA 45</code>
• <code>Бот, мой рекорд в H2H 38</code>

👑 <b>Команды администратора:</b>
• <code>/list</code> - Просмотр всех регистраций
• <code>/clear confirm</code> - Очистить все данные
• <code>/export</code> - Экспорт данных в JSON
• <code>/stats</code> - Просмотр статистики
                """,
                
                # Button texts
                "help_button": "📖 Помощь",
                "examples_button": "💡 Примеры",
                
                # Success messages
                "team_name_saved": "✅ Название команды сохранено: <b>{team_name}</b>",
                "rating_saved": "✅ Рейтинг {tournament} сохранен: <b>{rating} ⭐</b>",
                "next_step_rating": "Теперь укажите ваш рейтинг турнира:\n• <code>Бот, мой рекорд в VSA X</code>\n• <code>Бот, мой рекорд в H2H X</code>",
                "awaiting_confirmation": "⏳ Ваша регистрация ожидает подтверждения администратора.",
                "registration_confirmed": "✅ Регистрация подтверждена для @{username} в {tournament}: {team_name}",
                
                # Error messages
                "error_occurred": "❌ Произошла ошибка. Попробуйте еще раз.",
                "processing_error": "❌ Ошибка обработки сообщения. Проверьте формат и попробуйте снова.",
                "validation_error": "❌ Ошибка валидации: {error}",
                "team_name_required": "❌ Сначала укажите название команды: <code>Бот, мой ник НазваниеКоманды</code>",
                "unrecognized_command": "❓ Не понял команду. Используйте /help для примеров.",
                
                # Admin messages
                "admin_only": "⛔ Эта команда доступна только администраторам.",
                "no_registrations": "📝 Регистраций не найдено.",
                "data_cleared": "🗑️ Все данные турнира были очищены.",
                "clear_confirmation": "⚠️ Это удалит ВСЕ данные турнира. Используйте <code>/clear confirm</code> для продолжения.",
                "export_complete": "📄 Данные турнира успешно экспортированы.",
                "no_pending_registration": "❌ Не найдено ожидающей регистрации для @{username}",
                "confirmation_failed": "❌ Не удалось подтвердить регистрацию.",
                "use_admin_command": "ℹ️ Администраторы должны использовать специальные команды для подтверждений.",
                
                # Status messages
                "bot_starting": "🚀 Бот запускается...",
                "bot_ready": "✅ Бот готов к работе!"
            }
        }
    
    def get_text(self, key: str, language: str = "en", **kwargs) -> str:
        """
        Get localized text
        
        Args:
            key: Text key
            language: Language code
            **kwargs: Format parameters
            
        Returns:
            Localized text
        """
        # Fallback to English if language not supported
        if language not in self.texts:
            language = "en"
        
        # Get text with fallback to English
        text = self.texts[language].get(key)
        if not text:
            text = self.texts["en"].get(key, f"Missing text: {key}")
        
        # Format with provided parameters
        try:
            return text.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing format parameter {e} for text key {key}")
            return text
        except Exception as e:
            logger.error(f"Error formatting text for key {key}: {e}")
            return text
    
    def get_supported_languages(self) -> list:
        """Get list of supported language codes"""
        return list(self.texts.keys())
    
    def add_text(self, language: str, key: str, text: str) -> None:
        """
        Add or update localized text
        
        Args:
            language: Language code
            key: Text key
            text: Localized text
        """
        if language not in self.texts:
            self.texts[language] = {}
        
        self.texts[language][key] = text
        logger.debug(f"Added text for {language}.{key}")
    
    def get_language_from_code(self, language_code: str) -> str:
        """
        Get supported language from Telegram language code
        
        Args:
            language_code: Telegram language code
            
        Returns:
            Supported language code
        """
        if not language_code:
            return "en"
        
        # Direct match
        if language_code in self.texts:
            return language_code
        
        # Language family match (e.g., en-US -> en)
        base_lang = language_code.split('-')[0].split('_')[0]
        if base_lang in self.texts:
            return base_lang
        
        # Default to English
        return "en"
