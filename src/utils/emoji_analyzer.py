# src/utils/emoji_analyzer.py

import base64
import io
import logging
from typing import Dict, List, Optional
import litellm
import discord
import requests
from io import BytesIO
import tomllib

logger = logging.getLogger(__name__)

# Cache for emoji descriptions to avoid repeated processing
emoji_cache = {}

def get_config():
    """Get the configuration from config.toml"""
    try:
        with open("config.toml", "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        logger.warning(f"Could not load config: {e}")
        return {}

def get_vision_model():
    """Get the vision model from config.toml, fallback to default_model if not specified"""
    config = get_config()
    ai_config = config.get('ai', {})
    
    # Try to get vision_model first
    vision_model = ai_config.get('vision_model')
    if vision_model:
        return vision_model
    
    # Fallback to default_model
    return ai_config.get('default_model', 'openai/gpt-4-vision-preview')

def download_emoji_image(url: str) -> Optional[bytes]:
    """
    Download an emoji image from its URL.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.warning(f"Could not download emoji image from {url}: {e}")
        return None

def encode_image_to_base64(image_bytes: bytes) -> str:
    """
    Encode image bytes to base64 string for use in API requests.
    """
    return base64.b64encode(image_bytes).decode('utf-8')

def is_vision_capable_model(model: str) -> bool:
    """
    Check if a model is vision capable based on its name.
    """
    if not model:
        return False
        
    vision_keywords = [
        "vision", 
        "gemini",  # Gemini models are generally vision capable
        "gpt-4o",  # OpenAI's newer models
        "claude-3",  # Anthropic's vision capable models
        "llava",   # LLaVA models
        "bakllava" # BAKLLaVA models
    ]
    
    model_lower = model.lower()
    return any(keyword in model_lower for keyword in vision_keywords)

def get_custom_emoji_description(emoji: discord.Emoji) -> Optional[str]:
    """
    Get a description of a custom server emoji using a multimodal model.
    """
    # Check cache first
    emoji_key = f"{emoji.guild.id}:{emoji.name}"
    if emoji_key in emoji_cache:
        return emoji_cache[emoji_key]
    
    # Get the vision model from config
    model = get_vision_model()
    
    # Check if model supports vision
    if not is_vision_capable_model(model):
        # For non-vision models, return a simple text description
        description = f"Custom server emoji: {emoji.name}"
        emoji_cache[emoji_key] = description
        return description
    
    # For vision models, try to get actual visual description
    try:
        # Download emoji image
        image_bytes = download_emoji_image(str(emoji.url))
        if not image_bytes:
            # Fallback to text description
            description = f"Custom server emoji: {emoji.name}"
            emoji_cache[emoji_key] = description
            return description
        
        # Encode image
        base64_image = encode_image_to_base64(image_bytes)
        
        # Create prompt for vision model
        prompt = f"What is in this custom server emoji? Describe it in one sentence."
        
        # Call vision model
        response = litellm.completion(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        )
        
        description = response.choices[0].message.content
        emoji_cache[emoji_key] = description
        return description
        
    except Exception as e:
        logger.warning(f"Could not get visual description for emoji {emoji.name}: {e}")
        # Fallback to simple text description
        description = f"Custom server emoji: {emoji.name}"
        emoji_cache[emoji_key] = description
        return description

def analyze_server_emojis(guild: discord.Guild) -> Dict[str, str]:
    """
    Analyze all custom emojis in a server and return descriptions.
    """
    if guild is None:
        return {}
    
    emoji_descriptions = {}
    
    try:
        # Get server emojis (custom emojis only)
        emojis = [emoji for emoji in guild.emojis]
        
        # Get descriptions for each emoji
        for emoji in emojis:
            description = get_custom_emoji_description(emoji)
            if description:
                emoji_descriptions[str(emoji)] = description
    except Exception as e:
        logger.error(f"Error analyzing server emojis: {e}")
    
    return emoji_descriptions

def create_enhanced_emoji_prompt(guild: discord.Guild) -> str:
    """
    Create an enhanced emoji prompt with descriptions for better AI understanding.
    """
    emoji_descriptions = analyze_server_emojis(guild)
    
    if not emoji_descriptions:
        # Fall back to the simple emoji prompt
        from src.utils.emoji_helper import create_emoji_prompt
        return create_emoji_prompt(guild)
    
    # Create detailed prompt with emoji descriptions
    prompt_lines = ["\n\nAvailable server emojis with descriptions:"]
    
    for emoji, description in emoji_descriptions.items():
        prompt_lines.append(f"- {emoji}: {description}")
    
    prompt_lines.append("\nPlease prioritize using these server emojis when appropriate, but don't go overboard (maximum 1-2 emojis per message).")
    prompt_lines.append("Use emojis naturally to enhance communication, not replace it.")
    
    return "\n".join(prompt_lines)