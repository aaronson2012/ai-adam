# tests/unit/test_emoji_parser.py

import pytest
import discord
from unittest.mock import Mock
from src.utils.emoji_parser import (
    extract_emoji_tags,
    validate_emoji_tag,
    convert_emoji_tag_to_discord_emoji,
    replace_emoji_tags,
    find_invalid_emoji_tags,
    has_emoji_tags
)

class TestEmojiParser:
    def test_extract_emoji_tags(self):
        """Test extracting emoji tags from text."""
        # Test basic extraction
        text = "Hello {smile} world {heart}"
        result = extract_emoji_tags(text)
        assert result == ["smile", "heart"]
        
        # Test with no tags
        text = "Hello world"
        result = extract_emoji_tags(text)
        assert result == []
        
        # Test with nested braces (will match inner content)
        text = "Hello {smile {nested} world} test"
        result = extract_emoji_tags(text)
        assert result == ["nested"]  # Inner content is matched
        
        # Test with special characters
        text = "Hello {smile_emoji} and {heart-eyes}"
        result = extract_emoji_tags(text)
        assert result == ["smile_emoji", "heart-eyes"]
    
    def test_has_emoji_tags(self):
        """Test checking if text has emoji tags."""
        # Test with tags
        text = "Hello {smile} world"
        assert has_emoji_tags(text) == True
        
        # Test without tags
        text = "Hello smile world"
        assert has_emoji_tags(text) == False
        
        # Test with empty string
        assert has_emoji_tags("") == False
    
    def test_validate_emoji_tag(self):
        """Test validating emoji tags."""
        # Create a mock guild with emojis
        mock_emoji1 = Mock()
        mock_emoji1.name = "smile"
        
        mock_emoji2 = Mock()
        mock_emoji2.name = "heart"
        
        mock_guild = Mock()
        mock_guild.emojis = [mock_emoji1, mock_emoji2]
        
        # Test valid custom emoji
        assert validate_emoji_tag("smile", mock_guild) == True
        assert validate_emoji_tag("heart", mock_guild) == True
        
        # Test invalid custom emoji
        assert validate_emoji_tag("invalid", mock_guild) == False
        
        # Test Unicode emoji (simplified)
        assert validate_emoji_tag("👍", mock_guild) == True
        assert validate_emoji_tag("😀", mock_guild) == True
    
    def test_convert_emoji_tag_to_discord_emoji(self):
        """Test converting emoji tags to Discord emojis."""
        # Create a mock guild with emojis
        mock_emoji = Mock()
        mock_emoji.name = "smile"
        mock_emoji.__str__ = Mock(return_value="<:smile:123456789>")
        
        mock_guild = Mock()
        mock_guild.emojis = [mock_emoji]
        
        # Test custom emoji conversion
        result = convert_emoji_tag_to_discord_emoji("smile", mock_guild)
        assert result == "<:smile:123456789>"
        
        # Test invalid emoji (should return None)
        result = convert_emoji_tag_to_discord_emoji("invalid", mock_guild)
        assert result is None
        
        # Test Unicode emoji (should return as-is)
        result = convert_emoji_tag_to_discord_emoji("👍", mock_guild)
        assert result == "👍"
    
    def test_replace_emoji_tags(self):
        """Test replacing emoji tags with Discord emojis."""
        # Create a mock guild with emojis
        mock_emoji = Mock()
        mock_emoji.name = "smile"
        mock_emoji.__str__ = Mock(return_value="<:smile:123456789>")
        
        mock_guild = Mock()
        mock_guild.emojis = [mock_emoji]
        
        # Test replacement
        text = "Hello {smile} world"
        result = replace_emoji_tags(text, mock_guild)
        assert result == "Hello <:smile:123456789> world"
        
        # Test with invalid emoji (should keep original tag)
        text = "Hello {invalid} world"
        result = replace_emoji_tags(text, mock_guild)
        assert result == "Hello {invalid} world"
        
        # Test with mixed valid and invalid
        text = "Hello {smile} and {invalid} world"
        result = replace_emoji_tags(text, mock_guild)
        assert result == "Hello <:smile:123456789> and {invalid} world"
        
        # Test with no tags
        text = "Hello world"
        result = replace_emoji_tags(text, mock_guild)
        assert result == "Hello world"
    
    def test_find_invalid_emoji_tags(self):
        """Test finding invalid emoji tags."""
        # Create a mock guild with emojis
        mock_emoji1 = Mock()
        mock_emoji1.name = "smile"
        
        mock_emoji2 = Mock()
        mock_emoji2.name = "heart"
        
        mock_guild = Mock()
        mock_guild.emojis = [mock_emoji1, mock_emoji2]
        
        # Test with invalid tags
        text = "Hello {smile} and {invalid} world {another_invalid}"
        result = find_invalid_emoji_tags(text, mock_guild)
        assert set(result) == {"invalid", "another_invalid"}
        
        # Test with all valid tags
        text = "Hello {smile} and {heart} world"
        result = find_invalid_emoji_tags(text, mock_guild)
        assert result == []
        
        # Test with no tags
        text = "Hello world"
        result = find_invalid_emoji_tags(text, mock_guild)
        assert result == []

if __name__ == "__main__":
    pytest.main([__file__])