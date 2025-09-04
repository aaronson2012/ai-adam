import pytest
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.cogs.reactions import ReactionCog

class TestLLMEmojiSelection:
    """Test that emoji selection is properly handled by the LLM"""

    @pytest.fixture
    def bot(self):
        """Create a mock bot"""
        mock_bot = MagicMock()
        mock_bot.config = {'ai': {'default_model': 'test-model'}}
        return mock_bot

    @pytest.fixture
    def reaction_cog(self, bot):
        """Create a ReactionCog instance"""
        return ReactionCog(bot)

    @pytest.mark.asyncio
    async def test_explicit_emoji_request_uses_llm(self, reaction_cog):
        """Test that explicit emoji requests are handled by the LLM, not pattern matching"""
        # Create a mock message with an explicit emoji request
        mock_message = MagicMock()
        mock_message.content = "please react to this with a construction worker emoji"
        mock_message.guild = MagicMock()
        mock_message.guild.emojis = []
        mock_message.author = MagicMock()
        mock_message.author.bot = False

        # Mock the LLM response
        with patch('litellm.completion') as mock_completion:
            # Mock should_react_to_message to return True
            with patch.object(reaction_cog, 'should_react_to_message', return_value=True):
                # Mock get_relevant_context to return empty string
                with patch.object(reaction_cog, 'get_relevant_context', return_value=""):
                    # Mock the LLM response for emoji selection
                    mock_completion.return_value = {
                        'choices': [{
                            'message': {
                                'content': '["👷"]'
                            }
                        }]
                    }
                    
                    # Call the method
                    reactions = await reaction_cog.get_appropriate_reaction_emojis(mock_message)
                    
                    # Verify that the LLM was called
                    assert mock_completion.called
                    
                    # Verify that we got the expected emoji (construction worker)
                    assert reactions == ["👷"]

    @pytest.mark.asyncio
    async def test_emoji_selection_fallback(self, reaction_cog):
        """Test that emoji selection falls back properly when LLM fails"""
        # Create a mock message
        mock_message = MagicMock()
        mock_message.content = "please react to this with a construction worker emoji"
        mock_message.guild = MagicMock()
        mock_message.guild.emojis = []
        mock_message.author = MagicMock()
        mock_message.author.bot = False

        # Mock the LLM to fail
        with patch('litellm.completion', side_effect=Exception("LLM Error")):
            # Mock should_react_to_message to return True
            with patch.object(reaction_cog, 'should_react_to_message', return_value=True):
                # Call the method
                reactions = await reaction_cog.get_appropriate_reaction_emojis(mock_message)
                
                # Verify that we got the fallback emoji
                assert reactions == ["👍"]