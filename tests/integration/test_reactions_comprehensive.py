import sys
import os
import unittest
from unittest.mock import Mock, AsyncMock, patch
import discord
import json

# Add the project root directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.cogs.reactions import ReactionCog

class TestReactionCogComprehensive(unittest.TestCase):
    def setUp(self):
        # Create a mock bot
        self.bot = Mock()
        self.bot.db_manager = AsyncMock()
        self.bot.config = {"ai": {"default_model": "test-model"}}
        
        # Create the cog
        self.cog = ReactionCog(self.bot)
        
    async def test_should_react_to_message_with_none_content(self):
        """Test that should_react_to_message handles None content correctly."""
        # Create a mock message with None content
        message = Mock()
        message.author.bot = False
        message.guild = Mock()
        message.guild.id = 123456789
        message.content = None
        message.id = 987654321
        
        # Mock the database manager methods
        self.bot.db_manager.get_server_personality = AsyncMock(return_value="default")
        
        # This should not raise an exception
        result = await self.cog.should_react_to_message(message)
        self.assertFalse(result)  # Should return False for None content
        
    async def test_should_react_to_message_with_empty_string_content(self):
        """Test that should_react_to_message handles empty string content correctly."""
        # Create a mock message with empty string content
        message = Mock()
        message.author.bot = False
        message.guild = Mock()
        message.guild.id = 123456789
        message.content = ""
        message.id = 987654322
        
        # Mock the database manager methods
        self.bot.db_manager.get_server_personality = AsyncMock(return_value="default")
        
        # This should not raise an exception
        result = await self.cog.should_react_to_message(message)
        self.assertFalse(result)  # Should return False for empty content
        
    async def test_should_react_to_message_with_non_string_content(self):
        """Test that should_react_to_message handles non-string content correctly."""
        # Create a mock message with non-string content
        message = Mock()
        message.author.bot = False
        message.guild = Mock()
        message.guild.id = 123456789
        message.content = 123  # Non-string content
        message.id = 987654323
        
        # Mock the database manager methods
        self.bot.db_manager.get_server_personality = AsyncMock(return_value="default")
        
        # This should not raise an exception
        result = await self.cog.should_react_to_message(message)
        self.assertFalse(result)  # Should return False for non-string content
        
    async def test_get_appropriate_reaction_emojis_with_none_content(self):
        """Test that get_appropriate_reaction_emojis handles None content correctly."""
        # Create a mock message with None content
        message = Mock()
        message.author.bot = False
        message.guild = Mock()
        message.guild.id = 123456789
        message.content = None
        message.id = 987654324
        
        # Mock the database manager methods
        self.bot.db_manager.get_server_personality = AsyncMock(return_value="default")
        message.guild.emojis = []
        
        # This should not raise an exception
        result = await self.cog.get_appropriate_reaction_emojis(message)
        self.assertEqual(result, ["👍"])  # Should return fallback reaction
        
    async def test_get_appropriate_reaction_emojis_with_empty_string_content(self):
        """Test that get_appropriate_reaction_emojis handles empty string content correctly."""
        # Create a mock message with empty string content
        message = Mock()
        message.author.bot = False
        message.guild = Mock()
        message.guild.id = 123456789
        message.content = ""
        message.id = 987654325
        
        # Mock the database manager methods
        self.bot.db_manager.get_server_personality = AsyncMock(return_value="default")
        message.guild.emojis = []
        
        # This should not raise an exception
        result = await self.cog.get_appropriate_reaction_emojis(message)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)  # Should return some reactions
        
    async def test_get_relevant_context_with_none_content_in_history(self):
        """Test that get_relevant_context handles None content in message history correctly."""
        # Create a mock message
        message = Mock()
        message.author.bot = False
        message.guild = Mock()
        message.guild.id = 123456789
        message.content = "Test message"
        message.id = 987654326
        message.channel.history = AsyncMock(return_value=[
            Mock(author=Mock(bot=False, display_name="User1"), content=None),
            Mock(author=Mock(bot=False, display_name="User2"), content="Hello"),
        ])
        
        # Mock the database manager methods
        self.bot.db_manager.get_user_memory = AsyncMock(return_value={"known_facts": "{}", "interaction_history": "[]"})
        self.bot.db_manager.get_server_personality = AsyncMock(return_value="default")
        
        # This should not raise an exception
        result = await self.cog.get_relevant_context(message)
        self.assertIsInstance(result, str)  # Should return a string context

if __name__ == '__main__':
    # Run the async tests
    unittest.main()