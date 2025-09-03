import sys
import os
import pytest
from unittest.mock import Mock, AsyncMock

# Add the 'src' directory to the Python path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_emoji_manager_import():
    """Test that the emoji manager can be imported correctly."""
    try:
        from src.utils.emoji_manager import EmojiManager
        assert EmojiManager is not None
    except ImportError as e:
        pytest.fail(f"Failed to import emoji manager: {e}")

def test_emoji_caching_flag():
    """Test that the emoji caching flag works correctly."""
    from src.utils.emoji_manager import EmojiManager
    
    # Create a mock database manager
    mock_db_manager = Mock()
    
    # Create an emoji manager instance
    emoji_manager = EmojiManager(mock_db_manager)
    
    # Initially, caching should not be in progress
    assert emoji_manager.is_caching_in_progress() == False
    
    # Set the flag to True
    emoji_manager.is_caching = True
    
    # Now caching should be in progress
    assert emoji_manager.is_caching_in_progress() == True
    
    # Set the flag back to False
    emoji_manager.is_caching = False
    
    # Now caching should not be in progress
    assert emoji_manager.is_caching_in_progress() == False