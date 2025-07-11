
#!/usr/bin/env python3
"""
Working Tournament Bot - Исправленная версия без ошибок импорта
"""

import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

try:
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    from telegram import Update
    TELEGRAM_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Ошибка импорта Telegram: {e}")
    TELEGRAM_AVAILABLE = False

from dotenv import load_dotenv
from bot.nlp import NLPProcessor
from bot.storage import DataStorage
from bot.localization import Localizer
from bot.validation import ValidationError, validate_team_name, validate_rating

# Загрузка переменных окружения
load_dotenv()

class WorkingTournamentBot:
    """Исправленный турнирный бот"""
    
    def __init__(self):
        self.token = os.getenv('BOT_TOKEN')
        self.admins = [admin.strip().lower() for admin in os.getenv('ADMINS', '').split(',') if admin.strip()]
        
        # Инициализация компонентов
        self.storage = DataStorage()
        self.localizer = Localizer()
        self.nlp = NLPProcessor()
        
        logger.info("Компоненты турнирного бота инициализированы")
    
    async def is_admin(self, update, context) -> bool:
        """Проверка является ли пользователь администратором чата"""
        try:
            user = update.effective_user
            chat = update.effective_chat
            
            # Проверяем статус пользователя в чате
            member = await context.bot.get_chat_member(chat.id, user.id)
            
            # Администраторы и создатели чата имеют права
            return member.status in ['administrator', 'creator']
        except Exception as e:
            logger.error(f"Ошибка при проверке прав администратора: {e}")
            return False
    
    async def handle_start(self, update, context):
        """Обработка команды /start"""
        user = update.effective_user
        lang = 'ru' if user.language_code and user.language_code.startswith('ru') else 'en'
        
        welcome_text = self.localizer.get_text("welcome_message", lang)
        instructions_text = self.localizer.get_text("instructions", lang)
        
        await update.message.reply_text(f"{welcome_text}\n\n{instructions_text}")
        
        logger.info(f"Пользователь {user.username or user.first_name or 'Unknown'} запустил бота")
    
    async def handle_help(self, update, context):
        """Обработка команды /help"""
        user = update.effective_user
        lang = 'ru' if user.language_code and user.language_code.startswith('ru') else 'en'
        
        if await self.is_admin(update, context):
            help_text = self.localizer.get_text("help_message", lang)
            examples_text = self.localizer.get_text("command_examples", lang)
            await update.message.reply_text(f"{help_text}\n\n{examples_text}")
        else:
            help_text = (
                "❓ Как зарегистрироваться на турнир:\n\n"
                "1️⃣ Сначала укажите название команды:\n"
                "• Бот, мой ник НазваниеКоманды\n\n"
                "2️⃣ Затем укажите рейтинг для турнира:\n"
                "• Бот, мой рекорд в VSA 99\n"
                "• Бот, мой рекорд в H2H 99\n\n"
                "📝 Примеры команд:\n"
                "• Бот, мой ник SuperTeam\n"
                "• Бот, мой рекорд в VSA 85\n"
                "• Бот, мой рекорд в H2H 78\n\n"
                "⚠️ После регистрации ожидайте подтверждения от администратора."
            )
            await update.message.reply_text(help_text)
    
    async def handle_command(self, update, context):
        """Обработка команды /command (только для админов)"""
        user = update.effective_user
        lang = 'ru' if user.language_code and user.language_code.startswith('ru') else 'en'
        
        if not await self.is_admin(update, context):
            error_text = self.localizer.get_text("admin_only", lang)
            await update.message.reply_text(error_text)
            return
        
        await update.message.reply_text(
            "🎮 Команды администратора:\n\n"
            "/start - Запуск бота\n"
            "/help - Помощь\n"
            "/list - Список всех игроков\n"
            "/stats - Статистика турнира\n"
            "/clear confirm - Очистить все данные\n"
            "/command - Показать эту справку\n\n"
            "📝 Для подтверждения регистрации:\n"
            "Напишите: 'подтвердить @username'"
        )
    
    async def handle_list(self, update, context):
        """Обработка команды /list (только для админов)"""
        user = update.effective_user
        lang = 'ru' if user.language_code and user.language_code.startswith('ru') else 'en'
        
        if not await self.is_admin(update, context):
            error_text = self.localizer.get_text("admin_only", lang)
            await update.message.reply_text(error_text)
            return
        
        players = self.storage.get_all_players()
        temp_registrations = self.storage.get_temp_registrations()
        
        message_parts = []
        
        # VSA Турнир
        vsa_players = players.get("vsa", {})
        if vsa_players:
            message_parts.append("🏆 VSA Турнир:")
            for username, data in vsa_players.items():
                status = "✅" if data.get("confirmed") else "⏳"
                message_parts.append(f"{status} {username}: {data['name']} ({data['stars']} ⭐)")
        else:
            message_parts.append("🏆 VSA Турнир: Нет регистраций")
        
        message_parts.append("")
        
        # H2H Турнир
        h2h_players = players.get("h2h", {})
        if h2h_players:
            message_parts.append("⚔️ H2H Турнир:")
            for username, data in h2h_players.items():
                status = "✅" if data.get("confirmed") else "⏳"
                message_parts.append(f"{status} {username}: {data['name']} ({data['stars']} ⭐)")
        else:
            message_parts.append("⚔️ H2H Турнир: Нет регистраций")
        
        # Ожидающие подтверждения
        if temp_registrations:
            message_parts.append("")
            message_parts.append("⏳ Ожидают подтверждения:")
            for user_id, data in temp_registrations.items():
                username = data.get("username", "Неизвестный")
                tournament = data.get("tournament_type", "unknown").upper()
                team_name = data.get("team_name", "Неизвестно")
                rating = data.get("rating", 0)
                message_parts.append(f"• @{username} - {tournament}: {team_name} ({rating} ⭐)")
        
        final_message = "\n".join(message_parts) if message_parts else "Регистраций не найдено"
        await update.message.reply_text(final_message)
        
        logger.info(f"Админ {user.username} запросил список игроков")
    
    async def handle_stats(self, update, context):
        """Обработка команды /stats (только для админов)"""
        user = update.effective_user
        lang = 'ru' if user.language_code and user.language_code.startswith('ru') else 'en'
        
        if not await self.is_admin(update, context):
            error_text = self.localizer.get_text("admin_only", lang)
            await update.message.reply_text(error_text)
            return
        
        stats = self.storage.get_statistics()
        
        message_parts = [
            "📊 Статистика турнира:",
            "",
            f"🏆 VSA Регистрации: {stats['vsa_total']} всего, {stats['vsa_confirmed']} подтверждено",
            f"⚔️ H2H Регистрации: {stats['h2h_total']} всего, {stats['h2h_confirmed']} подтверждено", 
            f"⏳ Ожидают подтверждения: {stats['pending_confirmations']}",
            "",
            f"📈 Всего пользователей: {stats['total_users']}",
            f"🕐 Последняя регистрация: {stats['last_registration_time'] or 'Никогда'}"
        ]
        
        await update.message.reply_text("\n".join(message_parts))
        logger.info(f"Админ {user.username} запросил статистику")
    
    async def handle_clear(self, update, context):
        """Обработка команды /clear (только для админов)"""
        user = update.effective_user
        lang = 'ru' if user.language_code and user.language_code.startswith('ru') else 'en'
        
        if not await self.is_admin(update, context):
            error_text = self.localizer.get_text("admin_only", lang)
            await update.message.reply_text(error_text)
            return
        
        # Проверка подтверждения
        args = context.args
        if not args or args[0].lower() != "confirm":
            await update.message.reply_text(
                "⚠️ Для очистки данных используйте: /clear confirm\n"
                "Это действие необратимо!"
            )
            return
        
        try:
            self.storage.clear_all_data()
            await update.message.reply_text("✅ Все данные турнира очищены")
            logger.info(f"Админ {user.username} очистил все данные")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при очистке данных: {e}")
    
    async def handle_message(self, update, context):
        """Обработка сообщений на естественном языке"""
        user = update.effective_user
        message_text = update.message.text
        lang = 'ru' if user.language_code and user.language_code.startswith('ru') else 'en'
        
        logger.info(f"Обработка сообщения от {user.username or user.first_name or 'Unknown'}: {message_text}")
        
        try:
            # Сначала проверяем, является ли это ответом на сообщение для подтверждения
            if update.message.reply_to_message and await self.is_admin(update, context):
                await self.handle_reply_confirmation(update, context)
                return
            
            # Парсинг сообщения через NLP процессор
            parsed_command = self.nlp.parse_message(message_text, lang)
            
            logger.info(f"Parsed command: {parsed_command}")
            
            if not parsed_command:
                help_text = (
                    "❓ Не понял команду. Используйте:\n\n"
                    "🔸 Бот, мой ник НазваниеКоманды\n"
                    "🔸 Бот, мой рекорд в VSA 99\n"
                    "🔸 Бот, мой рекорд в H2H 99\n\n"
                    "Или отправьте /help для подробной справки."
                )
                await update.message.reply_text(help_text)
                return
            
            command_type = parsed_command.get("type")
            
            if command_type == "set_team_name":
                await self.handle_team_name(update, context, parsed_command["team_name"], lang)
            
            elif command_type == "set_vsa_rating":
                await self.handle_rating(update, context, "vsa", parsed_command["rating"], lang)
            
            elif command_type == "set_h2h_rating":
                await self.handle_rating(update, context, "h2h", parsed_command["rating"], lang)
            
            elif command_type == "admin_confirm":
                await self.handle_admin_confirm(update, context, parsed_command["username"], lang)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            error_text = self.localizer.get_text("processing_error", lang)
            await update.message.reply_text(error_text)
    
    async def handle_team_name(self, update, context, team_name: str, lang: str):
        """Обработка установки названия команды"""
        user = update.effective_user
        
        try:
            validate_team_name(team_name)
            
            if "registration_data" not in context.user_data:
                context.user_data["registration_data"] = {}
            
            context.user_data["registration_data"]["team_name"] = team_name
            context.user_data["registration_data"]["timestamp"] = datetime.now()
            
            success_text = self.localizer.get_text("team_name_saved", lang, team_name=team_name)
            next_step_text = self.localizer.get_text("next_step_rating", lang)
            
            await update.message.reply_text(f"{success_text}\n\n{next_step_text}")
            logger.info(f"Пользователь {user.username or user.first_name or 'Unknown'} установил название команды: {team_name}")
            
        except ValidationError as e:
            error_text = self.localizer.get_text("validation_error", lang, error=str(e))
            await update.message.reply_text(error_text)
    
    async def handle_rating(self, update, context, tournament_type: str, rating: int, lang: str):
        """Обработка установки рейтинга"""
        user = update.effective_user
        
        try:
            validate_rating(rating)
            
            registration_data = context.user_data.get("registration_data", {})
            if "team_name" not in registration_data:
                error_text = self.localizer.get_text("team_name_required", lang)
                await update.message.reply_text(error_text)
                return
            
            team_name = registration_data["team_name"]
            
            success = await self.storage.save_temp_registration(
                user_id=user.id,
                username=user.username or user.first_name or "Unknown",
                tournament_type=tournament_type,
                team_name=team_name,
                rating=rating
            )
            
            if success:
                success_text = self.localizer.get_text("rating_saved", lang, tournament=tournament_type.upper(), rating=rating)
                confirm_text = self.localizer.get_text("awaiting_confirmation", lang)
                await update.message.reply_text(f"{success_text}\n\n{confirm_text}")
                logger.info(f"Пользователь {user.username or user.first_name or 'Unknown'} зарегистрировался на {tournament_type}: {rating}")
            else:
                error_text = "Регистрация не удалась. Возможно, вы уже зарегистрированы на этот турнир."
                await update.message.reply_text(error_text)
            
        except ValidationError as e:
            error_text = self.localizer.get_text("validation_error", lang, error=str(e))
            await update.message.reply_text(error_text)
    
    async def handle_admin_confirm(self, update, context, target_username: str, lang: str):
        """Обработка подтверждения администратором"""
        user = update.effective_user
        
        if not await self.is_admin(update, context):
            error_text = self.localizer.get_text("admin_only", lang)
            await update.message.reply_text(error_text)
            return
        
        # Поиск ожидающей регистрации
        temp_registrations = self.storage.get_temp_registrations()
        target_data = None
        target_user_id = None
        
        for user_id, data in temp_registrations.items():
            if data.get("username", "").lower() == target_username.lower():
                target_data = data
                target_user_id = user_id
                break
        
        if not target_data:
            error_text = f"Не найдено ожидающих регистраций для @{target_username}"
            await update.message.reply_text(error_text)
            return
        
        success = self.storage.confirm_registration(target_user_id)
        
        if success:
            success_text = f"✅ Регистрация подтверждена для @{target_username} в {target_data['tournament_type'].upper()}: {target_data['team_name']}"
            await update.message.reply_text(success_text)
            logger.info(f"Админ {user.username} подтвердил регистрацию для {target_username}")
        else:
            await update.message.reply_text("Не удалось подтвердить регистрацию.")

    async def handle_reply_confirmation(self, update, context):
        """Обработка подтверждения через ответ на сообщение"""
        user = update.effective_user
        
        if not await self.is_admin(update, context):
            return
        
        # Проверяем, является ли это ответом на сообщение
        if not update.message.reply_to_message:
            return
        
        # Извлекаем информацию из сообщения, на которое отвечаем
        reply_text = update.message.reply_to_message.text
        current_text = update.message.text.lower()
        
        # Проверяем, содержит ли ответ подтверждение
        if "подтвердить" in current_text or "подтверждаю" in current_text or "да" in current_text:
            # Ищем username в исходном сообщении
            import re
            username_match = re.search(r'@(\w+)', reply_text)
            if username_match:
                username = username_match.group(1)
                await self.handle_admin_confirm(update, context, username, 'ru')
    
    
    
    async def run(self):
        """Запуск бота"""
        if not TELEGRAM_AVAILABLE:
            logger.error("Библиотека Telegram недоступна. Невозможно запустить бота.")
            return
        
        if not self.token:
            logger.error("BOT_TOKEN не найден в переменных окружения")
            return
        
        logger.info("Запуск турнирного бота...")
        
        # Создание приложения
        application = Application.builder().token(self.token).build()
        
        # Убираем команды из меню Telegram
        try:
            await application.bot.set_my_commands([])
            logger.info("Команды бота очищены")
        except Exception as e:
            logger.error(f"Ошибка при настройке команд: {e}")
        
        # Добавление обработчиков команд (только для админов)
        application.add_handler(CommandHandler("start", self.handle_start))
        application.add_handler(CommandHandler("help", self.handle_help))
        application.add_handler(CommandHandler("list", self.handle_list))
        application.add_handler(CommandHandler("stats", self.handle_stats))
        application.add_handler(CommandHandler("clear", self.handle_clear))
        application.add_handler(CommandHandler("command", self.handle_command))
        
        # Обработчик сообщений для обработки естественного языка
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Запуск периодической очистки
        asyncio.create_task(self.storage.periodic_cleanup())
        
        # Запуск бота с правильным управлением lifecycle
        try:
            async with application:
                await application.start()
                await application.updater.start_polling(drop_pending_updates=True)
                logger.info("Бот успешно запущен и готов к работе!")
                
                # Держим бота работающим
                try:
                    await asyncio.Event().wait()  # Бесконечное ожидание
                except KeyboardInterrupt:
                    logger.info("Получен сигнал остановки")
                finally:
                    await application.updater.stop()
                    await application.stop()
                    
        except Exception as e:
            logger.error(f"Ошибка при запуске polling: {e}")
            raise

def main():
    """Точка входа"""
    if not TELEGRAM_AVAILABLE:
        print("Библиотека Telegram недоступна. Проверьте установку.")
        return
    
    try:
        bot = WorkingTournamentBot()
        
        # Проверяем, есть ли уже запущенный event loop (как в Replit)
        try:
            loop = asyncio.get_running_loop()
            # Если event loop уже запущен, создаем задачу
            task = asyncio.create_task(bot.run())
            logger.info("Бот запущен как задача в существующем event loop")
            return task
        except RuntimeError:
            # Если нет активного event loop, создаем новый
            asyncio.run(bot.run())
            
    except Exception as e:
        logger.error(f"Не удалось запустить бота: {e}")
        raise

if __name__ == "__main__":
    import nest_asyncio
    try:
        # Разрешаем вложенные event loops для совместимости с Replit
        nest_asyncio.apply()
    except:
        pass
    
    main()
