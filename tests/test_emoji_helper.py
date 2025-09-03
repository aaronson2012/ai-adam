import sys
import os
import pytest
from unittest.mock import Mock

# Add the 'src' directory to the Python path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_emoji_helper_import():
    """Test that the emoji helper can be imported correctly."""
    try:
        from src.utils.emoji_helper import get_server_emojis, get_random_emojis, create_emoji_prompt
        assert get_server_emojis is not None
        assert get_random_emojis is not None
        assert create_emoji_prompt is not None
    except ImportError as e:
        pytest.fail(f"Failed to import emoji helper: {e}")

def test_get_server_emojis():
    """Test getting server emojis."""
    from src.utils.emoji_helper import get_server_emojis
    
    # Test with None guild
    assert get_server_emojis(None) == []
    
    # Test with mock guild that has no emojis
    mock_guild = Mock()
    mock_guild.emojis = []
    assert get_server_emojis(mock_guild) == []
    
    # Test with mock guild that has emojis
    mock_emoji1 = Mock()
    mock_emoji1.name = "test1"
    mock_emoji2 = Mock()
    mock_emoji2.name = "test2"
    
    mock_guild.emojis = [mock_emoji1, mock_emoji2]
    result = get_server_emojis(mock_guild)
    assert ":test1:" in result
    assert ":test2:" in result

def test_get_random_emojis():
    """Test getting random emojis."""
    from src.utils.emoji_helper import get_random_emojis
    
    # Test with None guild
    assert get_random_emojis(None) == []
    
    # Test with mock guild that has no emojis
    mock_guild = Mock()
    mock_guild.emojis = []
    assert get_random_emojis(mock_guild) == []
    
    # Test with mock guild that has emojis
    mock_emoji1 = Mock()
    mock_emoji1.name = "test1"
    mock_emoji2 = Mock()
    mock_emoji2.name = "test2"
    mock_emoji3 = Mock()
    mock_emoji3.name = "test3"
    
    mock_guild.emojis = [mock_emoji1, mock_emoji2, mock_emoji3]
    result = get_random_emojis(mock_guild, 2)
    assert len(result) == 2
    # All results should be from the available emojis
    for emoji in result:
        assert emoji in [":test1:", ":test2:", ":test3:"]

def test_create_emoji_prompt():
    """Test creating emoji prompt."""
    from src.utils.emoji_helper import create_emoji_prompt
    
    # Test with None guild
    assert create_emoji_prompt(None) == ""
    
    # Test with mock guild that has no emojis
    mock_guild = Mock()
    mock_guild.emojis = []
    assert create_emoji_prompt(mock_guild) == ""
    
    # Test with mock guild that has emojis
    mock_emoji1 = Mock()
    mock_emoji1.name = "test1"
    mock_emoji2 = Mock()
    mock_emoji2.name = "test2"
    
    mock_guild.emojis = [mock_emoji1, mock_emoji2]
    result = create_emoji_prompt(mock_guild)
    assert "Available server emojis:" in result
    assert ":test1:" in result
    assert ":test2:" in result
    assert "prioritize using these server emojis" in result