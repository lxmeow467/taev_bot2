#!/usr/bin/env python3
"""
Working Tournament Bot - Simplified version that handles the import issue
"""

import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any

# Set up basic logging
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
    logger.warning(f"Telegram import issue: {e}")
    TELEGRAM_AVAILABLE = False

from dotenv import load_dotenv
from bot.nlp import NLPProcessor
from bot.storage import DataStorage
from bot.localization import Localizer
from bot.validation import ValidationError, validate_team_name, validate_rating

# Load environment
load_dotenv()

class WorkingTournamentBot:
    """Simplified tournament bot that works around import issues"""
    
    def __init__(self):
        self.token = os.getenv('BOT_TOKEN')
        self.admins = os.getenv('ADMINS', '').split(',')
        
        # Initialize core components
        self.storage = DataStorage()
        self.localizer = Localizer()
        self.nlp = NLPProcessor()
        
        logger.info("Tournament bot components initialized")
    
    def is_admin(self, username: str) -> bool:
        """Check if user is admin"""
        if not username:
            return False
        clean_username = username.lstrip('@').lower()
        return clean_username in [admin.strip().lower() for admin in self.admins if admin.strip()]
    
    async def handle_start(self, update, context):
        """Handle /start command"""
        user = update.effective_user
        lang = 'ru' if user.language_code and user.language_code.startswith('ru') else 'en'
        
        welcome_text = self.localizer.get_text("welcome_message", lang)
        instructions_text = self.localizer.get_text("instructions", lang)
        
        await update.message.reply_text(
            f"{welcome_text}\n\n{instructions_text}",
            parse_mode='HTML'
        )
        
        logger.info(f"User {user.username} started the bot")
    
    async def handle_help(self, update, context):
        """Handle /help command"""
        user = update.effective_user
        lang = 'ru' if user.language_code and user.language_code.startswith('ru') else 'en'
        
        help_text = self.localizer.get_text("help_message", lang)
        examples_text = self.localizer.get_text("command_examples", lang)
        
        await update.message.reply_text(f"{help_text}\n\n{examples_text}", parse_mode='HTML')
    
    async def handle_list(self, update, context):
        """Handle /list command (admin only)"""
        user = update.effective_user
        lang = 'ru' if user.language_code and user.language_code.startswith('ru') else 'en'
        
        if not self.is_admin(user.username):
            error_text = self.localizer.get_text("admin_only", lang)
            await update.message.reply_text(error_text)
            return
        
        players = self.storage.get_all_players()
        temp_registrations = self.storage.get_temp_registrations()
        
        message_parts = []
        
        # VSA Tournament
        vsa_players = players.get("vsa", {})
        if vsa_players:
            message_parts.append("🏆 <b>VSA Tournament:</b>")
            for username, data in vsa_players.items():
                status = "✅" if data.get("confirmed") else "⏳"
                message_parts.append(f"{status} {username}: {data['name']} ({data['stars']} ⭐)")
        else:
            message_parts.append("🏆 <b>VSA Tournament:</b> No registrations")
        
        message_parts.append("")
        
        # H2H Tournament
        h2h_players = players.get("h2h", {})
        if h2h_players:
            message_parts.append("⚔️ <b>H2H Tournament:</b>")
            for username, data in h2h_players.items():
                status = "✅" if data.get("confirmed") else "⏳"
                message_parts.append(f"{status} {username}: {data['name']} ({data['stars']} ⭐)")
        else:
            message_parts.append("⚔️ <b>H2H Tournament:</b> No registrations")
        
        # Pending confirmations
        if temp_registrations:
            message_parts.append("")
            message_parts.append("⏳ <b>Pending Confirmations:</b>")
            for user_id, data in temp_registrations.items():
                username = data.get("username", "Unknown")
                tournament = data.get("tournament_type", "unknown").upper()
                team_name = data.get("team_name", "Unknown")
                rating = data.get("rating", 0)
                message_parts.append(f"• @{username} - {tournament}: {team_name} ({rating} ⭐)")
        
        final_message = "\n".join(message_parts) if message_parts else "No registrations found"
        await update.message.reply_text(final_message, parse_mode='HTML')
        
        logger.info(f"Admin {user.username} requested player list")
    
    async def handle_stats(self, update, context):
        """Handle /stats command (admin only)"""
        user = update.effective_user
        lang = 'ru' if user.language_code and user.language_code.startswith('ru') else 'en'
        
        if not self.is_admin(user.username):
            error_text = self.localizer.get_text("admin_only", lang)
            await update.message.reply_text(error_text)
            return
        
        stats = self.storage.get_statistics()
        
        message_parts = [
            "📊 <b>Tournament Statistics:</b>",
            "",
            f"🏆 VSA Registrations: {stats['vsa_total']} total, {stats['vsa_confirmed']} confirmed",
            f"⚔️ H2H Registrations: {stats['h2h_total']} total, {stats['h2h_confirmed']} confirmed",
            f"⏳ Pending Confirmations: {stats['pending_confirmations']}",
            "",
            f"📈 Total Users: {stats['total_users']}",
            f"🕐 Last Registration: {stats['last_registration_time'] or 'Never'}"
        ]
        
        await update.message.reply_text("\n".join(message_parts), parse_mode='HTML')
        logger.info(f"Admin {user.username} requested statistics")
    
    async def handle_message(self, update, context):
        """Handle natural language messages"""
        user = update.effective_user
        message_text = update.message.text
        lang = 'ru' if user.language_code and user.language_code.startswith('ru') else 'en'
        
        logger.info(f"Processing message from {user.username}: {message_text}")
        
        try:
            # Parse the message using NLP processor
            parsed_command = self.nlp.parse_message(message_text, lang)
            
            if not parsed_command:
                help_text = self.localizer.get_text("unrecognized_command", lang)
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
            logger.error(f"Error processing message: {e}")
            error_text = self.localizer.get_text("processing_error", lang)
            await update.message.reply_text(error_text)
    
    async def handle_team_name(self, update, context, team_name: str, lang: str):
        """Handle team name setting"""
        user = update.effective_user
        
        try:
            validate_team_name(team_name)
            
            if "registration_data" not in context.user_data:
                context.user_data["registration_data"] = {}
            
            context.user_data["registration_data"]["team_name"] = team_name
            context.user_data["registration_data"]["timestamp"] = datetime.now()
            
            success_text = self.localizer.get_text("team_name_saved", lang).format(team_name=team_name)
            next_step_text = self.localizer.get_text("next_step_rating", lang)
            
            await update.message.reply_text(f"{success_text}\n\n{next_step_text}")
            logger.info(f"User {user.username} set team name: {team_name}")
            
        except ValidationError as e:
            error_text = self.localizer.get_text("validation_error", lang).format(error=str(e))
            await update.message.reply_text(error_text)
    
    async def handle_rating(self, update, context, tournament_type: str, rating: int, lang: str):
        """Handle rating setting"""
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
                username=user.username,
                tournament_type=tournament_type,
                team_name=team_name,
                rating=rating
            )
            
            if success:
                success_text = self.localizer.get_text("rating_saved", lang).format(
                    tournament=tournament_type.upper(), 
                    rating=rating
                )
                confirm_text = self.localizer.get_text("awaiting_confirmation", lang)
                await update.message.reply_text(f"{success_text}\n\n{confirm_text}")
                logger.info(f"User {user.username} registered for {tournament_type}: {rating}")
            else:
                error_text = "Registration failed. You may already be registered for this tournament."
                await update.message.reply_text(error_text)
            
        except ValidationError as e:
            error_text = self.localizer.get_text("validation_error", lang).format(error=str(e))
            await update.message.reply_text(error_text)
    
    async def handle_admin_confirm(self, update, context, target_username: str, lang: str):
        """Handle admin confirmation"""
        user = update.effective_user
        
        if not self.is_admin(user.username):
            error_text = self.localizer.get_text("admin_only", lang)
            await update.message.reply_text(error_text)
            return
        
        # Find pending registration
        temp_registrations = self.storage.get_temp_registrations()
        target_data = None
        target_user_id = None
        
        for user_id, data in temp_registrations.items():
            if data.get("username", "").lower() == target_username.lower():
                target_data = data
                target_user_id = user_id
                break
        
        if not target_data:
            error_text = f"No pending registration found for @{target_username}"
            await update.message.reply_text(error_text)
            return
        
        success = self.storage.confirm_registration(target_user_id)
        
        if success:
            success_text = f"✅ Registration confirmed for @{target_username} in {target_data['tournament_type'].upper()}: {target_data['team_name']}"
            await update.message.reply_text(success_text)
            logger.info(f"Admin {user.username} confirmed registration for {target_username}")
        else:
            await update.message.reply_text("Failed to confirm registration.")
    
    async def run(self):
        """Start the bot"""
        if not TELEGRAM_AVAILABLE:
            logger.error("Telegram library not available. Cannot start bot.")
            return
        
        if not self.token:
            logger.error("BOT_TOKEN not found in environment variables")
            return
        
        logger.info("Starting Tournament Bot...")
        
        # Create application
        application = Application.builder().token(self.token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.handle_start))
        application.add_handler(CommandHandler("help", self.handle_help))
        application.add_handler(CommandHandler("list", self.handle_list))
        application.add_handler(CommandHandler("stats", self.handle_stats))
        
        # Message handler for natural language processing
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Start periodic cleanup
        asyncio.create_task(self.storage.periodic_cleanup())
        
        # Start the bot
        await application.run_polling(drop_pending_updates=True)

async def main():
    """Main entry point"""
    try:
        bot = WorkingTournamentBot()
        await bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    if TELEGRAM_AVAILABLE:
        asyncio.run(main())
    else:
        print("Telegram library not available. Please check the installation.")
        print("Running demo instead...")
        import subprocess
        subprocess.run(["python", "simple_production_demo.py"])