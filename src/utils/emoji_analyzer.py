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

# Import database manager
from src.database.manager import DatabaseManager

logger = logging.getLogger(__name__)

def get_config():
    """Get the configuration from config.toml"""
    logger.debug("Loading configuration from config.toml")
    try:
        with open("config.toml", "rb") as f:
            config = tomllib.load(f)
        logger.debug("Configuration loaded successfully")
        return config
    except Exception as e:
        logger.warning(f"Could not load config: {e}")
        return {}

def get_vision_model():
    """Get the vision model from config.toml, fallback to default_model if not specified"""
    logger.debug("Getting vision model from configuration")
    config = get_config()
    ai_config = config.get('ai', {})
    
    # Try to get vision_model first
    vision_model = ai_config.get('vision_model')
    if vision_model:
        logger.debug(f"Using vision model from config: {vision_model}")
        return vision_model
    
    # Fallback to default_model
    default_model = ai_config.get('default_model', 'openai/gpt-4-vision-preview')
    logger.debug(f"Using default model as fallback: {default_model}")
    return default_model

def download_emoji_image(url: str) -> Optional[bytes]:
    """
    Download an emoji image from its URL.
    """
    logger.debug(f"Downloading emoji image from URL: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        logger.debug(f"Successfully downloaded emoji image, size: {len(response.content)} bytes")
        return response.content
    except Exception as e:
        logger.warning(f"Could not download emoji image from {url}: {e}")
        return None

def encode_image_to_base64(image_bytes: bytes) -> str:
    """
    Encode image bytes to base64 string for use in API requests.
    """
    logger.debug(f"Encoding image to base64, size: {len(image_bytes)} bytes")
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    logger.debug(f"Encoded image to base64, length: {len(encoded)} characters")
    return encoded

def is_vision_capable_model(model: str) -> bool:
    """
    Check if a model is vision capable based on its name.
    """
    logger.debug(f"Checking if model is vision capable: {model}")
    if not model:
        logger.debug("Model is None or empty, not vision capable")
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
    is_vision = any(keyword in model_lower for keyword in vision_keywords)
    logger.debug(f"Model vision capability: {is_vision}")
    return is_vision

async def get_custom_emoji_description(emoji: discord.Emoji, db_manager: DatabaseManager) -> Optional[str]:
    """
    Get a description of a custom server emoji using a multimodal model.
    Uses database caching to avoid repeated processing.
    """
    logger.debug(f"Getting description for custom emoji: {emoji.name} (ID: {emoji.id}) in guild: {emoji.guild.name} (ID: {emoji.guild.id})")
    
    # Check database cache first
    logger.debug(f"Checking database cache for emoji {emoji.name}")
    cached_description = await db_manager.get_emoji_description(emoji.guild.id, emoji.name)
    if cached_description:
        logger.debug(f"Using cached description for emoji {emoji.name}: {cached_description}")
        return cached_description
    
    # Get the vision model from config
    logger.debug("Getting vision model from configuration")
    model = get_vision_model()
    logger.debug(f"Using vision model: {model}")
    
    # Check if model supports vision
    logger.debug("Checking if model is vision capable")
    if not is_vision_capable_model(model):
        logger.debug("Model is not vision capable, using text description")
        # For non-vision models, return a simple text description
        description = f"Custom server emoji: {emoji.name}"
        logger.debug(f"Saving text description for emoji {emoji.name}: {description}")
        await db_manager.save_emoji_description(emoji.guild.id, emoji.name, description)
        return description
    
    # For vision models, try to get actual visual description
    logger.debug("Model is vision capable, attempting visual description")
    try:
        # Download emoji image
        logger.debug(f"Downloading emoji image from URL: {emoji.url}")
        image_bytes = download_emoji_image(str(emoji.url))
        if not image_bytes:
            logger.warning(f"Could not download emoji image for {emoji.name}, using text description")
            # Fallback to text description
            description = f"Custom server emoji: {emoji.name}"
            await db_manager.save_emoji_description(emoji.guild.id, emoji.name, description)
            return description
        
        # Encode image
        logger.debug("Encoding image to base64")
        base64_image = encode_image_to_base64(image_bytes)
        
        # Create prompt for vision model
        prompt = f"What is in this custom server emoji? Describe it in one sentence."
        logger.debug(f"Vision model prompt: {prompt}")
        
        # Call vision model
        logger.debug("Calling vision model for emoji description")
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
        logger.debug(f"Vision model response: {description}")
        await db_manager.save_emoji_description(emoji.guild.id, emoji.name, description)
        logger.debug(f"Saved visual description for emoji {emoji.name}")
        return description
        
    except Exception as e:
        logger.warning(f"Could not get visual description for emoji {emoji.name}: {e}")
        # Fallback to simple text description
        description = f"Custom server emoji: {emoji.name}"
        await db_manager.save_emoji_description(emoji.guild.id, emoji.name, description)
        logger.debug(f"Saved fallback text description for emoji {emoji.name}")
        return description

async def analyze_server_emojis(guild: discord.Guild, db_manager: DatabaseManager) -> Dict[str, str]:
    """
    Analyze all custom emojis in a server and return descriptions.
    """
    logger.debug(f"Analyzing server emojis for guild: {guild.name if guild else 'None'} (ID: {guild.id if guild else 'None'})")
    if guild is None:
        logger.debug("Guild is None, returning empty emoji descriptions")
        return {}
    
    emoji_descriptions = {}
    
    try:
        # Get server emojis (custom emojis only)
        emojis = [emoji for emoji in guild.emojis]
        logger.debug(f"Found {len(emojis)} custom emojis in guild")
        
        # Get descriptions for each emoji
        for emoji in emojis:
            logger.debug(f"Processing emoji: {emoji.name}")
            description = await get_custom_emoji_description(emoji, db_manager)
            if description:
                emoji_descriptions[str(emoji)] = description
                logger.debug(f"Added description for emoji {emoji.name}")
            else:
                logger.debug(f"No description returned for emoji {emoji.name}")
    except Exception as e:
        logger.error(f"Error analyzing server emojis: {e}")
    
    logger.debug(f"Returning {len(emoji_descriptions)} emoji descriptions")
    return emoji_descriptions

async def create_enhanced_emoji_prompt(guild: discord.Guild, db_manager: DatabaseManager) -> str:
    """
    Create an enhanced emoji prompt with descriptions for better AI understanding.
    """
    logger.debug(f"Creating enhanced emoji prompt for guild: {guild.name if guild else 'None'} (ID: {guild.id if guild else 'None'})")
    emoji_descriptions = await analyze_server_emojis(guild, db_manager)
    logger.debug(f"Retrieved {len(emoji_descriptions)} emoji descriptions")
    
    if not emoji_descriptions:
        logger.debug("No emoji descriptions found, falling back to simple emoji prompt")
        # Fall back to the simple emoji prompt
        from src.utils.emoji_helper import create_emoji_prompt
        simple_prompt = create_emoji_prompt(guild)
        logger.debug(f"Simple emoji prompt: {simple_prompt}")
        return simple_prompt
    
    # Create detailed prompt with emoji descriptions
    logger.debug("Creating detailed prompt with emoji descriptions")
    prompt_lines = ["\n\nAvailable server emojis with descriptions:"]
    
    # Convert Discord emoji format to curly brace format for AI consumption
    for emoji_key, description in emoji_descriptions.items():
        # Extract emoji name from Discord format <:emoji_name:123456789>
        if emoji_key.startswith("<:") and ":" in emoji_key:
            # Extract the emoji name (between the first and last colon)
            emoji_name = emoji_key.split(":")[1]
            # Format for AI consumption using curly braces
            prompt_lines.append(f"- {{{emoji_name}}}: {description}")
            logger.debug(f"Added emoji description: {{{emoji_name}}}: {description}")
        else:
            # If it's already in the right format or is a Unicode emoji, use as-is
            prompt_lines.append(f"- {emoji_key}: {description}")
            logger.debug(f"Added emoji description: {emoji_key}: {description}")
    
    prompt_lines.append("\nPlease prioritize using these server emojis liberally and frequently to enhance communication and add personality to your responses.")
    prompt_lines.append("Use multiple emojis in a single message when appropriate to express emotions or reactions.")
    prompt_lines.append("Use emojis to 'spice things up' and make conversations more engaging.")
    prompt_lines.append("Remember to use the curly brace format {emoji_name} for custom server emojis.")
    prompt_lines.append("Do NOT use the Discord emoji format like <:emoji_name:123456789>.")
    
    prompt = "\n".join(prompt_lines)
    logger.debug(f"Enhanced emoji prompt created (first 200 chars): {prompt[:200]}...")
    return prompt