"""
Unit tests for bot handlers
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes

from bot.handlers import BotHandlers
from bot.storage import DataStorage
from bot.localization import Localizer
from bot.nlp import NLPProcessor


class TestBotHandlers:
    """Test cases for BotHandlers class"""
    
    @pytest.fixture
    def mock_storage(self):
        """Create mock storage"""
        storage = MagicMock(spec=DataStorage)
        storage.save_temp_registration = AsyncMock(return_value=True)
        storage.get_all_players.return_value = {"vsa": {}, "h2h": {}}
        storage.get_temp_registrations.return_value = {}
        return storage
    
    @pytest.fixture
    def mock_localizer(self):
        """Create mock localizer"""
        localizer = MagicMock(spec=Localizer)
        localizer.get_text.return_value = "Test message"
        return localizer
    
    @pytest.fixture
    def mock_nlp(self):
        """Create mock NLP processor"""
        nlp = MagicMock(spec=NLPProcessor)
        return nlp
    
    @pytest.fixture
    def handlers(self, mock_storage, mock_localizer, mock_nlp):
        """Create handlers instance"""
        return BotHandlers(mock_storage, mock_localizer, mock_nlp)
    
    @pytest.fixture
    def mock_update(self):
        """Create mock update"""
        user = User(id=123, first_name="Test", is_bot=False, username="testuser")
        chat = Chat(id=123, type="private")
        message = Message(
            message_id=1,
            date=None,
            chat=chat,
            from_user=user,
            text="Test message"
        )
        message.reply_text = AsyncMock()
        
        update = Update(update_id=1, message=message)
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context"""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        return context
    
    @pytest.mark.asyncio
    async def test_start_command(self, handlers, mock_update, mock_context, mock_localizer):
        """Test /start command"""
        mock_localizer.get_text.side_effect = lambda key, lang: f"localized_{key}"
        
        await handlers.start_command(mock_update, mock_context)
        
        # Verify message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "localized_welcome_message" in call_args[0][0]
        
        # Verify localizer was called
        assert mock_localizer.get_text.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_help_command(self, handlers, mock_update, mock_context, mock_localizer):
        """Test /help command"""
        mock_localizer.get_text.side_effect = lambda key, lang: f"localized_{key}"
        
        await handlers.help_command(mock_update, mock_context)
        
        # Verify message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "localized_help_message" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_process_message_team_name(self, handlers, mock_update, mock_context, mock_nlp, mock_localizer):
        """Test processing team name message"""
        # Setup NLP to return team name command
        mock_nlp.parse_message.return_value = {
            "type": "set_team_name",
            "team_name": "TestTeam"
        }
        mock_localizer.get_text.return_value = "Team name saved: TestTeam"
        
        await handlers.process_message(mock_update, mock_context)
        
        # Verify NLP was called
        mock_nlp.parse_message.assert_called_once()
        
        # Verify team name was stored in context
        assert "registration_data" in mock_context.user_data
        assert mock_context.user_data["registration_data"]["team_name"] == "TestTeam"
        
        # Verify response was sent
        mock_update.message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_vsa_rating(self, handlers, mock_update, mock_context, mock_nlp, mock_storage, mock_localizer):
        """Test processing VSA rating message"""
        # Setup context with existing team name
        mock_context.user_data = {
            "registration_data": {
                "team_name": "TestTeam"
            }
        }
        
        # Setup NLP to return VSA rating command
        mock_nlp.parse_message.return_value = {
            "type": "set_vsa_rating",
            "rating": 42
        }
        mock_localizer.get_text.return_value = "VSA rating saved"
        
        await handlers.process_message(mock_update, mock_context)
        
        # Verify storage was called
        mock_storage.save_temp_registration.assert_called_once_with(
            user_id=123,
            username="testuser",
            tournament_type="vsa",
            team_name="TestTeam",
            rating=42
        )
        
        # Verify response was sent
        mock_update.message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_no_team_name(self, handlers, mock_update, mock_context, mock_nlp, mock_localizer):
        """Test processing rating without team name"""
        # Setup NLP to return rating command
        mock_nlp.parse_message.return_value = {
            "type": "set_vsa_rating",
            "rating": 42
        }
        mock_localizer.get_text.return_value = "Team name required first"
        
        await handlers.process_message(mock_update, mock_context)
        
        # Verify error message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Team name required first" in call_args
    
    @pytest.mark.asyncio
    async def test_process_message_unrecognized(self, handlers, mock_update, mock_context, mock_nlp, mock_localizer):
        """Test processing unrecognized message"""
        # Setup NLP to return None (unrecognized)
        mock_nlp.parse_message.return_value = None
        mock_localizer.get_text.return_value = "Unrecognized command"
        
        await handlers.process_message(mock_update, mock_context)
        
        # Verify help message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Unrecognized command" in call_args
    
    @pytest.mark.asyncio
    async def test_process_message_exception(self, handlers, mock_update, mock_context, mock_nlp, mock_localizer):
        """Test processing message with exception"""
        # Setup NLP to raise exception
        mock_nlp.parse_message.side_effect = Exception("Test error")
        mock_localizer.get_text.return_value = "Processing error"
        
        await handlers.process_message(mock_update, mock_context)
        
        # Verify error message was sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Processing error" in call_args


if __name__ == "__main__":
    pytest.main([__file__])
