#!/usr/bin/env python3
"""
Webhook-based Tournament Bot - Alternative implementation
Uses manual HTTP requests to avoid import issues
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import requests
from dotenv import load_dotenv

from bot.nlp import NLPProcessor
from bot.storage import DataStorage
from bot.localization import Localizer
from bot.validation import ValidationError, validate_team_name, validate_rating

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

class ManualTelegramBot:
    """Manual implementation using direct Telegram API calls"""
    
    def __init__(self):
        self.token = os.getenv('BOT_TOKEN')
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.admins = [admin.strip() for admin in os.getenv('ADMINS', '').split(',') if admin.strip()]
        
        # Initialize components
        self.storage = DataStorage()
        self.localizer = Localizer()
        self.nlp = NLPProcessor()
        
        # In-memory user context storage
        self.user_contexts = {}
        
        logger.info("Manual Tournament Bot initialized")
    
    def is_admin(self, username: str) -> bool:
        """Check if user is admin"""
        if not username:
            return False
        return username.lower() in [admin.lower() for admin in self.admins]
    
    def send_message(self, chat_id: int, text: str, parse_mode: str = None) -> bool:
        """Send message via Telegram API"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text[:4000],  # Telegram message limit
            }
            if parse_mode:
                data["parse_mode"] = parse_mode
            
            response = requests.post(url, data=data)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def get_updates(self, offset: int = 0) -> List[Dict]:
        """Get updates from Telegram"""
        try:
            url = f"{self.base_url}/getUpdates"
            params = {"offset": offset, "timeout": 10}
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("result", [])
            return []
        except Exception as e:
            logger.error(f"Failed to get updates: {e}")
            return []
    
    async def handle_update(self, update: Dict) -> None:
        """Process a single update"""
        try:
            message = update.get("message")
            if not message:
                return
            
            chat_id = message["chat"]["id"]
            user = message.get("from", {})
            username = user.get("username", "")
            user_id = user.get("id")
            text = message.get("text", "")
            
            if not text:
                return
            
            # Determine language
            lang_code = user.get("language_code", "en")
            lang = "ru" if lang_code and lang_code.startswith("ru") else "en"
            
            logger.info(f"Processing message from @{username}: {text}")
            
            # Handle commands
            if text.startswith("/"):
                await self.handle_command(chat_id, user_id, username, text, lang)
            else:
                await self.handle_natural_language(chat_id, user_id, username, text, lang)
                
        except Exception as e:
            logger.error(f"Error handling update: {e}")
    
    async def handle_command(self, chat_id: int, user_id: int, username: str, text: str, lang: str):
        """Handle slash commands"""
        command = text.split()[0].lower()
        
        if command == "/start":
            welcome_text = self.localizer.get_text("welcome_message", lang)
            instructions_text = self.localizer.get_text("instructions", lang)
            self.send_message(chat_id, f"{welcome_text}\n\n{instructions_text}", "HTML")
            
        elif command == "/help":
            help_text = self.localizer.get_text("help_message", lang)
            examples_text = self.localizer.get_text("command_examples", lang)
            self.send_message(chat_id, f"{help_text}\n\n{examples_text}", "HTML")
            
        elif command == "/list":
            await self.handle_list_command(chat_id, username, lang)
            
        elif command == "/stats":
            await self.handle_stats_command(chat_id, username, lang)
            
        else:
            help_text = self.localizer.get_text("unrecognized_command", lang)
            self.send_message(chat_id, help_text)
    
    async def handle_list_command(self, chat_id: int, username: str, lang: str):
        """Handle /list command"""
        if not self.is_admin(username):
            error_text = self.localizer.get_text("admin_only", lang)
            self.send_message(chat_id, error_text)
            return
        
        players = self.storage.get_all_players()
        temp_registrations = self.storage.get_temp_registrations()
        
        message_parts = []
        
        # VSA Tournament
        vsa_players = players.get("vsa", {})
        if vsa_players:
            message_parts.append("🏆 <b>VSA Tournament:</b>")
            for username_key, data in vsa_players.items():
                status = "✅" if data.get("confirmed") else "⏳"
                message_parts.append(f"{status} {username_key}: {data['name']} ({data['stars']} ⭐)")
        else:
            message_parts.append("🏆 <b>VSA Tournament:</b> No registrations")
        
        message_parts.append("")
        
        # H2H Tournament
        h2h_players = players.get("h2h", {})
        if h2h_players:
            message_parts.append("⚔️ <b>H2H Tournament:</b>")
            for username_key, data in h2h_players.items():
                status = "✅" if data.get("confirmed") else "⏳"
                message_parts.append(f"{status} {username_key}: {data['name']} ({data['stars']} ⭐)")
        else:
            message_parts.append("⚔️ <b>H2H Tournament:</b> No registrations")
        
        # Pending confirmations
        if temp_registrations:
            message_parts.append("")
            message_parts.append("⏳ <b>Pending Confirmations:</b>")
            for user_id, data in temp_registrations.items():
                username_temp = data.get("username", "Unknown")
                tournament = data.get("tournament_type", "unknown").upper()
                team_name = data.get("team_name", "Unknown")
                rating = data.get("rating", 0)
                message_parts.append(f"• @{username_temp} - {tournament}: {team_name} ({rating} ⭐)")
        
        final_message = "\n".join(message_parts) if message_parts else "No registrations found"
        self.send_message(chat_id, final_message, "HTML")
        
        logger.info(f"Admin @{username} requested player list")
    
    async def handle_stats_command(self, chat_id: int, username: str, lang: str):
        """Handle /stats command"""
        if not self.is_admin(username):
            error_text = self.localizer.get_text("admin_only", lang)
            self.send_message(chat_id, error_text)
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
        
        self.send_message(chat_id, "\n".join(message_parts), "HTML")
        logger.info(f"Admin @{username} requested statistics")
    
    async def handle_natural_language(self, chat_id: int, user_id: int, username: str, text: str, lang: str):
        """Handle natural language messages"""
        try:
            parsed_command = self.nlp.parse_message(text, lang)
            
            if not parsed_command:
                help_text = self.localizer.get_text("unrecognized_command", lang)
                self.send_message(chat_id, help_text)
                return
            
            command_type = parsed_command.get("type")
            
            if command_type == "set_team_name":
                await self.handle_team_name(chat_id, user_id, username, parsed_command["team_name"], lang)
            
            elif command_type == "set_vsa_rating":
                await self.handle_rating(chat_id, user_id, username, "vsa", parsed_command["rating"], lang)
            
            elif command_type == "set_h2h_rating":
                await self.handle_rating(chat_id, user_id, username, "h2h", parsed_command["rating"], lang)
            
            elif command_type == "admin_confirm":
                await self.handle_admin_confirm(chat_id, username, parsed_command["username"], lang)
                
        except Exception as e:
            logger.error(f"Error processing natural language: {e}")
            error_text = self.localizer.get_text("processing_error", lang)
            self.send_message(chat_id, error_text)
    
    async def handle_team_name(self, chat_id: int, user_id: int, username: str, team_name: str, lang: str):
        """Handle team name setting"""
        try:
            validate_team_name(team_name)
            
            # Store in user context
            if user_id not in self.user_contexts:
                self.user_contexts[user_id] = {}
            
            self.user_contexts[user_id]["team_name"] = team_name
            self.user_contexts[user_id]["timestamp"] = datetime.now()
            
            success_text = self.localizer.get_text("team_name_saved", lang).format(team_name=team_name)
            next_step_text = self.localizer.get_text("next_step_rating", lang)
            
            self.send_message(chat_id, f"{success_text}\n\n{next_step_text}")
            logger.info(f"User @{username} set team name: {team_name}")
            
        except ValidationError as e:
            error_text = self.localizer.get_text("validation_error", lang).format(error=str(e))
            self.send_message(chat_id, error_text)
    
    async def handle_rating(self, chat_id: int, user_id: int, username: str, tournament_type: str, rating: int, lang: str):
        """Handle rating setting"""
        try:
            validate_rating(rating)
            
            user_context = self.user_contexts.get(user_id, {})
            if "team_name" not in user_context:
                error_text = self.localizer.get_text("team_name_required", lang)
                self.send_message(chat_id, error_text)
                return
            
            team_name = user_context["team_name"]
            
            success = await self.storage.save_temp_registration(
                user_id=user_id,
                username=username,
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
                self.send_message(chat_id, f"{success_text}\n\n{confirm_text}")
                logger.info(f"User @{username} registered for {tournament_type}: {rating}")
            else:
                error_text = "Registration failed. You may already be registered for this tournament."
                self.send_message(chat_id, error_text)
                
        except ValidationError as e:
            error_text = self.localizer.get_text("validation_error", lang).format(error=str(e))
            self.send_message(chat_id, error_text)
    
    async def handle_admin_confirm(self, chat_id: int, username: str, target_username: str, lang: str):
        """Handle admin confirmation"""
        if not self.is_admin(username):
            error_text = self.localizer.get_text("admin_only", lang)
            self.send_message(chat_id, error_text)
            return
        
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
            self.send_message(chat_id, error_text)
            return
        
        success = self.storage.confirm_registration(target_user_id)
        
        if success:
            success_text = f"✅ Registration confirmed for @{target_username} in {target_data['tournament_type'].upper()}: {target_data['team_name']}"
            self.send_message(chat_id, success_text)
            logger.info(f"Admin @{username} confirmed registration for @{target_username}")
        else:
            self.send_message(chat_id, "Failed to confirm registration.")
    
    async def run(self):
        """Main bot loop"""
        if not self.token:
            logger.error("BOT_TOKEN not found in environment variables")
            return
        
        logger.info("Starting Manual Tournament Bot with polling...")
        
        offset = 0
        
        # Start periodic cleanup
        asyncio.create_task(self.storage.periodic_cleanup())
        
        while True:
            try:
                updates = self.get_updates(offset)
                
                for update in updates:
                    await self.handle_update(update)
                    offset = update["update_id"] + 1
                
                if not updates:
                    await asyncio.sleep(1)  # Brief pause when no updates
                    
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying

async def main():
    """Main entry point"""
    try:
        bot = ManualTelegramBot()
        await bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())