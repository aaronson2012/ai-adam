import sys
import os
import pytest
from unittest.mock import AsyncMock, Mock, patch

# Add the 'src' directory to the Python path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_personality_integration():
    """Test that the personality system is correctly integrated into the main module."""
    # Import the main module dynamically to avoid import issues
    import src.main
    
    # Check that the personality system is imported
    assert hasattr(src.main, 'get_personality_prompt')
    
    # Test that we can get the default personality prompt
    personality_prompt = src.main.get_personality_prompt("default")
    assert isinstance(personality_prompt, str)
    assert len(personality_prompt) > 0
    
    # Verify that the prompt contains key characteristics
    assert "natural" in personality_prompt.lower()
    assert "genuine" in personality_prompt.lower()
    assert "guidelines" in personality_prompt.lower()

@pytest.mark.asyncio
async def test_personality_used_in_prompt():
    """Test that the personality is used in the LLM prompt."""
    # Import the main module dynamically to avoid import issues
    import src.main
    
    # Create a mock message
    mock_author = Mock()
    mock_author.id = "123456789"
    
    mock_channel = AsyncMock()
    
    mock_message = Mock()
    mock_message.author = mock_author
    mock_message.channel = mock_channel
    mock_message.content = "Hello, how are you?"
    mock_message.created_at = "2025-01-01 12:00:00"
    
    # Create a mock bot user
    mock_bot_user = Mock()
    mock_bot_user.id = "987654321"
    mock_bot_user.mentioned_in = Mock(return_value=True)
    
    # Create a mock bot
    mock_bot = Mock()
    mock_bot.process_commands = AsyncMock()
    mock_bot.user = mock_bot_user
    src.main.bot = mock_bot
    
    # Mock the personality prompt
    with patch('src.main.get_personality_prompt') as mock_get_personality_prompt:
        mock_get_personality_prompt.return_value = "Test personality prompt"
        
        # Mock the database manager
        with patch('src.main.db_manager') as mock_db_manager:
            mock_db_manager.update_user_memory = AsyncMock()
            mock_db_manager.get_user_memory = AsyncMock(return_value={"known_facts": "{}", "interaction_history": "[]"})
            
            # Mock litellm.completion
            mock_response = {
                'choices': [{
                    'message': {
                        'content': 'Hello! I am doing well, thank you for asking.'
                    }
                }]
            }
            with patch('src.main.litellm.completion', return_value=mock_response):
                # Call the on_message function
                await src.main.on_message(mock_message)
                
                # Verify that the personality prompt was requested
                mock_get_personality_prompt.assert_called_with("default")