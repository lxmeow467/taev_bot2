#!/usr/bin/env python3
"""
Финальная рабочая версия турнирного бота
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
    logger.error(f"Ошибка импорта Telegram: {e}")
    TELEGRAM_AVAILABLE = False
    exit(1)

from dotenv import load_dotenv
from bot.nlp import NLPProcessor
from bot.storage import DataStorage
from bot.localization import Localizer
from bot.validation import ValidationError, validate_team_name, validate_rating

# Загрузка переменных окружения
load_dotenv()

class TournamentBot:
    """Турнирный бот"""

    def __init__(self):
        self.token = os.getenv('BOT_TOKEN')
        if not self.token:
            raise ValueError("BOT_TOKEN не найден в переменных окружения")

        self.admins = [admin.strip().lower() for admin in os.getenv('ADMINS', '').split(',') if admin.strip()]

        # Инициализация компонентов
        self.storage = DataStorage()
        self.localizer = Localizer()
        self.nlp = NLPProcessor()

        logger.info("Турнирный бот инициализирован")

    async def is_admin(self, update, context) -> bool:
        """Проверка прав администратора"""
        try:
            user = update.effective_user
            chat = update.effective_chat

            member = await context.bot.get_chat_member(chat.id, user.id)
            return member.status in ['administrator', 'creator']
        except Exception as e:
            logger.error(f"Ошибка проверки прав: {e}")
            return False

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user = update.effective_user
        welcome_text = (
            "🏆 Добро пожаловать в турнирный бот!\n\n"
            "Для регистрации:\n"
            "1️⃣ Укажите название команды: Бот, мой ник НазваниеКоманды\n"
            "2️⃣ Укажите рейтинг: Бот, мой рекорд в VSA 99\n\n"
            "Для справки используйте /help"
        )
        await update.message.reply_text(welcome_text)

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = (
            "❓ Команды бота:\n\n"
            "🔸 Бот, мой ник НазваниеКоманды\n"
            "🔸 Бот, мой рекорд в VSA число\n"
            "🔸 Бот, мой рекорд в H2H число\n\n"
            "Админские команды:\n"
            "/roster - список игроков\n"
            "/stats - статистика"
        )
        await update.message.reply_text(help_text)

    async def handle_roster(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /roster"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Только для администраторов")
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

        # H2H Турнир
        h2h_players = players.get("h2h", {})
        if h2h_players:
            message_parts.append("⚔️ H2H Турнир:")
            for username, data in h2h_players.items():
                status = "✅" if data.get("confirmed") else "⏳"
                message_parts.append(f"{status} {username}: {data['name']} ({data['stars']} ⭐)")

        # Ожидающие подтверждения
        if temp_registrations:
            message_parts.append("\n⏳ Ожидают подтверждения:")
            for user_id, data in temp_registrations.items():
                username = data.get("username", "Unknown")
                tournament = data.get("tournament_type", "unknown").upper()
                team_name = data.get("team_name", "Unknown")
                rating = data.get("rating", 0)
                message_parts.append(f"• @{username} - {tournament}: {team_name} ({rating} ⭐)")

        final_message = "\n".join(message_parts) if message_parts else "Регистраций нет"
        await update.message.reply_text(final_message)

    async def handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /stats"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Только для администраторов")
            return

        stats = self.storage.get_statistics()

        stats_text = (
            f"📊 Статистика:\n"
            f"🏆 VSA: {stats['vsa_total']} всего, {stats['vsa_confirmed']} подтверждено\n"
            f"⚔️ H2H: {stats['h2h_total']} всего, {stats['h2h_confirmed']} подтверждено\n"
            f"⏳ Ожидают: {stats['pending_confirmations']}\n"
            f"👥 Всего пользователей: {stats['total_users']}"
        )
        await update.message.reply_text(stats_text)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка сообщений"""
        user = update.effective_user
        message_text = update.message.text

        logger.info(f"Сообщение от {user.username or user.first_name}: {message_text}")

        try:
            parsed_command = self.nlp.parse_message(message_text, "ru")

            if not parsed_command:
                await update.message.reply_text(
                    "❓ Не понял команду. Используйте:\n"
                    "• Бот, мой ник НазваниеКоманды\n"
                    "• Бот, мой рекорд в VSA число\n"
                    "• Бот, мой рекорд в H2H число"
                )
                return

            command_type = parsed_command.get("type")

            if command_type == "set_team_name":
                await self.handle_team_name(update, context, parsed_command["team_name"])
            elif command_type == "set_vsa_rating":
                await self.handle_rating(update, context, "vsa", parsed_command["rating"])
            elif command_type == "set_h2h_rating":
                await self.handle_rating(update, context, "h2h", parsed_command["rating"])
            elif command_type == "admin_confirm":
                await self.handle_admin_confirm(update, context, parsed_command["username"])
            elif command_type == "admin_reject":
                await self.handle_admin_reject(update, context, parsed_command["username"])

        except Exception as e:
            logger.error(f"Ошибка обработки: {e}")
            await update.message.reply_text("❌ Произошла ошибка при обработке команды")

    async def handle_team_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE, team_name: str):
        """Обработка названия команды"""
        try:
            validate_team_name(team_name)

            if "registration_data" not in context.user_data:
                context.user_data["registration_data"] = {}

            context.user_data["registration_data"]["team_name"] = team_name

            await update.message.reply_text(
                f"✅ Название команды сохранено: {team_name}\n\n"
                f"Теперь укажите рейтинг:\n"
                f"• Бот, мой рекорд в VSA число\n"
                f"• Бот, мой рекорд в H2H число"
            )

        except ValidationError as e:
            await update.message.reply_text(f"❌ Ошибка: {e}")

    async def handle_rating(self, update: Update, context: ContextTypes.DEFAULT_TYPE, tournament_type: str, rating: int):
        """Обработка рейтинга"""
        try:
            validate_rating(rating)

            registration_data = context.user_data.get("registration_data", {})
            if "team_name" not in registration_data:
                await update.message.reply_text("❌ Сначала укажите название команды")
                return

            team_name = registration_data["team_name"]
            user = update.effective_user

            success = await self.storage.save_temp_registration(
                user_id=user.id,
                username=user.username or user.first_name,
                tournament_type=tournament_type,
                team_name=team_name,
                rating=rating
            )

            if success:
                await update.message.reply_text(
                    f"✅ Рейтинг {tournament_type.upper()} сохранен: {rating} ⭐\n\n"
                    f"⏳ Ожидайте подтверждения от администратора"
                )
            else:
                await update.message.reply_text("❌ Вы уже зарегистрированы на этот турнир")

        except ValidationError as e:
            await update.message.reply_text(f"❌ Ошибка: {e}")

    async def handle_admin_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_username: str):
        """Подтверждение админом"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Только для администраторов")
            return

        temp_registrations = self.storage.get_temp_registrations()
        target_user_id = None

        for user_id, data in temp_registrations.items():
            if data.get("username", "").lower() == target_username.lower():
                target_user_id = user_id
                break

        if target_user_id:
            success = self.storage.confirm_registration(target_user_id)
            if success:
                await update.message.reply_text(f"✅ Регистрация подтверждена для @{target_username}")
            else:
                await update.message.reply_text("❌ Ошибка подтверждения")
        else:
            await update.message.reply_text(f"❌ Регистрация для @{target_username} не найдена")

    async def handle_admin_reject(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_username: str):
        """Отклонение админом"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Только для администраторов")
            return

        temp_registrations = self.storage.get_temp_registrations()
        target_user_id = None

        for user_id, data in temp_registrations.items():
            if data.get("username", "").lower() == target_username.lower():
                target_user_id = user_id
                break

        if target_user_id:
            success = self.storage.reject_registration(target_user_id)
            if success:
                await update.message.reply_text(f"❌ Регистрация отклонена для @{target_username}")
            else:
                await update.message.reply_text("❌ Ошибка отклонения")
        else:
            await update.message.reply_text(f"❌ Регистрация для @{target_username} не найдена")

    async def handle_comande(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /comande"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Только для администраторов")
            return

        command_text = (
            "🎮 Команды администратора:\n\n"
            "/start - Запуск бота\n"
            "/help - Помощь\n"
            "/roster - Список всех игроков\n"
            "/stats - Статистика турнира\n"
            "/delplayer @username - Удалить игрока\n"
            "/comande - Показать эту справку\n\n"
            "Для подтверждения регистрации используйте:\n"
            "• Бот, подтвердить @username\n"
             "• Бот @username +1 добавить\n"
            "• Бот @username - 1 отклонить"
        )
        await update.message.reply_text(command_text)

    async def handle_delplayer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /delplayer для удаления игрока"""
        if not await self.is_admin(update, context):
            await update.message.reply_text("❌ Только для администраторов")
            return

        # Проверяем аргументы команды
        if not context.args:
            await update.message.reply_text(
                "❌ Укажите имя пользователя\n"
                "Пример: /delplayer @username"
            )
            return

        target_username = context.args[0].replace("@", "").lower()

        # Удаляем из временных регистраций
        temp_registrations = self.storage.get_temp_registrations()
        temp_deleted = False
        for user_id, data in list(temp_registrations.items()):
            if data.get("username", "").lower() == target_username:
                success = self.storage.reject_registration(int(user_id))
                if success:
                    temp_deleted = True
                    break

        # Удаляем из подтвержденных игроков
        players = self.storage.get_all_players()
        confirmed_deleted = False
        tournament_deleted = None

        for tournament_type in ["vsa", "h2h"]:
            tournament_players = players.get(tournament_type, {})
            for username_key in list(tournament_players.keys()):
                if username_key.lower() == target_username:
                    success = self.storage.remove_confirmed_player(tournament_type, username_key)
                    if success:
                        confirmed_deleted = True
                        tournament_deleted = tournament_type.upper()
                        break

        # Формируем ответ
        if temp_deleted and confirmed_deleted:
            await update.message.reply_text(
                f"✅ Игрок @{target_username} удален из ожидающих и из турнира {tournament_deleted}"
            )
        elif temp_deleted:
            await update.message.reply_text(
                f"✅ Игрок @{target_username} удален из ожидающих подтверждения"
            )
        elif confirmed_deleted:
            await update.message.reply_text(
                f"✅ Игрок @{target_username} удален из турнира {tournament_deleted}"
            )
        else:
            await update.message.reply_text(
                f"❌ Игрок @{target_username} не найден в списках"
            )

    async def run(self):
        """Запуск бота"""
        logger.info("Запуск бота...")

        application = Application.builder().token(self.token).build()

        # Добавляем обработчики
        application.add_handler(CommandHandler("start", self.handle_start))
        application.add_handler(CommandHandler("help", self.handle_help))
        application.add_handler(CommandHandler("roster", self.handle_roster))
        application.add_handler(CommandHandler("stats", self.handle_stats))
        application.add_handler(CommandHandler("comande", self.handle_comande))
        application.add_handler(CommandHandler("delplayer", self.handle_delplayer))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Запускаем бота
        try:
            await application.initialize()
            await application.start()
            await application.updater.start_polling(drop_pending_updates=True)

            logger.info("Бот запущен и готов к работе!")

            # Держим бота активным
            await asyncio.Event().wait()

        except Exception as e:
            logger.error(f"Ошибка запуска: {e}")
        finally:
            await application.stop()
            await application.shutdown()

async def main():
    """Главная функция"""
    try:
        bot = TournamentBot()
        await bot.run()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())