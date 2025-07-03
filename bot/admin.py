"""
Admin handlers for tournament management
"""

import json
import logging
from typing import List, Dict, Any
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from bot.storage import DataStorage
from bot.localization import Localizer

logger = logging.getLogger(__name__)


class AdminHandlers:
    """Handles admin-only commands and operations"""
    
    def __init__(self, storage: DataStorage, localizer: Localizer, admins: List[str]):
        self.storage = storage
        self.localizer = localizer
        self.admins = admins
    
    def _is_admin(self, username: str) -> bool:
        """Check if user is an admin"""
        if not username:
            return False
        clean_username = username.lstrip('@').lower()
        return clean_username in [admin.lower() for admin in self.admins]
    
    async def list_players(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """List all registered players"""
        user = update.effective_user
        lang = user.language_code if user.language_code in ["en", "ru"] else "en"
        
        if not self._is_admin(user.username):
            error_text = self.localizer.get_text("admin_only", lang)
            await update.message.reply_text(error_text)
            return
        
        try:
            players = self.storage.get_all_players()
            temp_registrations = self.storage.get_temp_registrations()
            
            message_parts = []
            
            # VSA Tournament
            vsa_players = players.get("vsa", {})
            if vsa_players:
                message_parts.append("🏆 <b>VSA Tournament:</b>")
                for username, data in vsa_players.items():
                    status = "✅" if data.get("confirmed") else "⏳"
                    message_parts.append(
                        f"{status} @{username}: {data['name']} ({data['stars']} ⭐)"
                    )
            else:
                message_parts.append("🏆 <b>VSA Tournament:</b> No registrations")
            
            message_parts.append("")
            
            # H2H Tournament
            h2h_players = players.get("h2h", {})
            if h2h_players:
                message_parts.append("⚔️ <b>H2H Tournament:</b>")
                for username, data in h2h_players.items():
                    status = "✅" if data.get("confirmed") else "⏳"
                    message_parts.append(
                        f"{status} @{username}: {data['name']} ({data['stars']} ⭐)"
                    )
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
                    message_parts.append(
                        f"• @{username} - {tournament}: {team_name} ({rating} ⭐)"
                    )
            
            if not message_parts or len(message_parts) <= 3:
                final_message = self.localizer.get_text("no_registrations", lang)
            else:
                final_message = "\n".join(message_parts)
            
            await update.message.reply_text(final_message, parse_mode='HTML')
            
            logger.info(f"Admin {user.username} requested player list")
            
        except Exception as e:
            logger.error(f"Error listing players: {e}")
            error_text = self.localizer.get_text("error_occurred", lang)
            await update.message.reply_text(error_text)
    
    async def clear_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear all tournament data"""
        user = update.effective_user
        lang = user.language_code if user.language_code in ["en", "ru"] else "en"
        
        if not self._is_admin(user.username):
            error_text = self.localizer.get_text("admin_only", lang)
            await update.message.reply_text(error_text)
            return
        
        try:
            # Get confirmation from context args
            args = context.args
            if not args or args[0].lower() != "confirm":
                confirm_text = self.localizer.get_text("clear_confirmation", lang)
                await update.message.reply_text(confirm_text)
                return
            
            # Clear all data
            self.storage.clear_all_data()
            
            success_text = self.localizer.get_text("data_cleared", lang)
            await update.message.reply_text(success_text)
            
            logger.info(f"Admin {user.username} cleared all tournament data")
            
        except Exception as e:
            logger.error(f"Error clearing data: {e}")
            error_text = self.localizer.get_text("error_occurred", lang)
            await update.message.reply_text(error_text)
    
    async def export_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Export tournament data to JSON"""
        user = update.effective_user
        lang = user.language_code if user.language_code in ["en", "ru"] else "en"
        
        if not self._is_admin(user.username):
            error_text = self.localizer.get_text("admin_only", lang)
            await update.message.reply_text(error_text)
            return
        
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "players": self.storage.get_all_players(),
                "temp_registrations": self.storage.get_temp_registrations(),
                "statistics": self.storage.get_statistics()
            }
            
            # Create JSON file
            json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            # Send as document
            filename = f"tournament_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            await update.message.reply_document(
                document=json_data.encode('utf-8'),
                filename=filename,
                caption=self.localizer.get_text("export_complete", lang)
            )
            
            logger.info(f"Admin {user.username} exported tournament data")
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            error_text = self.localizer.get_text("error_occurred", lang)
            await update.message.reply_text(error_text)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show tournament statistics"""
        user = update.effective_user
        lang = user.language_code if user.language_code in ["en", "ru"] else "en"
        
        if not self._is_admin(user.username):
            error_text = self.localizer.get_text("admin_only", lang)
            await update.message.reply_text(error_text)
            return
        
        try:
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
            
            final_message = "\n".join(message_parts)
            await update.message.reply_text(final_message, parse_mode='HTML')
            
            logger.info(f"Admin {user.username} requested statistics")
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            error_text = self.localizer.get_text("error_occurred", lang)
            await update.message.reply_text(error_text)
    
    async def confirm_registration(
        self, 
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE, 
        target_username: str
    ) -> None:
        """Confirm a user's registration"""
        user = update.effective_user
        lang = user.language_code if user.language_code in ["en", "ru"] else "en"
        
        if not self._is_admin(user.username):
            error_text = self.localizer.get_text("admin_only", lang)
            await update.message.reply_text(error_text)
            return
        
        try:
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
                error_text = self.localizer.get_text(
                    "no_pending_registration", 
                    lang
                ).format(username=target_username)
                await update.message.reply_text(error_text)
                return
            
            # Confirm registration
            success = self.storage.confirm_registration(target_user_id)
            
            if success:
                success_text = self.localizer.get_text(
                    "registration_confirmed",
                    lang
                ).format(
                    username=target_username,
                    tournament=target_data["tournament_type"].upper(),
                    team_name=target_data["team_name"]
                )
                await update.message.reply_text(success_text)
                
                logger.info(f"Admin {user.username} confirmed registration for {target_username}")
            else:
                error_text = self.localizer.get_text("confirmation_failed", lang)
                await update.message.reply_text(error_text)
                
        except Exception as e:
            logger.error(f"Error confirming registration: {e}")
            error_text = self.localizer.get_text("error_occurred", lang)
            await update.message.reply_text(error_text)
