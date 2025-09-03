import sys
import os
import pytest
from unittest.mock import AsyncMock, Mock, patch

# Add the 'src' directory to the Python path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.mark.asyncio
async def test_personality_integration():
    """Test that the personality system works correctly with the message processing."""
    # Import the main module dynamically to avoid import issues
    import src.main
    
    # Create a mock message
    mock_author = Mock()
    mock_author.id = "123456789"
    
    mock_channel = AsyncMock()
    
    mock_message = Mock()
    mock_message.author = mock_author
    mock_message.channel = mock_channel
    mock_message.content = "What is your role?"
    mock_message.created_at = "2025-01-01 12:00:00"
    mock_message.mentions = []
    
    # Create a mock guild
    mock_guild = Mock()
    mock_guild.id = 987654321
    
    # Attach guild to message
    mock_message.guild = mock_guild
    
    # Create a mock bot user
    mock_bot_user = Mock()
    mock_bot_user.id = "987654321"
    mock_bot_user.mentioned_in = Mock(return_value=True)
    
    # Create a mock bot
    mock_bot = Mock()
    mock_bot.process_commands = AsyncMock()
    mock_bot.user = mock_bot_user
    mock_bot.user.mentioned_in = Mock(return_value=True)
    src.main.bot = mock_bot
    
    # Set up personality
    from src.utils.personalities import set_server_personality
    set_server_personality(mock_guild.id, "tech_expert")
    
    # Mock the database manager
    with patch('src.main.db_manager') as mock_db_manager:
        mock_db_manager.update_user_memory = AsyncMock()
        mock_db_manager.get_user_memory = AsyncMock(return_value={"known_facts": "{}", "interaction_history": "[]"})
        mock_db_manager.get_server_memory = AsyncMock(return_value={"known_facts": "{}"})
        
        # Mock litellm.completion to capture the prompt
        captured_prompt = {}
        def capture_prompt(model, messages):
            captured_prompt['prompt'] = messages[0]['content']
            return {
                'choices': [{
                    'message': {
                        'content': 'I am a tech expert AI assistant.'
                    }
                }]
            }
        
        with patch('src.main.litellm.completion', side_effect=capture_prompt):
            # Mock emoji analyzer
            with patch('src.main.create_enhanced_emoji_prompt', return_value=""):
                # Call the on_message function
                await src.main.on_message(mock_message)
                
                # Verify that the prompt contains the tech expert personality
                assert 'prompt' in captured_prompt
                assert 'Tech Expert' in captured_prompt['prompt']
                assert 'technology expert' in captured_prompt['prompt'].lower()

def test_personality_storage():
    """Test that personalities are stored and retrieved correctly."""
    from src.utils.personalities import get_server_personality, set_server_personality, server_personalities
    
    # Clear the server personalities to ensure a clean state
    server_personalities.clear()
    
    # Test setting and getting server personalities
    guild_id = 123456789
    personality_name = "tech_expert"
    
    # Initially should return default
    assert get_server_personality(guild_id) == "default"
    
    # Set a personality
    set_server_personality(guild_id, personality_name)
    
    # Should now return the set personality
    assert get_server_personality(guild_id) == personality_name