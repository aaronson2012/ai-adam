import sys
import os
import pytest
from unittest.mock import AsyncMock, Mock, patch
import json
import asyncio

# Add the 'src' directory to the Python path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Helper class for async iterator
class AsyncIterator:
    def __init__(self, seq):
        self.iter = iter(seq)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.iter)
        except StopIteration:
            raise StopAsyncIteration

@pytest.mark.asyncio
async def test_comprehensive_bot_integration():
    """Comprehensive integration test simulating multiple users interacting with the bot."""
    # Import the main module dynamically to avoid import issues
    import src.main
    
    # Set up database manager mock
    mock_db_manager = AsyncMock()
    
    # Track calls to verify behavior
    user_memory_calls = []
    server_memory_calls = []
    
    # Create mock methods that track calls
    async def track_get_user_memory(user_id):
        user_memory_calls.append(user_id)
        return {"known_facts": "{}", "interaction_history": "[]"}
    
    async def track_get_server_memory(guild_id):
        server_memory_calls.append(guild_id)
        return {"known_facts": "{}"}
    
    mock_db_manager.get_user_memory = track_get_user_memory
    mock_db_manager.get_server_memory = track_get_server_memory
    mock_db_manager.update_user_memory = AsyncMock()
    mock_db_manager.extract_targeted_facts = AsyncMock(return_value={})
    
    # Patch the global db_manager in main
    src.main.db_manager = mock_db_manager
    
    # Create mock users
    mock_user1 = Mock()
    mock_user1.id = "111111111"
    mock_user1.mention = "<@111111111>"
    mock_user1.display_name = "Alice"
    
    mock_user2 = Mock()
    mock_user2.id = "222222222"
    mock_user2.mention = "<@222222222>"
    mock_user2.display_name = "Bob"
    
    mock_bot_user = Mock()
    mock_bot_user.id = "999999999"
    mock_bot_user.mention = "<@999999999>"
    mock_bot_user.display_name = "AI-Adam"
    
    # Create mock channel with proper async history method
    mock_channel = AsyncMock()
    mock_channel.history = Mock(return_value=AsyncIterator([]))
    
    # Create mock guild
    mock_guild = Mock()
    mock_guild.id = 123456789
    mock_guild.name = "Test Server"
    
    # Set up the bot reference
    src.main.bot = Mock()
    src.main.bot.user = mock_bot_user
    
    # Track all interactions to verify behavior
    interactions = []
    
    # Mock litellm.completion to capture prompts and return realistic responses
    def mock_completion(model, messages):
        prompt = messages[0]['content']
        interactions.append({
            'prompt': prompt,
            'model': model
        })
        
        # Return different responses based on the prompt content
        if 'Alice' in prompt and 'likes programming' in prompt:
            response_content = "I know Alice is interested in programming!"
        elif 'Bob' in prompt and 'enjoys music' in prompt:
            response_content = "I remember Bob likes music."
        elif 'personality' in prompt.lower() and 'tech expert' in prompt.lower():
            response_content = "I'm a tech expert assistant."
        elif 'server' in prompt.lower() and 'testing' in prompt.lower():
            response_content = "This server is about testing."
        else:
            response_content = "Hello! How can I help you today?"
            
        return {
            'choices': [{
                'message': {
                    'content': response_content
                }
            }]
        }
    
    # Test scenario 1: User mentions bot and introduces themselves
    with patch('src.main.litellm.completion', side_effect=mock_completion):
        with patch('src.main.create_enhanced_emoji_prompt', return_value=""):
            # Alice introduces herself to the bot
            mock_message1 = Mock()
            mock_message1.author = mock_user1
            mock_message1.channel = mock_channel
            mock_message1.content = f"{mock_bot_user.mention} Hi, I'm Alice and I like programming!"
            mock_message1.created_at = "2025-01-01 12:00:00"
            mock_message1.mentions = [mock_bot_user]
            mock_message1.guild = mock_guild
            
            # Process the message
            await src.main.on_message(mock_message1)
            
            # Verify interaction was recorded
            src.main.db_manager.update_user_memory.assert_called()
            
    # Test scenario 2: Another user mentions bot and introduces themselves
    with patch('src.main.litellm.completion', side_effect=mock_completion):
        with patch('src.main.create_enhanced_emoji_prompt', return_value=""):
            # Bob introduces himself to the bot
            mock_message2 = Mock()
            mock_message2.author = mock_user2
            mock_message2.channel = mock_channel
            mock_message2.content = f"{mock_bot_user.mention} Hey there, I'm Bob and I enjoy music!"
            mock_message2.created_at = "2025-01-01 12:05:00"
            mock_message2.mentions = [mock_bot_user]
            mock_message2.guild = mock_guild
            
            # Process the message
            await src.main.on_message(mock_message2)
            
    # Test scenario 3: Alice asks about Bob (context awareness)
    with patch('src.main.litellm.completion', side_effect=mock_completion):
        with patch('src.main.create_enhanced_emoji_prompt', return_value=""):
            # Set up mock to return Bob's memory when requested
            async def context_aware_get_user_memory(user_id):
                if user_id == "111111111":  # Alice
                    return {"known_facts": '{"name": "Alice", "interests": "programming"}', "interaction_history": "[]"}
                elif user_id == "222222222":  # Bob
                    return {"known_facts": '{"name": "Bob", "interests": "music"}', "interaction_history": "[]"}
                else:
                    return {"known_facts": "{}", "interaction_history": "[]"}
            
            # Replace the method temporarily
            original_get_user_memory = src.main.db_manager.get_user_memory
            src.main.db_manager.get_user_memory = context_aware_get_user_memory
            
            # Reset the channel history mock for this interaction
            mock_channel.history = Mock(return_value=AsyncIterator([
                Mock(author=Mock(id=222222222, bot=False)),  # Bob's message
                Mock(author=Mock(id=111111111, bot=False)),  # Alice's message
            ]))
            
            # Alice asks about Bob
            mock_message3 = Mock()
            mock_message3.author = mock_user1
            mock_message3.channel = mock_channel
            mock_message3.content = f"{mock_bot_user.mention} What do you know about Bob?"
            mock_message3.created_at = "2025-01-01 12:10:00"
            mock_message3.mentions = [mock_bot_user]
            mock_message3.guild = mock_guild
            
            # Process the message
            await src.main.on_message(mock_message3)
            
            # Restore the original method
            src.main.db_manager.get_user_memory = original_get_user_memory
            
            # Verify that we captured interactions
            assert len(interactions) > 0
            
    # Test scenario 4: Memory update for another user
    with patch('src.main.litellm.completion', side_effect=mock_completion):
        with patch('src.main.create_enhanced_emoji_prompt', return_value=""):
            # Alice tells the bot something about Bob
            mock_message4 = Mock()
            mock_message4.author = mock_user1
            mock_message4.channel = mock_channel
            mock_message4.content = f"{mock_bot_user.mention} {mock_user2.mention} Bob also likes hiking."
            mock_message4.created_at = "2025-01-01 12:15:00"
            mock_message4.mentions = [mock_bot_user, mock_user2]
            mock_message4.guild = mock_guild
            
            # Mock the fact extraction to return the hiking fact
            src.main.db_manager.extract_targeted_facts = AsyncMock(
                return_value={"hobbies": "hiking"}
            )
            
            # Process the message
            await src.main.on_message(mock_message4)
            
            # Verify that Bob's memory was updated
            # We'll check that the method was called with the right user ID
            calls_made = [call for call in src.main.db_manager.update_user_memory.call_args_list 
                         if call[0][0] == "222222222"]
            assert len(calls_made) > 0, "Bob's memory should have been updated"
    
    # Test scenario 5: Server memory functionality
    with patch('src.main.litellm.completion', side_effect=mock_completion):
        with patch('src.main.create_enhanced_emoji_prompt', return_value=""):
            # Set up server memory
            async def server_memory_with_content(guild_id):
                return {"known_facts": '{"purpose": "testing", "topic": "AI"}'}
            
            # Replace the method temporarily
            original_get_server_memory = src.main.db_manager.get_server_memory
            src.main.db_manager.get_server_memory = server_memory_with_content
            
            # Reset the channel history mock
            mock_channel.history = Mock(return_value=AsyncIterator([]))
            
            # User asks about server
            mock_message5 = Mock()
            mock_message5.author = mock_user1
            mock_message5.channel = mock_channel
            mock_message5.content = f"{mock_bot_user.mention} What is this server about?"
            mock_message5.created_at = "2025-01-01 12:20:00"
            mock_message5.mentions = [mock_bot_user]
            mock_message5.guild = mock_guild
            
            # Clear previous interactions for this test
            prev_interaction_count = len(interactions)
            
            # Process the message
            await src.main.on_message(mock_message5)
            
            # Restore the original method
            src.main.db_manager.get_server_memory = original_get_server_memory
            
            # Verify that a new interaction was captured
            assert len(interactions) > prev_interaction_count, "Should have captured a new interaction"

