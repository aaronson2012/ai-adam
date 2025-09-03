import sys
import os
import unittest
from unittest.mock import Mock, AsyncMock, patch
import discord
import json

# Add the project root directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.cogs.reactions import ReactionCog

class TestReactionCog(unittest.TestCase):
    def setUp(self):
        # Create a mock bot
        self.bot = Mock()
        self.bot.db_manager = AsyncMock()
        
        # Create the cog
        self.cog = ReactionCog(self.bot)
        
    def test_init(self):
        """Test that the cog initializes correctly."""
        self.assertEqual(self.cog.bot, self.bot)
        self.assertEqual(self.cog.db_manager, self.bot.db_manager)
        self.assertEqual(self.cog.max_recent_messages, 50)
        
    async def test_get_recently_reacted(self):
        """Test getting recently reacted messages."""
        guild_id = 123456789
        
        # Initially should be an empty set
        recently_reacted = await self.cog.get_recently_reacted(guild_id)
        self.assertIsInstance(recently_reacted, set)
        self.assertEqual(len(recently_reacted), 0)
        
    async def test_add_recently_reacted(self):
        """Test adding a message to recently reacted."""
        guild_id = 123456789
        message_id = 987654321
        
        # Add a message ID
        await self.cog.add_recently_reacted(guild_id, message_id)
        
        # Check that it's now in the set
        recently_reacted = await self.cog.get_recently_reacted(guild_id)
        self.assertIn(message_id, recently_reacted)
        
    async def test_is_recently_reacted(self):
        """Test checking if a message has been recently reacted to."""
        guild_id = 123456789
        message_id = 987654321
        other_message_id = 111111111
        
        # Initially should be False
        is_recent = await self.cog.is_recently_reacted(guild_id, message_id)
        self.assertFalse(is_recent)
        
        # Add to recently reacted
        await self.cog.add_recently_reacted(guild_id, message_id)
        
        # Should now be True for that message
        is_recent = await self.cog.is_recently_reacted(guild_id, message_id)
        self.assertTrue(is_recent)
        
        # Should still be False for other messages
        is_recent = await self.cog.is_recently_reacted(guild_id, other_message_id)
        self.assertFalse(is_recent)

if __name__ == '__main__':
    # Run the async tests
    unittest.main()