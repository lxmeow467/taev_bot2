"""
Main bot handlers for user interactions and commands
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.storage import DataStorage
from bot.localization import Localizer
from bot.nlp import NLPProcessor
from bot.validation import ValidationError, validate_team_name, validate_rating

logger = logging.getLogger(__name__)


class BotHandlers:
    """Handles user commands and messages"""
    
    def __init__(self, storage: DataStorage, localizer: Localizer, nlp_processor: NLPProcessor):
        self.storage = storage
        self.localizer = localizer
        self.nlp_processor = nlp_processor
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        user = update.effective_user
        lang = user.language_code if user.language_code in ["en", "ru"] else "en"
        
        welcome_text = self.localizer.get_text("welcome_message", lang)
        instructions_text = self.localizer.get_text("instructions", lang)
        
        # Create inline keyboard with helpful buttons
        keyboard = [
            [
                InlineKeyboardButton(
                    self.localizer.get_text("help_button", lang),
                    callback_data="help"
                ),
                InlineKeyboardButton(
                    self.localizer.get_text("examples_button", lang),
                    callback_data="examples"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        full_message = f"{welcome_text}\n\n{instructions_text}"
        
        await update.message.reply_text(
            full_message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        logger.info(f"User {user.username} ({user.id}) started the bot")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        user = update.effective_user
        lang = user.language_code if user.language_code in ["en", "ru"] else "en"
        
        help_text = self.localizer.get_text("help_message", lang)
        examples_text = self.localizer.get_text("command_examples", lang)
        
        full_message = f"{help_text}\n\n{examples_text}"
        
        await update.message.reply_text(full_message, parse_mode='HTML')
    
    async def process_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Process natural language messages"""
        user = update.effective_user
        message_text = update.message.text
        lang = user.language_code if user.language_code in ["en", "ru"] else "en"
        
        logger.info(f"Processing message from {user.username}: {message_text}")
        
        try:
            # Parse the message using NLP processor
            parsed_command = self.nlp_processor.parse_message(message_text, lang)
            
            if not parsed_command:
                # Send help message for unrecognized commands
                help_text = self.localizer.get_text("unrecognized_command", lang)
                await update.message.reply_text(help_text)
                return
            
            # Process the parsed command
            await self._handle_parsed_command(update, context, parsed_command, lang)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_text = self.localizer.get_text("processing_error", lang)
            await update.message.reply_text(error_text)
    
    async def _handle_parsed_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        command: Dict[str, Any],
        lang: str
    ) -> None:
        """Handle a parsed command"""
        user = update.effective_user
        command_type = command.get("type")
        
        if command_type == "set_team_name":
            await self._handle_team_name(update, context, command["team_name"], lang)
        
        elif command_type == "set_vsa_rating":
            await self._handle_rating(update, context, "vsa", command["rating"], lang)
        
        elif command_type == "set_h2h_rating":
            await self._handle_rating(update, context, "h2h", command["rating"], lang)
        
        elif command_type == "admin_confirm":
            await self._handle_admin_confirm(update, context, command["username"], lang)
        
        else:
            help_text = self.localizer.get_text("unrecognized_command", lang)
            await update.message.reply_text(help_text)
    
    async def _handle_team_name(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        team_name: str,
        lang: str
    ) -> None:
        """Handle team name setting"""
        user = update.effective_user
        
        try:
            # Validate team name
            validate_team_name(team_name)
            
            # Store in user context
            if "registration_data" not in context.user_data:
                context.user_data["registration_data"] = {}
            
            context.user_data["registration_data"]["team_name"] = team_name
            context.user_data["registration_data"]["timestamp"] = datetime.now()
            
            success_text = self.localizer.get_text(
                "team_name_saved", 
                lang
            ).format(team_name=team_name)
            
            next_step_text = self.localizer.get_text("next_step_rating", lang)
            
            await update.message.reply_text(f"{success_text}\n\n{next_step_text}")
            
            logger.info(f"User {user.username} set team name: {team_name}")
            
        except ValidationError as e:
            error_text = self.localizer.get_text("validation_error", lang).format(error=str(e))
            await update.message.reply_text(error_text)
    
    async def _handle_rating(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        tournament_type: str,
        rating: int,
        lang: str
    ) -> None:
        """Handle rating setting"""
        user = update.effective_user
        
        try:
            # Validate rating
            validate_rating(rating)
            
            # Check if user has team name set
            registration_data = context.user_data.get("registration_data", {})
            if "team_name" not in registration_data:
                error_text = self.localizer.get_text("team_name_required", lang)
                await update.message.reply_text(error_text)
                return
            
            # Store rating
            registration_data[f"{tournament_type}_rating"] = rating
            registration_data["timestamp"] = datetime.now()
            
            # Check if registration is complete for this tournament
            team_name = registration_data["team_name"]
            
            success_text = self.localizer.get_text(
                "rating_saved",
                lang
            ).format(tournament=tournament_type.upper(), rating=rating)
            
            # Save to temporary storage
            await self.storage.save_temp_registration(
                user_id=user.id,
                username=user.username,
                tournament_type=tournament_type,
                team_name=team_name,
                rating=rating
            )
            
            confirm_text = self.localizer.get_text("awaiting_confirmation", lang)
            
            await update.message.reply_text(f"{success_text}\n\n{confirm_text}")
            
            logger.info(f"User {user.username} set {tournament_type} rating: {rating}")
            
        except ValidationError as e:
            error_text = self.localizer.get_text("validation_error", lang).format(error=str(e))
            await update.message.reply_text(error_text)
    
    async def _handle_admin_confirm(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        target_username: str,
        lang: str
    ) -> None:
        """Handle admin confirmation (delegate to admin handlers)"""
        from bot.admin import AdminHandlers
        
        # This should be handled by admin handlers, but we'll provide basic feedback
        error_text = self.localizer.get_text("use_admin_command", lang)
        await update.message.reply_text(error_text)
