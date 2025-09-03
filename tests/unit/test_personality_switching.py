"""
Tests for the personality switching functionality in main.py.
"""

import sys
import os
import pytest
from unittest.mock import AsyncMock, Mock, patch

# Add the 'src' directory to the Python path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_personality_switching_functions():
    """Test that the personality switching functions in main.py work correctly."""
    from src.utils.personalities import server_personalities
    
    # Clear the server personalities to ensure a clean state
    server_personalities.clear()
    
    # Test the wrapper functions in main.py would work as expected
    # (This is a simplified test since we can't easily test the async functions without a full bot)
    
    # Test that server_personalities is working as a fallback
    guild_id = "123456789"
    personality_name = "tech_expert"
    
    # Initially should return default
    from src.utils.personalities import get_server_personality
    assert get_server_personality(guild_id) == "default"
    
    # Set a personality using the memory function
    from src.utils.personalities import set_server_personality
    set_server_personality(guild_id, personality_name)
    
    # Should now return the set personality
    assert get_server_personality(guild_id) == personality_name

if __name__ == "__main__":
    pytest.main([__file__, "-v"])