# src/utils/emoji_parser.py

import discord
import re
import logging
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

def extract_emoji_tags(text: str) -> List[str]:
    """
    Extract all emoji tags from text that are enclosed in curly braces.
    
    Args:
        text (str): Text to search for emoji tags
        
    Returns:
        List[str]: List of emoji names found in curly braces
    """
    logger.debug(f"Extracting emoji tags from text: {text[:100]}...")
    # Find all patterns like {emoji_name}
    pattern = r'\{([^{}]+)\}'
    matches = re.findall(pattern, text)
    logger.debug(f"Found {len(matches)} emoji tags: {matches}")
    return matches

def validate_emoji_tag(emoji_name: str, guild: discord.Guild) -> bool:
    """
    Validate if an emoji name exists in the guild.
    
    Args:
        emoji_name (str): Name of the emoji to validate
        guild (discord.Guild): Guild to check for emoji
        
    Returns:
        bool: True if emoji exists, False otherwise
    """
    logger.debug(f"Validating emoji tag: {emoji_name}")
    
    # Check if it's a standard Unicode emoji (we'll assume all Unicode emojis are valid)
    # This is a simplified check - in practice, you might want a more comprehensive list
    if len(emoji_name) <= 2 and any(ord(char) > 127 for char in emoji_name):
        logger.debug(f"Emoji {emoji_name} is a Unicode emoji, considered valid")
        return True
    
    # Check custom emojis in the guild
    emoji_obj = discord.utils.get(guild.emojis, name=emoji_name)
    is_valid = emoji_obj is not None
    logger.debug(f"Emoji {emoji_name} validity: {is_valid}")
    return is_valid

def convert_emoji_tag_to_discord_emoji(emoji_name: str, guild: discord.Guild) -> Optional[str]:
    """
    Convert an emoji name to its Discord representation.
    
    Args:
        emoji_name (str): Name of the emoji
        guild (discord.Guild): Guild to look for custom emojis
        
    Returns:
        Optional[str]: Discord emoji representation or None if not found
    """
    logger.debug(f"Converting emoji tag to Discord emoji: {emoji_name}")
    
    # Check if it's already a Unicode emoji
    if len(emoji_name) <= 2 and any(ord(char) > 127 for char in emoji_name):
        logger.debug(f"Emoji {emoji_name} is a Unicode emoji")
        return emoji_name
    
    # Check custom emojis in the guild
    emoji_obj = discord.utils.get(guild.emojis, name=emoji_name)
    if emoji_obj:
        discord_emoji = str(emoji_obj)
        logger.debug(f"Found custom emoji {emoji_name}: {discord_emoji}")
        return discord_emoji
    
    logger.debug(f"Emoji {emoji_name} not found in guild")
    return None

def replace_emoji_tags(text: str, guild: discord.Guild) -> str:
    """
    Replace all emoji tags in text with actual Discord emojis.
    
    Args:
        text (str): Text containing emoji tags
        guild (discord.Guild): Guild to look for custom emojis
        
    Returns:
        str: Text with emoji tags replaced by Discord emojis
    """
    logger.debug(f"Replacing emoji tags in text: {text[:100]}...")
    
    def replace_match(match):
        emoji_name = match.group(1)
        logger.debug(f"Processing emoji tag: {emoji_name}")
        discord_emoji = convert_emoji_tag_to_discord_emoji(emoji_name, guild)
        if discord_emoji:
            logger.debug(f"Replacing {emoji_name} with {discord_emoji}")
            return discord_emoji
        else:
            # If emoji not found, keep the original tag
            logger.debug(f"Emoji {emoji_name} not found, keeping original tag")
            return match.group(0)
    
    # Replace all patterns like {emoji_name} with actual emojis
    pattern = r'\{([^{}]+)\}'
    result = re.sub(pattern, replace_match, text)
    logger.debug(f"Text after emoji replacement: {result[:100]}...")
    return result

def find_invalid_emoji_tags(text: str, guild: discord.Guild) -> List[str]:
    """
    Find all invalid emoji tags in text.
    
    Args:
        text (str): Text containing emoji tags
        guild (discord.Guild): Guild to validate emojis against
        
    Returns:
        List[str]: List of invalid emoji names
    """
    logger.debug(f"Finding invalid emoji tags in text: {text[:100]}...")
    emoji_tags = extract_emoji_tags(text)
    invalid_tags = []
    
    for emoji_name in emoji_tags:
        if not validate_emoji_tag(emoji_name, guild):
            invalid_tags.append(emoji_name)
            logger.debug(f"Found invalid emoji tag: {emoji_name}")
    
    logger.debug(f"Found {len(invalid_tags)} invalid emoji tags: {invalid_tags}")
    return invalid_tags

def has_emoji_tags(text: str) -> bool:
    """
    Check if text contains any emoji tags.
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text contains emoji tags, False otherwise
    """
    logger.debug(f"Checking if text has emoji tags: {text[:100]}...")
    has_tags = bool(re.search(r'\{[^{}]+\}', text))
    logger.debug(f"Text has emoji tags: {has_tags}")
    return has_tags