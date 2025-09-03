import sys
import os
import unittest
from unittest.mock import Mock, AsyncMock, patch
import discord

# Add the project root directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestReactionIntegration(unittest.TestCase):
    def test_reaction_cog_registration(self):
        """Test that the reaction cog can be imported and registered."""
        # This test ensures that the reaction cog can be imported without errors
        try:
            from src.cogs.reactions import ReactionCog
            cog_class = ReactionCog
            self.assertIsNotNone(cog_class)
        except ImportError as e:
            self.fail(f"Failed to import ReactionCog: {e}")
            
    def test_reaction_cog_setup_function(self):
        """Test that the reaction cog has a setup function."""
        try:
            # Import the module
            import src.cogs.reactions as reactions_module
            # Check that it has a setup function
            self.assertTrue(hasattr(reactions_module, 'setup'))
            self.assertTrue(callable(reactions_module.setup))
        except ImportError as e:
            self.fail(f"Failed to import reactions module: {e}")

if __name__ == '__main__':
    unittest.main()