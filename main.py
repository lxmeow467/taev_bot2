#!/usr/bin/env python3
"""
Advanced Telegram Bot for Esports Tournament Registration
Production-ready implementation with NLP and admin management
"""

import asyncio
import logging
import os
from typing import Dict, Any

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.ext import ContextTypes
from telegram import Update

from config import Config
from bot.handlers import BotHandlers
from bot.admin import AdminHandlers
from bot.nlp import NLPProcessor
from bot.storage import DataStorage
from bot.localization import Localizer

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EsportsTournamentBot:
    """Main bot class that orchestrates all components"""
    
    def __init__(self):
        self.config = Config()
        self.storage = DataStorage()
        self.localizer = Localizer()
        self.nlp_processor = NLPProcessor()
        
        # Initialize handlers
        self.bot_handlers = BotHandlers(
            storage=self.storage,
            localizer=self.localizer,
            nlp_processor=self.nlp_processor
        )
        self.admin_handlers = AdminHandlers(
            storage=self.storage,
            localizer=self.localizer,
            admins=self.config.ADMINS
        )
        
        # Create application
        self.application = Application.builder().token(self.config.BOT_TOKEN).build()
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Setup all bot handlers"""
        app = self.application
        
        # Command handlers
        app.add_handler(CommandHandler("start", self.bot_handlers.start_command))
        app.add_handler(CommandHandler("help", self.bot_handlers.help_command))
        app.add_handler(CommandHandler("list", self.admin_handlers.list_players))
        app.add_handler(CommandHandler("clear", self.admin_handlers.clear_data))
        app.add_handler(CommandHandler("export", self.admin_handlers.export_data))
        app.add_handler(CommandHandler("stats", self.admin_handlers.stats_command))
        
        # Message handlers for natural language processing
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.bot_handlers.process_message
        ))
        
        # Error handler
        app.add_error_handler(self.error_handler)
        
        logger.info("All handlers registered successfully")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Global error handler"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update.effective_message:
            error_msg = self.localizer.get_text(
                "error_occurred",
                update.effective_user.language_code if update.effective_user else "en"
            )
            await update.effective_message.reply_text(error_msg)
    
    async def run(self) -> None:
        """Start the bot"""
        logger.info("Starting Esports Tournament Bot...")
        
        # Start periodic cleanup task
        asyncio.create_task(self.storage.periodic_cleanup())
        
        # Start the bot
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(drop_pending_updates=True)
        
        logger.info("Bot is running...")
        
        # Keep the bot running
        await self.application.updater.idle()
        
        # Cleanup
        await self.application.stop()
        await self.application.shutdown()


async def main():
    """Main entry point"""
    try:
        bot = EsportsTournamentBot()
        await bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
