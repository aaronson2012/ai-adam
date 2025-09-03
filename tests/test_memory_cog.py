import sys
import os
import pytest
from unittest.mock import AsyncMock, Mock, patch
import json

# Add the 'src' directory to the Python path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_memory_cog_import():
    """Test that the memory cog can be imported correctly."""
    try:
        import src.cogs.memory
        assert src.cogs.memory is not None
    except ImportError as e:
        pytest.fail(f"Failed to import Memory cog: {e}")

def test_memory_cog_setup():
    """Test that the memory cog setup works correctly."""
    # Create a mock bot
    mock_bot = Mock()
    mock_db_manager = AsyncMock()
    mock_bot.db_manager = mock_db_manager
    
    # Import and set up the memory cog
    import src.cogs.memory
    src.cogs.memory.setup(mock_bot)
    
    # Verify that the slash_command decorator was called
    mock_bot.slash_command.assert_called()
    
    # Get the call arguments to verify the command name
    call_args = mock_bot.slash_command.call_args_list[0][1]  # kwargs from the first call
    assert call_args.get('name') == 'memory'
    assert call_args.get('description') == 'Get or clear memory information about a user'