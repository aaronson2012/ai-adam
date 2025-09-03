import sys
import os
import pytest

# Add the 'src' directory to the Python path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_personality_loading():
    """Test that personalities can be loaded correctly."""
    from src.utils.personalities import get_personality, get_available_personalities, get_personality_prompt, register_personality, create_personality_template
    
    # Test that we can get the default personality
    default_personality = get_personality()
    assert default_personality is not None
    assert "name" in default_personality
    assert "description" in default_personality
    assert "personality_traits" in default_personality
    
    # Test that we get the default personality when requesting a non-existent one
    non_existent_personality = get_personality("non_existent")
    assert non_existent_personality == default_personality
    
    # Test that we can get available personalities
    personalities = get_available_personalities()
    assert "default" in personalities
    
    # Test that we can get personality prompts
    default_prompt = get_personality_prompt("default")
    assert isinstance(default_prompt, str)
    assert len(default_prompt) > 0
    
    # Verify that the default personality has the key characteristics we're looking for
    assert "natural" in default_prompt.lower()
    assert "genuine" in default_prompt.lower()
    assert "guidelines" in default_prompt.lower()
    
    # Test creating a new personality template
    template = create_personality_template("test", "A test personality")
    assert template["name"] == "test"
    assert template["description"] == "A test personality"
    
    # Test registering a new personality
    register_personality("test", template)
    assert "test" in get_available_personalities()
    test_personality = get_personality("test")
    assert test_personality["name"] == "test"

def test_base_guidelines_inclusion():
    """Test that base guidelines are included in all personality prompts."""
    from src.utils.personalities import get_personality_prompt
    
    # Test that base guidelines are in the default personality prompt
    default_prompt = get_personality_prompt("default")
    assert "DO NOT try to act like a human" in default_prompt
    assert "MAY use emojis naturally" in default_prompt
    assert "MAY ask clarifying questions" in default_prompt
    assert "SHOULD prioritize using server-specific emojis" in default_prompt