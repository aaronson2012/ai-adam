# src/utils/emoji_formatter.py

import discord
import re
import logging
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

def format_emojis_for_discord(text: str, guild: discord.Guild) -> str:
    """
    Ensure all emojis in the text are properly formatted for Discord.
    Custom emojis should be enclosed in curly braces like {emoji_name}.
    Standard Unicode emojis should be left as-is.
    
    Args:
        text (str): Text to format
        guild (discord.Guild): Guild to validate custom emojis against
        
    Returns:
        str: Text with properly formatted emojis
    """
    logger.debug(f"Formatting emojis in text: {text[:100]}...")
    
    # First, let's identify all potential emoji patterns in the text
    # This includes:
    # 1. Already properly formatted emojis in curly braces: {emoji_name}
    # 2. Custom emojis in Discord format: <:emoji_name:123456789>
    # 3. Potential emoji names that might be custom emojis
    
    # Pattern to match Discord custom emoji format: <:emoji_name:123456789>
    discord_emoji_pattern = r'<:(\w+):\d+>'
    
    def replace_discord_emoji(match):
        emoji_name = match.group(1)
        logger.debug(f"Found Discord emoji format, converting to curly brace format: {emoji_name}")
        # Check if this is a valid custom emoji in the guild
        emoji_obj = discord.utils.get(guild.emojis, name=emoji_name)
        if emoji_obj:
            # Valid custom emoji, convert to curly brace format
            return f"{{{emoji_name}}}"
        else:
            # Not a valid custom emoji, leave as-is
            return match.group(0)
    
    # Replace Discord emoji format with curly brace format
    result = re.sub(discord_emoji_pattern, replace_discord_emoji, text)
    logger.debug(f"Text after Discord emoji conversion: {result[:100]}...")
    
    # Pattern to match potential emoji names that might be custom emojis
    # This is a bit tricky as we don't want to match every word
    # We'll look for words that are likely to be emoji names based on common patterns
    # Emoji names typically contain only alphanumeric characters and underscores
    potential_emoji_pattern = r'\b([a-zA-Z][a-zA-Z0-9_]{1,29})\b'
    
    def replace_potential_emoji(match):
        potential_name = match.group(1)
        logger.debug(f"Checking potential emoji name: {potential_name}")
        
        # Skip common words that are unlikely to be emoji names
        common_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'man', 'men', 'put', 'too', 'use', 'any', 'big', 'end', 'far', 'got', 'hot', 'let', 'lot', 'run', 'sat', 'say', 'she', 'sit', 'try', 'up', 'way', 'win', 'yes'
        }
        
        if potential_name.lower() in common_words:
            logger.debug(f"Skipping common word: {potential_name}")
            return match.group(0)
        
        # Check if this is a valid custom emoji in the guild
        emoji_obj = discord.utils.get(guild.emojis, name=potential_name)
        if emoji_obj:
            logger.debug(f"Found valid custom emoji, converting to curly brace format: {potential_name}")
            # Valid custom emoji, ensure it's in curly brace format
            # But only if it's not already in curly braces (which we handled earlier)
            return f"{{{potential_name}}}"
        else:
            # Not a valid custom emoji, leave as-is
            logger.debug(f"Not a valid custom emoji: {potential_name}")
            return match.group(0)
    
    # Apply this replacement only to text that's not already in curly braces
    # We'll use a more complex approach to avoid matching text inside curly braces
    def process_text_outside_braces(text):
        # Split text by curly braces to process only outside parts
        parts = re.split(r'(\{[^}]+\})', text)
        for i, part in enumerate(parts):
            # Only process parts that are not curly brace expressions
            if not (part.startswith('{') and part.endswith('}')):
                parts[i] = re.sub(potential_emoji_pattern, replace_potential_emoji, part)
        return ''.join(parts)
    
    result = process_text_outside_braces(result)
    logger.debug(f"Text after potential emoji conversion: {result[:100]}...")
    
    return result

def validate_emoji_formatting(text: str) -> bool:
    """
    Validate that emojis in the text are properly formatted.
    
    Args:
        text (str): Text to validate
        
    Returns:
        bool: True if formatting is valid, False otherwise
    """
    logger.debug(f"Validating emoji formatting in text: {text[:100]}...")
    
    # Check for any Discord emoji format that should be converted
    discord_emoji_pattern = r'<:(\w+):\d+>'
    if re.search(discord_emoji_pattern, text):
        logger.debug("Found unconverted Discord emoji format")
        return False
    
    # Check for any other invalid emoji formats
    # This is a simple check - in practice, you might want more comprehensive validation
    
    logger.debug("Emoji formatting is valid")
    return True