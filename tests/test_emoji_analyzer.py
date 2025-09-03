import sys
import os
import pytest
from unittest.mock import Mock, patch

# Add the 'src' directory to the Python path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_emoji_analyzer_import():
    """Test that the emoji analyzer can be imported correctly."""
    try:
        from src.utils.emoji_analyzer import (
            get_config,
            get_vision_model,
            download_emoji_image,
            encode_image_to_base64,
            is_vision_capable_model,
            get_custom_emoji_description,
            analyze_server_emojis,
            create_enhanced_emoji_prompt
        )
        assert get_config is not None
        assert get_vision_model is not None
        assert download_emoji_image is not None
        assert encode_image_to_base64 is not None
        assert is_vision_capable_model is not None
        assert get_custom_emoji_description is not None
        assert analyze_server_emojis is not None
        assert create_enhanced_emoji_prompt is not None
    except ImportError as e:
        pytest.fail(f"Failed to import emoji analyzer: {e}")

def test_download_emoji_image():
    """Test downloading emoji image."""
    from src.utils.emoji_analyzer import download_emoji_image
    
    # Test with None URL
    result = download_emoji_image(None)
    assert result is None

def test_encode_image_to_base64():
    """Test encoding image to base64."""
    from src.utils.emoji_analyzer import encode_image_to_base64
    
    # Test with some sample bytes
    sample_bytes = b"test image data"
    result = encode_image_to_base64(sample_bytes)
    assert isinstance(result, str)
    assert len(result) > 0

def test_is_vision_capable_model():
    """Test checking if a model is vision capable."""
    from src.utils.emoji_analyzer import is_vision_capable_model
    
    # Test with vision capable models
    assert is_vision_capable_model("openai/gpt-4-vision-preview") == True
    assert is_vision_capable_model("gemini/gemini-pro-vision") == True
    assert is_vision_capable_model("gpt-4o") == True
    assert is_vision_capable_model("claude-3-opus") == True
    
    # Test with non-vision capable models
    assert is_vision_capable_model("openai/gpt-4") == False
    assert is_vision_capable_model("gemini/gemini-pro") == True  # Gemini models are generally vision capable
    assert is_vision_capable_model("llama3") == False
    
    # Test with None
    assert is_vision_capable_model(None) == False
    
    # Test with empty string
    assert is_vision_capable_model("") == False

@patch('src.utils.emoji_analyzer.litellm.completion')
@patch('src.utils.emoji_analyzer.download_emoji_image')
@patch('src.utils.emoji_analyzer.is_vision_capable_model')
def test_get_custom_emoji_description_vision_model(mock_is_vision_capable, mock_download_emoji_image, mock_completion):
    """Test getting custom emoji description with vision model."""
    from src.utils.emoji_analyzer import get_custom_emoji_description
    
    # Clear the cache to avoid interference from other tests
    from src.utils.emoji_analyzer import emoji_cache
    emoji_cache.clear()
    
    # Create a mock emoji
    mock_emoji = Mock()
    mock_emoji.guild.id = 123456789
    mock_emoji.name = "test_emoji"
    mock_emoji.url = "https://cdn.discordapp.com/emojis/test.png"
    
    # Mock the functions
    mock_is_vision_capable.return_value = True
    mock_download_emoji_image.return_value = b"fake image data"
    mock_completion.return_value.choices = [
        Mock(message=Mock(content="This is a test emoji showing a smiley face"))
    ]
    
    # Test with a custom emoji
    result = get_custom_emoji_description(mock_emoji)
    assert isinstance(result, str)
    assert len(result) > 0

@patch('src.utils.emoji_analyzer.is_vision_capable_model')
def test_get_custom_emoji_description_non_vision_model(mock_is_vision_capable):
    """Test getting custom emoji description with non-vision model."""
    from src.utils.emoji_analyzer import get_custom_emoji_description
    
    # Clear the cache to avoid interference from other tests
    from src.utils.emoji_analyzer import emoji_cache
    emoji_cache.clear()
    
    # Create a mock emoji
    mock_emoji = Mock()
    mock_emoji.guild.id = 123456789
    mock_emoji.name = "test_emoji"
    
    # Mock the function to return False
    mock_is_vision_capable.return_value = False
    
    # Test with a custom emoji
    result = get_custom_emoji_description(mock_emoji)
    assert result == "Custom server emoji: test_emoji"

def test_analyze_server_emojis():
    """Test analyzing server emojis."""
    from src.utils.emoji_analyzer import analyze_server_emojis
    
    # Test with None guild
    result = analyze_server_emojis(None)
    assert result == {}

def test_create_enhanced_emoji_prompt():
    """Test creating enhanced emoji prompt."""
    from src.utils.emoji_analyzer import create_enhanced_emoji_prompt
    
    # Test with None guild
    result = create_enhanced_emoji_prompt(None)
    # Should fall back to the simple emoji prompt
    assert isinstance(result, str)