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
                message_parts.append("VSA Tournament:")
                for username, data in vsa_players.items():
                    status = "✅" if data.get("confirmed") else "⏳"
                    message_parts.append(
                        f"{status} @{username}: {data['name']} ({data['stars']} ⭐)"
                    )
            else:
                message_parts.append("VSA Tournament: No registrations")
            
            message_parts.append("")
            
            # H2H Tournament
            h2h_players = players.get("h2h", {})
            if h2h_players:
                message_parts.append("H2H Tournament:")
                for username, data in h2h_players.items():
                    status = "✅" if data.get("confirmed") else "⏳"
                    message_parts.append(
                        f"{status} @{username}: {data['name']} ({data['stars']} ⭐)"
                    )
            else:
                message_parts.append("H2H Tournament: No registrations")

            # Send as single message
            await update.message.reply_text("\n".join(message_parts))
            
        except Exception as e:
            logger.error(f"Error listing players: {e}")
            error_text = self.localizer.get_text("list_players_error", lang)
            await update.message.reply_text(error_text)
