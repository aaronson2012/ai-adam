import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# Add the 'src' directory to the Python path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_emoji_analyzer_real_emoji():
    """Test that the emoji analyzer can analyze a real emoji."""
    try:
        from src.utils.emoji_analyzer import (
            get_custom_emoji_description,
            analyze_server_emojis,
            create_enhanced_emoji_prompt,
            download_emoji_image,
            encode_image_to_base64,
            is_vision_capable_model
        )
        
        # Test that all functions can be imported correctly
        assert get_custom_emoji_description is not None
        assert analyze_server_emojis is not None
        assert create_enhanced_emoji_prompt is not None
        assert download_emoji_image is not None
        assert encode_image_to_base64 is not None
        assert is_vision_capable_model is not None
        
        # Test vision capability detection
        assert is_vision_capable_model("openai/gpt-4-vision-preview") == True
        assert is_vision_capable_model("gemini/gemini-pro-vision") == True
        assert is_vision_capable_model("gpt-4o") == True
        assert is_vision_capable_model("claude-3-opus") == True
        assert is_vision_capable_model("openai/gpt-4") == False
        assert is_vision_capable_model("llama3") == False
        
        print("✅ Emoji analyzer functions imported and working correctly")
        
    except ImportError as e:
        pytest.fail(f"Failed to import emoji analyzer functions: {e}")
    except Exception as e:
        pytest.fail(f"Error testing emoji analyzer: {e}")

def test_emoji_downloader():
    """Test that the emoji downloader can download an image."""
    try:
        from src.utils.emoji_analyzer import download_emoji_image
        
        # Test with a real emoji URL from Wikimedia
        emoji_url = "https://upload.wikimedia.org/wikipedia/commons/e/ef/Emoji_u263a.svg"
        image_bytes = download_emoji_image(emoji_url)
        
        # It might be None if there's a network issue
        # but it shouldn't raise an exception
        assert image_bytes is None or isinstance(image_bytes, bytes)
        
        print("✅ Emoji downloader working correctly")
        
    except Exception as e:
        pytest.fail(f"Error testing emoji downloader: {e}")

def test_emoji_encoder():
    """Test that the emoji encoder can encode an image."""
    try:
        from src.utils.emoji_analyzer import encode_image_to_base64
        
        # Test with some sample bytes
        sample_bytes = b"test image data"
        base64_string = encode_image_to_base64(sample_bytes)
        
        assert isinstance(base64_string, str)
        assert len(base64_string) > 0
        
        print("✅ Emoji encoder working correctly")
        
    except Exception as e:
        pytest.fail(f"Error testing emoji encoder: {e}")

@patch('src.utils.emoji_analyzer.download_emoji_image')
@patch('src.utils.emoji_analyzer.litellm.completion')
@patch('src.utils.emoji_analyzer.get_config')
@pytest.mark.asyncio
async def test_get_custom_emoji_description_with_vision_model(mock_get_config, mock_completion, mock_download):
    """Test getting emoji description with a vision-capable model."""
    try:
        from src.utils.emoji_analyzer import get_custom_emoji_description
        
        # Mock config to return a vision model
        mock_get_config.return_value = {
            'ai': {
                'vision_model': 'openai/gpt-4-vision-preview'
            }
        }
        
        # Mock the download to return some fake image data
        mock_download.return_value = b"fake image data"
        
        # Mock the completion response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "A smiling face emoji"
        mock_completion.return_value = mock_response
        
        # Create a mock emoji
        mock_emoji = Mock()
        mock_emoji.guild.id = 12345
        mock_emoji.name = "smile"
        mock_emoji.url = "http://example.com/emoji.png"
        
        # Create an async mock for the database manager
        mock_db_manager = AsyncMock()
        mock_db_manager.get_emoji_description.return_value = None  # No cached description
        mock_db_manager.save_emoji_description = AsyncMock()
        
        # Test the function
        description = await get_custom_emoji_description(mock_emoji, mock_db_manager)
        
        # Verify the result
        assert description == "A smiling face emoji"
        
        # Verify the mocks were called correctly
        mock_download.assert_called_once_with("http://example.com/emoji.png")
        mock_completion.assert_called_once()
        mock_db_manager.save_emoji_description.assert_called_once_with(
            mock_emoji.guild.id, mock_emoji.name, "A smiling face emoji"
        )
        
        print("✅ Custom emoji description with vision model working correctly")
        
    except Exception as e:
        pytest.fail(f"Error testing custom emoji description with vision model: {e}")

