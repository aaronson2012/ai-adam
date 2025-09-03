import sys
import os
import pytest
from unittest.mock import AsyncMock, Mock, patch

# Add the 'src' directory to the Python path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_personality_cog_import():
    """Test that the personality cog can be imported correctly."""
    try:
        import src.cogs.personality
        from src.utils.personalities import server_personalities, get_server_personality, set_server_personality
        assert server_personalities is not None
    except ImportError as e:
        pytest.fail(f"Failed to import Personality cog: {e}")

def test_personality_cog_methods():
    """Test that the personality cog methods work correctly."""
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