@pytest.mark.asyncio
async def test_personality_command_integration():
    """Test the personality command integration."""
    # Import the personality cog
    import src.cogs.personality
    
    # Create a mock bot
    mock_bot = Mock()
    mock_bot.db_manager = AsyncMock()
    
    # Set up the server personality in the database
    mock_bot.db_manager.get_server_personality = AsyncMock(return_value="default")
    mock_bot.db_manager.set_server_personality = AsyncMock()
    
    # Create a mock context
    mock_ctx = Mock()
    mock_ctx.guild = Mock()
    mock_ctx.guild.id = 123456789
    mock_ctx.respond = AsyncMock()
    
    # Set up the personality cog
    src.cogs.personality.setup(mock_bot)
    
    # This test verifies that the command is set up correctly
    assert any(call[1].get('name') == 'personality' for call in mock_bot.slash_command.call_args_list)

@pytest.mark.asyncio
async def test_memory_command_integration():
    """Test the memory command integration."""
    # Import the memory cog
    import src.cogs.memory
    
    # Create a mock bot
    mock_bot = Mock()
    mock_bot.db_manager = AsyncMock()
    
    # Set up return values for memory retrieval
    mock_bot.db_manager.get_user_memory = AsyncMock(return_value={
        "known_facts": '{"name": "Alice", "interests": "programming"}'
    })
    mock_bot.db_manager.get_server_memory = AsyncMock(return_value={
        "known_facts": '{"purpose": "testing"}'
    })
    
    # Create a mock context
    mock_ctx = Mock()
    mock_ctx.author = Mock()
    mock_ctx.author.id = "111111111"
    mock_ctx.author.display_name = "Alice"
    mock_ctx.guild = Mock()
    mock_ctx.guild.id = 123456789
    mock_ctx.guild.name = "Test Server"
    mock_ctx.respond = AsyncMock()
    
    # Set up the memory cog
    src.cogs.memory.setup(mock_bot)
    
    # This test verifies that the command is set up correctly
    assert any(call[1].get('name') == 'memory' for call in mock_bot.slash_command.call_args_list)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])