@patch('src.utils.emoji_analyzer.download_emoji_image')
@patch('src.utils.emoji_analyzer.litellm.completion')
@patch('src.utils.emoji_analyzer.get_config')
@pytest.mark.asyncio
async def test_get_custom_emoji_description_with_non_vision_model(mock_get_config, mock_completion, mock_download):
    """Test getting emoji description with a non-vision model."""
    try:
        from src.utils.emoji_analyzer import get_custom_emoji_description
        
        # Mock config to return a non-vision model
        mock_get_config.return_value = {
            'ai': {
                'default_model': 'openai/gpt-4'
            }
        }
        
        # Create a mock emoji
        mock_emoji = Mock()
        mock_emoji.guild.id = 12345
        mock_emoji.name = "smile"
        
        # Create an async mock for the database manager
        mock_db_manager = AsyncMock()
        mock_db_manager.get_emoji_description.return_value = None  # No cached description
        mock_db_manager.save_emoji_description = AsyncMock()
        
        # Test the function
        description = await get_custom_emoji_description(mock_emoji, mock_db_manager)
        
        # Verify the result is a simple text description
        assert description == "Custom server emoji: smile"
        
        # Verify no network calls were made
        mock_download.assert_not_called()
        mock_completion.assert_not_called()
        mock_db_manager.save_emoji_description.assert_called_once_with(
            mock_emoji.guild.id, mock_emoji.name, "Custom server emoji: smile"
        )
        
        print("✅ Custom emoji description with non-vision model working correctly")
        
    except Exception as e:
        pytest.fail(f"Error testing custom emoji description with non-vision model: {e}")

@patch('src.utils.emoji_analyzer.download_emoji_image')
@patch('src.utils.emoji_analyzer.litellm.completion')
@patch('src.utils.emoji_analyzer.get_config')
@pytest.mark.asyncio
async def test_get_custom_emoji_description_download_failure(mock_get_config, mock_completion, mock_download):
    """Test getting emoji description when image download fails."""
    try:
        from src.utils.emoji_analyzer import get_custom_emoji_description
        
        # Mock config to return a vision model
        mock_get_config.return_value = {
            'ai': {
                'vision_model': 'openai/gpt-4-vision-preview'
            }
        }
        
        # Mock the download to fail
        mock_download.return_value = None
        
        # Create a mock emoji
        mock_emoji = Mock()
        mock_emoji.guild.id = 12345
        mock_emoji.name = "smile"
        mock_emoji.url = "http://example.com/emoji.png"
        
        # Create an async mock for the database manager
        mock_db_manager = AsyncMock()
        mock_db_manager.get_emoji_description.return_value = None  # No cached description
        mock_db_manager.save_emoji_description = AsyncMock()
        
        # Test the function
        description = await get_custom_emoji_description(mock_emoji, mock_db_manager)
        
        # Verify the result is a fallback text description
        assert description == "Custom server emoji: smile"
        
        # Verify the download was attempted but no completion call was made
        mock_download.assert_called_once_with("http://example.com/emoji.png")
        mock_completion.assert_not_called()
        mock_db_manager.save_emoji_description.assert_called_once_with(
            mock_emoji.guild.id, mock_emoji.name, "Custom server emoji: smile"
        )
        
        print("✅ Custom emoji description with download failure working correctly")
        
    except Exception as e:
        pytest.fail(f"Error testing custom emoji description with download failure: {e}")

@patch('src.utils.emoji_analyzer.download_emoji_image')
@patch('src.utils.emoji_analyzer.litellm.completion')
@patch('src.utils.emoji_analyzer.get_config')
@pytest.mark.asyncio
async def test_get_custom_emoji_description_api_failure(mock_get_config, mock_completion, mock_download):
    """Test getting emoji description when the API call fails."""
    try:
        from src.utils.emoji_analyzer import get_custom_emoji_description
        
        # Mock config to return a vision model
        mock_get_config.return_value = {
            'ai': {
                'vision_model': 'openai/gpt-4-vision-preview'
            }
        }
        
        # Mock the download to return some fake image data
        mock_download.return_value = b"fake image data"
        
        # Mock the completion to raise an exception
        mock_completion.side_effect = Exception("API error")
        
        # Create a mock emoji
        mock_emoji = Mock()
        mock_emoji.guild.id = 12345
        mock_emoji.name = "smile"
        mock_emoji.url = "http://example.com/emoji.png"
        
        # Create an async mock for the database manager
        mock_db_manager = AsyncMock()
        mock_db_manager.get_emoji_description.return_value = None  # No cached description
        mock_db_manager.save_emoji_description = AsyncMock()
        
        # Test the function
        description = await get_custom_emoji_description(mock_emoji, mock_db_manager)
        
        # Verify the result is a fallback text description
        assert description == "Custom server emoji: smile"
        
        # Verify the mocks were called correctly
        mock_download.assert_called_once_with("http://example.com/emoji.png")
        mock_completion.assert_called_once()
        mock_db_manager.save_emoji_description.assert_called_once_with(
            mock_emoji.guild.id, mock_emoji.name, "Custom server emoji: smile"
        )
        
        print("✅ Custom emoji description with API failure working correctly")
        
    except Exception as e:
        pytest.fail(f"Error testing custom emoji description with API failure: {e}")

