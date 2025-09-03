"""
Additional comprehensive tests for the personality system edge cases.
"""

import sys
import os
import pytest
from unittest.mock import AsyncMock, Mock, patch

# Add the 'src' directory to the Python path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_get_personality_with_invalid_name():
    """Test that get_personality returns the default personality when given an invalid name."""
    from src.utils.personalities import get_personality
    
    # Test with invalid personality name
    personality = get_personality("nonexistent_personality")
    
    # Should return the default personality since "nonexistent_personality" doesn't exist
    # but the "default" key does exist
    assert personality is not None
    assert personality['name'] == "Default"  # The actual default personality name

def test_get_personality_prompt_with_default():
    """Test that get_personality_prompt works with default personality."""
    from src.utils.personalities import get_personality_prompt
    
    # Test with default personality
    prompt = get_personality_prompt("default")
    
    # Should return a non-empty string
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "Default" in prompt

def test_get_personality_prompt_with_tech_expert():
    """Test that get_personality_prompt works with tech_expert personality."""
    from src.utils.personalities import get_personality_prompt
    
    # Test with tech_expert personality
    prompt = get_personality_prompt("tech_expert")
    
    # Should return a non-empty string with tech expert characteristics
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "Tech Expert" in prompt
    assert "technology expert" in prompt.lower()

def test_get_available_personalities():
    """Test that get_available_personalities returns expected personalities."""
    from src.utils.personalities import get_available_personalities
    
    # Get available personalities
    personalities = get_available_personalities()
    
    # Should include at least the default personalities
    assert isinstance(personalities, list)
    assert len(personalities) >= 2  # default and tech_expert
    assert "default" in personalities
    assert "tech_expert" in personalities

def test_personality_storage_isolation():
    """Test that personality storage correctly isolates different guilds."""
    from src.utils.personalities import get_server_personality, set_server_personality, server_personalities
    
    # Clear the server personalities to ensure a clean state
    server_personalities.clear()
    
    # Test with two different guilds
    guild_id_1 = 123456789
    guild_id_2 = 987654321
    
    # Both should start with default
    assert get_server_personality(guild_id_1) == "default"
    assert get_server_personality(guild_id_2) == "default"
    
    # Set different personalities for each guild
    set_server_personality(guild_id_1, "tech_expert")
    set_server_personality(guild_id_2, "default")
    
    # Verify they're isolated
    assert get_server_personality(guild_id_1) == "tech_expert"
    assert get_server_personality(guild_id_2) == "default"

def test_personality_case_sensitivity():
    """Test that personality names are handled correctly with case sensitivity."""
    from src.utils.personalities import get_personality
    
    # Test with different case variations
    personality_lower = get_personality("default")
    personality_upper = get_personality("DEFAULT")
    personality_mixed = get_personality("Default")
    
    # The actual "default" personality should have name "Default"
    assert personality_lower['name'] == "Default"
    
    # Since the "default" personality exists, case variations will also return it
    # because the get_personality function first tries the exact key, and if not found,
    # falls back to the "default" key, not the fallback default
    assert personality_upper['name'] == "Default"
    assert personality_mixed['name'] == "Default"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])