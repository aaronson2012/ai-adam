# tests/integration/test_emoji_system.py

import pytest
import discord
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from src.utils.emoji_parser import replace_emoji_tags, find_invalid_emoji_tags
from src.utils.ai_response_validator import validate_and_retry_ai_response

class TestEmojiSystem:
    def test_emoji_tag_replacement(self):
        """Test that emoji tags are correctly replaced with Discord emojis."""
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
    
    def test_invalid_emoji_detection(self):
        """Test that invalid emoji tags are correctly detected."""
        # Create a mock guild with emojis
        mock_emoji = Mock()
        mock_emoji.name = "smile"
        
        mock_guild = Mock()
        mock_guild.emojis = [mock_emoji]
        
        # Test with invalid emoji
        text = "Hello {invalid} world"
        invalid_emojis = find_invalid_emoji_tags(text, mock_guild)
        assert invalid_emojis == ["invalid"]
        
        # Test with valid emoji
        text = "Hello {smile} world"
        invalid_emojis = find_invalid_emoji_tags(text, mock_guild)
        assert invalid_emojis == []
    
    @pytest.mark.asyncio
    async def test_ai_response_validation_and_retry(self):
        """Test the complete AI response validation and retry system."""
        # Create a mock guild with emojis
        mock_emoji = Mock()
        mock_emoji.name = "smile"
        
        mock_guild = Mock()
        mock_guild.emojis = [mock_emoji]
        
        # Configuration
        config = {
            'ai': {
                'default_model': 'test-model'
            }
        }
        
        # Test response with invalid emoji
        response_text = "Hello {invalid} world"
        original_prompt = "Say hello"
        
        # Mock the litellm.completion to return a corrected response
        with patch('src.utils.ai_response_validator.litellm') as mock_litellm:
            mock_litellm.completion.return_value = {
                'choices': [{
                    'message': {
                        'content': 'Hello {smile} world'
                    }
                }]
            }
            
            result_text, was_retried = await validate_and_retry_ai_response(
                response_text, mock_guild, config, original_prompt
            )
            
            # Should have been retried and corrected
            assert result_text == "Hello {smile} world"
            assert was_retried == True
    
    @pytest.mark.asyncio
    async def test_complete_emoji_system_integration(self):
        """Test the complete emoji system integration."""
        # Create a mock guild with emojis
        mock_emoji = Mock()
        mock_emoji.name = "smile"
        mock_emoji.__str__ = Mock(return_value="<:smile:123456789>")
        
        mock_guild = Mock()
        mock_guild.emojis = [mock_emoji]
        
        # Configuration
        config = {
            'ai': {
                'default_model': 'test-model'
            }
        }
        
        # Test response with invalid emoji that gets corrected
        response_text = "Hello {invalid} world"
        original_prompt = "Say hello"
        
        # Mock the litellm.completion to return a corrected response
        with patch('src.utils.ai_response_validator.litellm') as mock_litellm:
            mock_litellm.completion.return_value = {
                'choices': [{
                    'message': {
                        'content': 'Hello {smile} world! 👍'
                    }
                }]
            }
            
            # First validate and retry
            corrected_text, was_retried = await validate_and_retry_ai_response(
                response_text, mock_guild, config, original_prompt
            )
            
            # Then process emoji tags
            final_text = replace_emoji_tags(corrected_text, mock_guild)
            
            # Should have been corrected and processed
            assert corrected_text == "Hello {smile} world! 👍"
            assert was_retried == True
            assert final_text == "Hello <:smile:123456789> world! 👍"

if __name__ == "__main__":
    pytest.main([__file__])