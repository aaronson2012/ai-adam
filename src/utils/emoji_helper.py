# src/utils/emoji_helper.py

import discord
import random

def get_server_emojis(guild):
    """Get a list of server emojis from a guild."""
    if guild is None:
        return []
    
    # Handle mock objects in tests
    try:
        # Return a list of emoji names in curly brace format for AI consumption
        # The AI should use {emoji_name} format, which will be converted to actual emojis later
        return [f"{{{emoji.name}}}" for emoji in guild.emojis]
    except (TypeError, AttributeError):
        # If guild.emojis is not iterable (e.g., in tests), return empty list
        return []

def get_random_emojis(guild, count=2):
    """Get a random selection of server emojis."""
    server_emojis = get_server_emojis(guild)
    
    # If we don't have enough server emojis, we can supplement with standard emojis
    # For now, we'll just return what we have or a subset
    if len(server_emojis) == 0:
        return []
    
    # Return up to 'count' random emojis
    return random.sample(server_emojis, min(count, len(server_emojis)))

def create_emoji_prompt(guild):
    """Create a prompt string with available server emojis."""
    server_emojis = get_server_emojis(guild)
    
    if not server_emojis:
        return ""
    
    emoji_list = ", ".join(server_emojis)
    return f"""

Available server emojis: {emoji_list}
Please prioritize using these server emojis liberally and frequently to enhance communication and add personality to your responses.
Remember to use the curly brace format {{emoji_name}} for custom server emojis.
Do NOT use the Discord emoji format like <:emoji_name:123456789>."""""