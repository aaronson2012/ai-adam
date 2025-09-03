"""
Integration test to verify that personalities are correctly applied in the AI responses.
This test verifies the fix for the issue where personalities were not being applied.
"""

import sys
import os
import pytest
from unittest.mock import AsyncMock, Mock, patch

# Add the 'src' directory to the Python path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.mark.asyncio
async def test_personality_applied_in_ai_response():
    """
    Test that when a personality is set for a server, 
    it is correctly used in the AI response generation.
    """
    # Import the main module
    import src.main
    
    # Clear any existing personality state
    from src.utils.personalities import server_personalities
    server_personalities.clear()
    
    # Create a mock message that would trigger a response
    mock_author = Mock()
    mock_author.id = "123456789"
    
    mock_channel = AsyncMock()
    
    mock_message = Mock()
    mock_message.author = mock_author
    mock_message.channel = mock_channel
    mock_message.content = "What is your role?"
    mock_message.created_at = "2025-01-01 12:00:00"
    
    # Create a mock guild
    mock_guild = Mock()
    mock_guild.id = 987654321
    mock_message.guild = mock_guild
    
    # Create a mock bot user that is mentioned in the message
    mock_bot_user = Mock()
    mock_bot_user.id = "987654321"
    mock_bot_user.mentioned_in = Mock(return_value=True)
    
    # Create a mock bot
    mock_bot = Mock()
    mock_bot.process_commands = AsyncMock()
    mock_bot.user = mock_bot_user
    mock_bot.user.mentioned_in = Mock(return_value=True)
    src.main.bot = mock_bot
    
    # Set the personality for this server to "tech_expert"
    from src.utils.personalities import set_server_personality, get_server_personality
    set_server_personality(mock_guild.id, "tech_expert")
    
    # Verify the personality was set correctly
    assert get_server_personality(mock_guild.id) == "tech_expert"
    
    # Mock the database manager
    with patch('src.main.db_manager') as mock_db_manager:
        mock_db_manager.update_user_memory = AsyncMock()
        mock_db_manager.get_user_memory = AsyncMock(return_value={"known_facts": "{}", "interaction_history": "[]"})
        
        # Mock litellm.completion to capture the prompt and return a mock response
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
                
                # Verify that the prompt was captured
                assert 'prompt' in captured_prompt
                
                # Verify that the prompt contains the tech expert personality
                prompt = captured_prompt['prompt']
                assert 'Tech Expert' in prompt
                assert 'technology expert' in prompt.lower()
                
                # Verify that the prompt contains key tech expert characteristics
                assert any(phrase in prompt.lower() for phrase in [
                    'explain complex technical topics',
                    'technology expert',
                    'technical expertise'
                ])
                
                # Verify that the response was sent
                mock_channel.send.assert_called_once_with('I am a tech expert AI assistant.')

if __name__ == "__main__":
    pytest.main([__file__, "-v"])