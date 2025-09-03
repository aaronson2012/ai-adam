# src/utils/personalities.py

import os
import tomllib
from glob import glob

# Store the current personality for each server (in-memory fallback)
server_personalities = {}

def get_server_personality(guild_id):
    """Get the current personality for a server."""
    return server_personalities.get(guild_id, "default")

def set_server_personality(guild_id, personality):
    """Set the current personality for a server."""
    server_personalities[guild_id] = personality

def load_personality_from_file(file_path):
    """Load a personality definition from a TOML file."""
    try:
        with open(file_path, "rb") as f:
            data = tomllib.load(f)
            
        # Extract the personality data
        personality = {
            "name": data.get("name", "Unnamed Personality"),
            "description": data.get("description", ""),
            "personality_traits": data.get("personality_traits", {}).get("content", ""),
            "communication_style": data.get("communication_style", {}).get("content", ""),
            "behavior_patterns": data.get("behavior_patterns", {}).get("content", "")
        }
        
        return personality
    except Exception as e:
        print(f"Error loading personality from {file_path}: {e}")
        return None

def load_base_guidelines():
    """Load the base guidelines that apply to all personalities."""
    guidelines_path = os.path.join(os.path.dirname(__file__), "..", "personalities", "base_guidelines.toml")
    try:
        with open(guidelines_path, "rb") as f:
            data = tomllib.load(f)
        return data.get("base_guidelines", {}).get("content", "")
    except Exception as e:
        print(f"Error loading base guidelines: {e}")
        # Return the original hardcoded guidelines as fallback
        return """Important guidelines for all interactions:
- DO NOT try to act like a human - just be straightforward and natural
- DO NOT use phrases that sound like an AI trying to be casual (like "What's kickin'" or "spill the beans")
- DO NOT be artificially enthusiastic or energetic
- DO respond like you're having a genuine conversation with a friend
- DO be appropriately brief and to the point when that's called for
- DO avoid over-explaining or being unnecessarily verbose
- DO be genuine and authentic in your responses
- You MAY use emojis naturally and sparingly (1-2 per message) to enhance communication
- You MAY ask clarifying questions when needed, but do so sparingly and only when genuinely needed
- You SHOULD prioritize using server-specific emojis when available and appropriate"""

def load_all_personalities():
    """Load all personalities from the personalities directory."""
    personalities = {}
    personalities_dir = os.path.join(os.path.dirname(__file__), "..", "personalities")
    
    # Load base guidelines once
    base_guidelines = load_base_guidelines()
    
    # Add base guidelines to globals
    global BASE_GUIDELINES
    BASE_GUIDELINES = base_guidelines
    
    # Load all personality files
    personality_files = glob(os.path.join(personalities_dir, "*.toml"))
    
    for file_path in personality_files:
        # Skip the base guidelines file
        if os.path.basename(file_path) == "base_guidelines.toml":
            continue
            
        personality = load_personality_from_file(file_path)
        if personality:
            # Extract personality name from filename (without extension)
            personality_name = os.path.splitext(os.path.basename(file_path))[0]
            personalities[personality_name] = personality
    
    return personalities

# Load all personalities at module import time
PERSONALITIES = load_all_personalities()

def get_personality(personality_name="default"):
    """Get the personality definition by name, defaulting to 'default' if not found."""
    return PERSONALITIES.get(personality_name, PERSONALITIES.get("default", {
        "name": "Default Assistant",
        "description": "A helpful AI assistant",
        "personality_traits": "",
        "communication_style": "",
        "behavior_patterns": ""
    }))

def get_available_personalities():
    """Get a list of available personality names."""
    return list(PERSONALITIES.keys())

def get_personality_prompt(personality_name="default"):
    """Get the system prompt for a specific personality."""
    personality = get_personality(personality_name)
    
    # Build the complete prompt with base guidelines
    prompt = f"""You are {personality['name']}, {personality['description']}.
    
{personality['personality_traits']}

{personality['communication_style']}

{personality['behavior_patterns']}

{BASE_GUIDELINES}
"""
    return prompt

def register_personality(name, personality_data):
    """Register a new personality."""
    PERSONALITIES[name] = personality_data

def create_personality_template(name, description):
    """Create a template for a new personality with the base guidelines."""
    return {
        "name": name,
        "description": description,
        "personality_traits": "",
        "communication_style": "",
        "behavior_patterns": ""
    }