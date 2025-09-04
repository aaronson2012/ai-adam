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
    
    return mock_message

@pytest.fixture
def mock_bot_user():
    """Create a mock bot user for testing."""
    mock_bot_user = Mock()
    mock_bot_user.id = "987654321"
    return mock_bot_user

@pytest.mark.asyncio
async def test_on_message_ignores_bot_messages(mock_message, mock_bot_user):
    """Test that the bot ignores messages from itself."""
    # Import the main module dynamically to avoid import issues
    import src.main
    
    # Create a mock bot and set its user property
    mock_bot = Mock()
    mock_bot.process_commands = AsyncMock()
    type(mock_bot).user = mock_bot_user
    src.main.bot = mock_bot
    
    # Set the message author to the bot user
    mock_message.author = mock_bot_user
    
    # Mock the mentioned_in method to return False
    mock_bot_user.mentioned_in = Mock(return_value=False)
    
    # Mock message mentions
    mock_message.mentions = []
    
    # Call the on_message function
    with patch('src.main.db_manager') as mock_db_manager:
        await src.main.on_message(mock_message)
        
        # The database manager should not be called
        mock_db_manager.get_user_memory.assert_not_called()

@pytest.mark.asyncio
async def test_on_message_handles_exceptions(mock_message, mock_bot_user):
    """Test that the bot handles exceptions gracefully."""
    # Import the main module dynamically to avoid import issues
    import src.main
    
    # Create a mock bot and set its user property
    mock_bot = Mock()
    mock_bot.process_commands = AsyncMock()
    mock_bot.user = mock_bot_user
    src.main.bot = mock_bot
    
    # Mock the mentioned_in method to return True
    mock_bot_user.mentioned_in = Mock(return_value=True)
    
    # Mock message mentions
    mock_message.mentions = []
    
    # Mock the database manager to return some memory
    with patch('src.main.db_manager') as mock_db_manager:
        mock_db_manager.update_user_memory = AsyncMock()
        mock_db_manager.get_user_memory = AsyncMock(return_value={"known_facts": "{}", "interaction_history": "[]"})
        mock_db_manager.get_server_memory = AsyncMock(return_value={"known_facts": "{}"})
        
        # Mock litellm.completion to raise an exception
        with patch('src.main.litellm.completion', side_effect=Exception("Test error")):
            await src.main.on_message(mock_message)
            
            # Check that the error message was sent
            mock_message.channel.send.assert_called_with("Sorry, I encountered an error processing your request.")

@pytest.mark.asyncio
async def test_on_message_processes_user_message(mock_message, mock_bot_user):
    """Test that the bot processes user messages correctly."""
    # Import the main module dynamically to avoid import issues
    import src.main
    
    # Create a mock bot and set its user property
    mock_bot = Mock()
    mock_bot.process_commands = AsyncMock()
    mock_bot.user = mock_bot_user
    src.main.bot = mock_bot
    
    # Mock the mentioned_in method to return True
    mock_bot_user.mentioned_in = Mock(return_value=True)
    
    # Mock message mentions
    mock_message.mentions = []
    
    # Mock the database manager
    with patch('src.main.db_manager') as mock_db_manager:
        mock_db_manager.update_user_memory = AsyncMock()
        mock_db_manager.get_user_memory = AsyncMock(return_value={"known_facts": "{}", "interaction_history": "[]"})
        mock_db_manager.get_server_memory = AsyncMock(return_value={"known_facts": "{}"})
        
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
            
            # Check that the response was sent
            mock_message.channel.send.assert_called_with('Hello! I am doing well, thank you for asking.')
            
            # Check that the database was updated twice (once for learning, once for response)
            assert mock_db_manager.update_user_memory.call_count == 2

@pytest.mark.asyncio
async def test_on_message_ignores_everyone_mentions(mock_message, mock_bot_user):
    """Test that the bot ignores @everyone mentions."""
    # Import the main module dynamically to avoid import issues
    import src.main
    
    # Create a mock bot and set its user property
    mock_bot = Mock()
    mock_bot.process_commands = AsyncMock()
    mock_bot.user = mock_bot_user
    src.main.bot = mock_bot
    
    # Mock the mentioned_in method to return True (mentioned)
    mock_bot_user.mentioned_in = Mock(return_value=True)
    
    # Set mention_everyone to True to simulate @everyone
    mock_message.mention_everyone = True
    
    # Mock message mentions
    mock_message.mentions = []
    
    # Mock the database manager
    with patch('src.main.db_manager') as mock_db_manager:
        mock_db_manager.update_user_memory = AsyncMock()
        mock_db_manager.get_user_memory = AsyncMock(return_value={"known_facts": "{}", "interaction_history": "[]"})
        mock_db_manager.get_server_memory = AsyncMock(return_value={"known_facts": "{}"})
        
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
            
            # Check that the response was NOT sent (bot should ignore @everyone)
            mock_message.channel.send.assert_not_called()
            
            # Check that the database was only updated once for learning, not for response
            assert mock_db_manager.update_user_memory.call_count == 1

def test_llm_env_vars_complete():
    """Test that the LLM environment variables list is comprehensive."""
    # Import the main module dynamically to avoid import issues
    import src.main
    
    # Check that we have a reasonable number of environment variables
    assert len(src.main.llm_env_vars) > 20
    
    # Check that some common ones are present
    common_vars = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY']
    for var in common_vars:
        assert var in src.main.llm_env_vars