@patch('src.utils.emoji_analyzer.get_custom_emoji_description')
@pytest.mark.asyncio
async def test_analyze_server_emojis(mock_get_description):
    """Test analyzing server emojis."""
    try:
        from src.utils.emoji_analyzer import analyze_server_emojis
        
        # Mock the description function
        mock_get_description.return_value = "A smiling face emoji"
        
        # Create a mock guild with emojis
        mock_emoji1 = Mock()
        mock_emoji1.__str__ = Mock(return_value="<:smile:12345>")
        
        mock_emoji2 = Mock()
        mock_emoji2.__str__ = Mock(return_value="<:heart:67890>")
        
        mock_guild = Mock()
        mock_guild.emojis = [mock_emoji1, mock_emoji2]
        mock_guild.id = 99999
        
        # Create an async mock for the database manager
        mock_db_manager = AsyncMock()
        
        # Test the function
        result = await analyze_server_emojis(mock_guild, mock_db_manager)
        
        # Verify the result
        assert len(result) == 2
        assert "<:smile:12345>" in result
        assert "<:heart:67890>" in result
        assert result["<:smile:12345>"] == "A smiling face emoji"
        assert result["<:heart:67890>"] == "A smiling face emoji"
        
        # Verify the mock was called correctly
        assert mock_get_description.call_count == 2
        
        print("✅ Server emoji analysis working correctly")
        
    except Exception as e:
        pytest.fail(f"Error testing server emoji analysis: {e}")

@patch('src.utils.emoji_analyzer.analyze_server_emojis')
@patch('src.utils.emoji_helper.create_emoji_prompt')
@pytest.mark.asyncio
async def test_create_enhanced_emoji_prompt_with_descriptions(mock_create_prompt, mock_analyze_emojis):
    """Test creating enhanced emoji prompt with descriptions."""
    try:
        from src.utils.emoji_analyzer import create_enhanced_emoji_prompt
        
        # Mock the analyze function to return descriptions
        mock_analyze_emojis.return_value = {
            "<:smile:12345>": "A smiling face emoji",
            "<:heart:67890>": "A red heart emoji"
        }
        
        # Create a mock guild
        mock_guild = Mock()
        mock_guild.id = 99999
        
        # Create an async mock for the database manager
        mock_db_manager = AsyncMock()
        
        # Test the function
        result = await create_enhanced_emoji_prompt(mock_guild, mock_db_manager)
        
        # Verify the result contains the descriptions
        assert "Available server emojis with descriptions:" in result
        assert "<:smile:12345>: A smiling face emoji" in result
        assert "<:heart:67890>: A red heart emoji" in result
        assert "Please prioritize using these server emojis liberally and frequently to enhance communication and add personality to your responses" in result
        
        # Verify the fallback wasn't called
        mock_create_prompt.assert_not_called()
        
        print("✅ Enhanced emoji prompt with descriptions working correctly")
        
    except Exception as e:
        pytest.fail(f"Error testing enhanced emoji prompt with descriptions: {e}")

@patch('src.utils.emoji_analyzer.analyze_server_emojis')
@patch('src.utils.emoji_helper.create_emoji_prompt')
@pytest.mark.asyncio
async def test_create_enhanced_emoji_prompt_without_descriptions(mock_create_prompt, mock_analyze_emojis):
    """Test creating enhanced emoji prompt when no descriptions are available."""
    try:
        from src.utils.emoji_analyzer import create_enhanced_emoji_prompt
        
        # Mock the analyze function to return no descriptions
        mock_analyze_emojis.return_value = {}
        
        # Mock the fallback function
        mock_create_prompt.return_value = "\n\nAvailable server emojis: <:smile:12345>, <:heart:67890>\nPlease prioritize using these server emojis when appropriate"
        
        # Create a mock guild
        mock_guild = Mock()
        mock_guild.id = 99999
        
        # Create an async mock for the database manager
        mock_db_manager = AsyncMock()
        
        # Test the function
        result = await create_enhanced_emoji_prompt(mock_guild, mock_db_manager)
        
        # Verify the result is the fallback
        assert result == "\n\nAvailable server emojis: <:smile:12345>, <:heart:67890>\nPlease prioritize using these server emojis when appropriate"
        
        # Verify the fallback was called
        mock_create_prompt.assert_called_once_with(mock_guild)
        
        print("✅ Enhanced emoji prompt without descriptions (fallback) working correctly")
        
    except Exception as e:
        pytest.fail(f"Error testing enhanced emoji prompt without descriptions: {e}")

if __name__ == "__main__":
    test_emoji_analyzer_real_emoji()
    test_emoji_downloader()
    test_emoji_encoder()
    test_get_custom_emoji_description_with_vision_model()
    test_get_custom_emoji_description_with_non_vision_model()
    test_get_custom_emoji_description_download_failure()
    test_get_custom_emoji_description_api_failure()
    test_analyze_server_emojis()
    test_create_enhanced_emoji_prompt_with_descriptions()
    test_create_enhanced_emoji_prompt_without_descriptions()
    print("All emoji analyzer tests passed! 🎉")