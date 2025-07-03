"""
Unit tests for NLP processor
"""

import pytest
from bot.nlp import NLPProcessor


class TestNLPProcessor:
    """Test cases for NLPProcessor class"""
    
    @pytest.fixture
    def nlp_processor(self):
        """Create NLP processor instance"""
        return NLPProcessor()
    
    def test_parse_team_name_russian(self, nlp_processor):
        """Test parsing Russian team name command"""
        messages = [
            "Бот, мой ник TestTeam",
            "бот мой ник AwesomeTeam",
            "Бот, команда SuperTeam"
        ]
        
        for message in messages:
            result = nlp_processor.parse_message(message, "ru")
            assert result is not None
            assert result["type"] == "set_team_name"
            assert len(result["team_name"]) > 0
    
    def test_parse_team_name_english(self, nlp_processor):
        """Test parsing English team name command"""
        messages = [
            "Bot, my nick TestTeam",
            "bot my nickname AwesomeTeam",
            "Bot, team name SuperTeam"
        ]
        
        for message in messages:
            result = nlp_processor.parse_message(message, "en")
            assert result is not None
            assert result["type"] == "set_team_name"
            assert len(result["team_name"]) > 0
    
    def test_parse_vsa_rating_russian(self, nlp_processor):
        """Test parsing Russian VSA rating command"""
        messages = [
            "Бот, мой рекорд в VSA 42",
            "бот мой рекорд в vsa 35",
            "Бот, VSA рейтинг 50"
        ]
        
        for message in messages:
            result = nlp_processor.parse_message(message, "ru")
            assert result is not None
            assert result["type"] == "set_vsa_rating"
            assert isinstance(result["rating"], int)
            assert result["rating"] > 0
    
    def test_parse_vsa_rating_english(self, nlp_processor):
        """Test parsing English VSA rating command"""
        messages = [
            "Bot, my VSA rating 42",
            "bot vsa 35",
            "Bot, my VSA record 50"
        ]
        
        for message in messages:
            result = nlp_processor.parse_message(message, "en")
            assert result is not None
            assert result["type"] == "set_vsa_rating"
            assert isinstance(result["rating"], int)
            assert result["rating"] > 0
    
    def test_parse_h2h_rating_russian(self, nlp_processor):
        """Test parsing Russian H2H rating command"""
        messages = [
            "Бот, мой рекорд в H2H 38",
            "бот мой рекорд в h2h 45",
            "Бот, H2H рейтинг 30"
        ]
        
        for message in messages:
            result = nlp_processor.parse_message(message, "ru")
            assert result is not None
            assert result["type"] == "set_h2h_rating"
            assert isinstance(result["rating"], int)
            assert result["rating"] > 0
    
    def test_parse_h2h_rating_english(self, nlp_processor):
        """Test parsing English H2H rating command"""
        messages = [
            "Bot, my H2H rating 38",
            "bot h2h 45",
            "Bot, my H2H record 30"
        ]
        
        for message in messages:
            result = nlp_processor.parse_message(message, "en")
            assert result is not None
            assert result["type"] == "set_h2h_rating"
            assert isinstance(result["rating"], int)
            assert result["rating"] > 0
    
    def test_parse_admin_confirm_russian(self, nlp_processor):
        """Test parsing Russian admin confirmation command"""
        messages = [
            "Бот @testuser +1",
            "бот testuser +1",
            "Бот, подтвердить testuser"
        ]
        
        for message in messages:
            result = nlp_processor.parse_message(message, "ru")
            assert result is not None
            assert result["type"] == "admin_confirm"
            assert result["username"] == "testuser"
    
    def test_parse_admin_confirm_english(self, nlp_processor):
        """Test parsing English admin confirmation command"""
        messages = [
            "Bot @testuser +1",
            "bot testuser +1",
            "Bot, confirm testuser"
        ]
        
        for message in messages:
            result = nlp_processor.parse_message(message, "en")
            assert result is not None
            assert result["type"] == "admin_confirm"
            assert result["username"] == "testuser"
    
    def test_parse_unrecognized_message(self, nlp_processor):
        """Test parsing unrecognized messages"""
        messages = [
            "Hello world",
            "Random text",
            "Bot help me",
            "What is this?"
        ]
        
        for message in messages:
            result = nlp_processor.parse_message(message, "en")
            assert result is None
    
    def test_parse_empty_message(self, nlp_processor):
        """Test parsing empty or None messages"""
        messages = [None, "", "   ", "\n\t"]
        
        for message in messages:
            result = nlp_processor.parse_message(message, "en")
            assert result is None
    
    def test_parse_case_insensitive(self, nlp_processor):
        """Test that parsing is case insensitive"""
        messages = [
            "BOT, MY NICK TESTTEAM",
            "Bot, My Nick TestTeam",
            "bot, my nick testteam"
        ]
        
        for message in messages:
            result = nlp_processor.parse_message(message, "en")
            assert result is not None
            assert result["type"] == "set_team_name"
    
    def test_validate_extracted_data(self, nlp_processor):
        """Test validation of extracted data"""
        # Valid team name
        valid_team = {"type": "set_team_name", "team_name": "ValidTeam"}
        assert nlp_processor.validate_extracted_data(valid_team) is True
        
        # Invalid team name (too long)
        invalid_team = {"type": "set_team_name", "team_name": "A" * 100}
        assert nlp_processor.validate_extracted_data(invalid_team) is False
        
        # Valid rating
        valid_rating = {"type": "set_vsa_rating", "rating": 50}
        assert nlp_processor.validate_extracted_data(valid_rating) is True
        
        # Invalid rating (too high)
        invalid_rating = {"type": "set_vsa_rating", "rating": 150}
        assert nlp_processor.validate_extracted_data(invalid_rating) is False
        
        # Valid username
        valid_username = {"type": "admin_confirm", "username": "testuser"}
        assert nlp_processor.validate_extracted_data(valid_username) is True
        
        # Invalid username (too short)
        invalid_username = {"type": "admin_confirm", "username": "ab"}
        assert nlp_processor.validate_extracted_data(invalid_username) is False
    
    def test_get_examples(self, nlp_processor):
        """Test getting command examples"""
        # English examples
        en_examples = nlp_processor.get_examples("en")
        assert len(en_examples) > 0
        assert any("nick" in example.lower() for example in en_examples)
        assert any("vsa" in example.lower() for example in en_examples)
        assert any("h2h" in example.lower() for example in en_examples)
        
        # Russian examples
        ru_examples = nlp_processor.get_examples("ru")
        assert len(ru_examples) > 0
        assert any("ник" in example.lower() for example in ru_examples)
        assert any("vsa" in example.lower() for example in ru_examples)
        assert any("h2h" in example.lower() for example in ru_examples)
    
    def test_language_fallback(self, nlp_processor):
        """Test language fallback mechanism"""
        # Use unsupported language, should fallback to English
        result = nlp_processor.parse_message("Bot, my nick TestTeam", "fr")
        assert result is not None
        assert result["type"] == "set_team_name"
        assert result["team_name"] == "TestTeam"


if __name__ == "__main__":
    pytest.main([__file__])
