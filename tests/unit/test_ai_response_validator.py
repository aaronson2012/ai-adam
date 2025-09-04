# tests/unit/test_ai_response_validator.py

import pytest
from unittest.mock import Mock, patch
import asyncio
from src.utils.ai_response_validator import validate_and_retry_ai_response

# Mock the litellm module
@pytest.fixture
def mock_litellm():
    with patch('src.utils.ai_response_validator.litellm') as mock:
        yield mock

class TestAIResponseValidator:
    @pytest.mark.asyncio
    async def test_validate_and_retry_ai_response_no_invalid_emojis(self):
        """Test that response is returned unchanged when no invalid emojis are found."""
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
        
        # Response with valid emoji
        response_text = "Hello {smile} world"
        original_prompt = "Say hello"
        
        # Call the function
        result_text, was_retried = await validate_and_retry_ai_response(
            response_text, mock_guild, config, original_prompt
        )
        
        # Should return original response without retry
        assert result_text == "Hello {smile} world"
        assert was_retried == False
    
    @pytest.mark.asyncio
    async def test_validate_and_retry_ai_response_with_invalid_emojis(self, mock_litellm):
        """Test that response is retried when invalid emojis are found."""
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
        
        # Response with invalid emoji
        response_text = "Hello {invalid} world"
        original_prompt = "Say hello"
        
        # Mock the litellm.completion response
        mock_litellm.completion.return_value = {
            'choices': [{
                'message': {
                    'content': 'Hello {smile} world'
                }
            }]
        }
        
        # Call the function
        result_text, was_retried = await validate_and_retry_ai_response(
            response_text, mock_guild, config, original_prompt
        )
        
        # Should return the corrected response with retry performed
        assert result_text == "Hello {smile} world"
        assert was_retried == True
        
        # Verify that litellm.completion was called
        mock_litellm.completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_and_retry_ai_response_max_retries(self, mock_litellm):
        """Test that retry mechanism respects maximum retry limit."""
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
        
        # Response with invalid emoji
        response_text = "Hello {invalid} world"
        original_prompt = "Say hello"
        
        # Mock the litellm.completion response to always return invalid emojis
        mock_litellm.completion.return_value = {
            'choices': [{
                'message': {
                    'content': 'Hello {invalid} world'
                }
            }]
        }
        
        # Call the function with max_retries=2
        result_text, was_retried = await validate_and_retry_ai_response(
            response_text, mock_guild, config, original_prompt, max_retries=2
        )
        
        # Should return the last response after 2 retries
        assert result_text == "Hello {invalid} world"
        assert was_retried == True
        
        # Verify that litellm.completion was called 2 times (max_retries)
        assert mock_litellm.completion.call_count == 2

if __name__ == "__main__":
    pytest.main([__file__])