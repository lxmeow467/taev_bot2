"""
Unit tests for admin handlers
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes

from bot.admin import AdminHandlers
from bot.storage import DataStorage
from bot.localization import Localizer


class TestAdminHandlers:
    """Test cases for AdminHandlers class"""
    
    @pytest.fixture
    def mock_storage(self):
        """Create mock storage"""
        storage = MagicMock(spec=DataStorage)
        storage.get_all_players.return_value = {
            "vsa": {
                "@testuser1": {"name": "Team1", "stars": 42, "confirmed": True}
            },
            "h2h": {
                "@testuser2": {"name": "Team2", "stars": 38, "confirmed": True}
            }
        }
        storage.get_temp_registrations.return_value = {
            "123": {
                "username": "pending_user",
                "tournament_type": "vsa",
                "team_name": "PendingTeam",
                "rating": 35,
                "timestamp": "2023-01-01T12:00:00"
            }
        }
        storage.get_statistics.return_value = {
            "vsa_total": 1,
            "h2h_total": 1,
            "vsa_confirmed": 1,
            "h2h_confirmed": 1,
            "pending_confirmations": 1,
            "total_users": 3,
            "last_registration_time": "2023-01-01T12:00:00"
        }
        storage.clear_all_data = MagicMock()
        storage.confirm_registration = MagicMock(return_value=True)
        return storage
    
    @pytest.fixture
    def mock_localizer(self):
        """Create mock localizer"""
        localizer = MagicMock(spec=Localizer)
        localizer.get_text.return_value = "Test message"
        return localizer
    
    @pytest.fixture
    def admin_handlers(self, mock_storage, mock_localizer):
        """Create admin handlers instance"""
        admins = ["admin1", "admin2"]
        return AdminHandlers(mock_storage, mock_localizer, admins)
    
    @pytest.fixture
    def mock_admin_update(self):
        """Create mock update from admin user"""
        user = User(id=456, first_name="Admin", is_bot=False, username="admin1")
        chat = Chat(id=456, type="private")
        message = Message(
            message_id=2,
            date=None,
            chat=chat,
            from_user=user,
            text="/list"
        )
        message.reply_text = AsyncMock()
        message.reply_document = AsyncMock()
        
        update = Update(update_id=2, message=message)
        return update
    
    @pytest.fixture
    def mock_user_update(self):
        """Create mock update from regular user"""
        user = User(id=123, first_name="User", is_bot=False, username="regularuser")
        chat = Chat(id=123, type="private")
        message = Message(
            message_id=3,
            date=None,
            chat=chat,
            from_user=user,
            text="/list"
        )
        message.reply_text = AsyncMock()
        
        update = Update(update_id=3, message=message)
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context"""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = []
        return context
    
    def test_is_admin(self, admin_handlers):
        """Test admin check functionality"""
        # Test valid admin
        assert admin_handlers._is_admin("admin1") is True
        assert admin_handlers._is_admin("@admin1") is True
        assert admin_handlers._is_admin("ADMIN1") is True  # Case insensitive
        
        # Test invalid admin
        assert admin_handlers._is_admin("regularuser") is False
        assert admin_handlers._is_admin("") is False
        assert admin_handlers._is_admin(None) is False
    
    @pytest.mark.asyncio
    async def test_list_players_admin(self, admin_handlers, mock_admin_update, mock_context, mock_localizer):
        """Test list players command as admin"""
        await admin_handlers.list_players(mock_admin_update, mock_context)
        
        # Verify message was sent
        mock_admin_update.message.reply_text.assert_called_once()
        call_args = mock_admin_update.message.reply_text.call_args[0][0]
        
        # Should contain tournament information
        assert "VSA" in call_args or "H2H" in call_args
    
    @pytest.mark.asyncio
    async def test_list_players_non_admin(self, admin_handlers, mock_user_update, mock_context, mock_localizer):
        """Test list players command as non-admin"""
        mock_localizer.get_text.return_value = "Admin only command"
        
        await admin_handlers.list_players(mock_user_update, mock_context)
        
        # Verify admin-only message was sent
        mock_user_update.message.reply_text.assert_called_once()
        call_args = mock_user_update.message.reply_text.call_args[0][0]
        assert "Admin only command" in call_args
    
    @pytest.mark.asyncio
    async def test_clear_data_without_confirmation(self, admin_handlers, mock_admin_update, mock_context, mock_localizer):
        """Test clear data command without confirmation"""
        mock_localizer.get_text.return_value = "Use /clear confirm"
        
        await admin_handlers.clear_data(mock_admin_update, mock_context)
        
        # Verify confirmation message was sent
        mock_admin_update.message.reply_text.assert_called_once()
        call_args = mock_admin_update.message.reply_text.call_args[0][0]
        assert "Use /clear confirm" in call_args
        
        # Verify data was not cleared
        admin_handlers.storage.clear_all_data.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_clear_data_with_confirmation(self, admin_handlers, mock_admin_update, mock_context, mock_localizer):
        """Test clear data command with confirmation"""
        mock_context.args = ["confirm"]
        mock_localizer.get_text.return_value = "Data cleared"
        
        await admin_handlers.clear_data(mock_admin_update, mock_context)
        
        # Verify success message was sent
        mock_admin_update.message.reply_text.assert_called_once()
        call_args = mock_admin_update.message.reply_text.call_args[0][0]
        assert "Data cleared" in call_args
        
        # Verify data was cleared
        admin_handlers.storage.clear_all_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_export_data_admin(self, admin_handlers, mock_admin_update, mock_context, mock_localizer):
        """Test export data command as admin"""
        mock_localizer.get_text.return_value = "Export complete"
        
        await admin_handlers.export_data(mock_admin_update, mock_context)
        
        # Verify document was sent
        mock_admin_update.message.reply_document.assert_called_once()
        
        # Check that JSON data was created
        call_args = mock_admin_update.message.reply_document.call_args
        assert call_args[1]["filename"].endswith(".json")
        assert "Export complete" in call_args[1]["caption"]
    
    @pytest.mark.asyncio
    async def test_export_data_non_admin(self, admin_handlers, mock_user_update, mock_context, mock_localizer):
        """Test export data command as non-admin"""
        mock_localizer.get_text.return_value = "Admin only command"
        
        await admin_handlers.export_data(mock_user_update, mock_context)
        
        # Verify admin-only message was sent
        mock_user_update.message.reply_text.assert_called_once()
        call_args = mock_user_update.message.reply_text.call_args[0][0]
        assert "Admin only command" in call_args
        
        # Verify no document was sent
        mock_user_update.message.reply_document.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_stats_command_admin(self, admin_handlers, mock_admin_update, mock_context, mock_localizer):
        """Test stats command as admin"""
        await admin_handlers.stats_command(mock_admin_update, mock_context)
        
        # Verify message was sent
        mock_admin_update.message.reply_text.assert_called_once()
        call_args = mock_admin_update.message.reply_text.call_args[0][0]
        
        # Should contain statistics
        assert "Statistics" in call_args or "VSA" in call_args or "H2H" in call_args
    
    @pytest.mark.asyncio
    async def test_confirm_registration_success(self, admin_handlers, mock_admin_update, mock_context, mock_localizer):
        """Test successful registration confirmation"""
        mock_localizer.get_text.return_value = "Registration confirmed for pending_user"
        
        await admin_handlers.confirm_registration(mock_admin_update, mock_context, "pending_user")
        
        # Verify confirmation was called
        admin_handlers.storage.confirm_registration.assert_called_once()
        
        # Verify success message was sent
        mock_admin_update.message.reply_text.assert_called_once()
        call_args = mock_admin_update.message.reply_text.call_args[0][0]
        assert "Registration confirmed for pending_user" in call_args
    
    @pytest.mark.asyncio
    async def test_confirm_registration_not_found(self, admin_handlers, mock_admin_update, mock_context, mock_localizer):
        """Test confirmation for non-existent registration"""
        mock_localizer.get_text.return_value = "No pending registration found"
        
        await admin_handlers.confirm_registration(mock_admin_update, mock_context, "nonexistent_user")
        
        # Verify error message was sent
        mock_admin_update.message.reply_text.assert_called_once()
        call_args = mock_admin_update.message.reply_text.call_args[0][0]
        assert "No pending registration found" in call_args
        
        # Verify confirmation was not called
        admin_handlers.storage.confirm_registration.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_confirm_registration_non_admin(self, admin_handlers, mock_user_update, mock_context, mock_localizer):
        """Test confirmation by non-admin"""
        mock_localizer.get_text.return_value = "Admin only command"
        
        await admin_handlers.confirm_registration(mock_user_update, mock_context, "pending_user")
        
        # Verify admin-only message was sent
        mock_user_update.message.reply_text.assert_called_once()
        call_args = mock_user_update.message.reply_text.call_args[0][0]
        assert "Admin only command" in call_args
        
        # Verify confirmation was not called
        admin_handlers.storage.confirm_registration.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__])
