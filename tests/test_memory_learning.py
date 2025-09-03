import sys
import os
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch

# Add the 'src' directory to the Python path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def mock_message():
    """Create a mock Discord message for testing."""
    mock_author = Mock()
    mock_author.id = "123456789"
    mock_author.mention = "<@123456789>"
    
    mock_channel = AsyncMock()
    
    mock_message = Mock()
    mock_message.author = mock_author
    mock_message.channel = mock_channel
    mock_message.content = "Hello, how are you?"
    mock_message.created_at = "2025-01-01 12:00:00"
    
    return mock_message

@pytest.fixture
def mock_bot_user():
    """Create a mock bot user for testing."""
    mock_bot_user = Mock()
    mock_bot_user.id = "987654321"
    return mock_bot_user

@pytest.mark.asyncio
async def test_on_message_always_updates_memory(mock_message, mock_bot_user):
    """Test that the bot always updates user memory, even when not responding."""
    # Import the main module dynamically to avoid import issues
    import src.main
    
    # Create a mock bot and set its user property
    mock_bot = Mock()
    mock_bot.process_commands = AsyncMock()
    mock_bot.user = mock_bot_user
    src.main.bot = mock_bot
    
    # Mock the mentioned_in method to return False (not mentioned)
    mock_bot_user.mentioned_in = Mock(return_value=False)
    
    # Mock message mentions
    mock_message.mentions = []
    
    # Mock the database manager
    with patch('src.main.db_manager') as mock_db_manager:
        mock_db_manager.update_user_memory = AsyncMock()
        mock_db_manager.get_user_memory = AsyncMock(return_value={"known_facts": "{}", "interaction_history": "[]"})
        
        # Mock litellm.completion to return a response
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'Hello! I am doing well, thank you for asking.'
                }
            }]
        }
        with patch('src.main.litellm.completion', return_value=mock_response):
            await src.main.on_message(mock_message)
            
            # Check that memory was updated even though bot wasn't mentioned
            mock_db_manager.update_user_memory.assert_called_once()
            
            # Check that no response was sent since bot wasn't mentioned
            mock_message.channel.send.assert_not_called()

@pytest.mark.asyncio
async def test_on_message_responds_when_mentioned(mock_message, mock_bot_user):
    """Test that the bot responds when mentioned."""
    # Import the main module dynamically to avoid import issues
    import src.main
    
    # Create a mock bot and set its user property
    mock_bot = Mock()
    mock_bot.process_commands = AsyncMock()
    mock_bot.user = mock_bot_user
    src.main.bot = mock_bot
    
    # Mock the mentioned_in method to return True (mentioned)
    mock_bot_user.mentioned_in = Mock(return_value=True)
    
    # Mock message mentions
    mock_message.mentions = []
    
    # Mock the database manager
    with patch('src.main.db_manager') as mock_db_manager:
        mock_db_manager.update_user_memory = AsyncMock()
        mock_db_manager.get_user_memory = AsyncMock(return_value={"known_facts": "{}", "interaction_history": "[]"})
        
        # Mock litellm.completion to return a response
        mock_response = {
            'choices': [{
                'message': {
                    'content': 'Hello! I am doing well, thank you for asking.'
                }
            }]
        }
        with patch('src.main.litellm.completion', return_value=mock_response):
            await src.main.on_message(mock_message)
            
            # Check that memory was updated
            assert mock_db_manager.update_user_memory.call_count == 2  # Once for learning, once for response
            
            # Check that a response was sent since bot was mentioned
            mock_message.channel.send.assert_called_with('Hello! I am doing well, thank you for asking.')