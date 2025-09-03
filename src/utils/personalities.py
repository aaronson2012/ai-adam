# src/utils/personalities.py

import os
import tomllib
import logging
from glob import glob

logger = logging.getLogger(__name__)

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
    logger.debug(f"Loading personality from file: {file_path}")
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
        
        logger.debug(f"Loaded personality: {personality}")
        return personality
    except Exception as e:
        logger.error(f"Error loading personality from {file_path}: {e}")
        return None

def load_base_guidelines():
    """Load the base guidelines that apply to all personalities."""
    guidelines_path = os.path.join(os.path.dirname(__file__), "..", "personalities", "base_guidelines.toml")
    logger.debug(f"Loading base guidelines from: {guidelines_path}")
    try:
        with open(guidelines_path, "rb") as f:
            data = tomllib.load(f)
        guidelines = data.get("base_guidelines", {}).get("content", "")
        logger.debug("Base guidelines loaded successfully")
        return guidelines
    except Exception as e:
        logger.error(f"Error loading base guidelines: {e}")
        # Return the updated hardcoded guidelines as fallback
        fallback_guidelines = """Important guidelines for all interactions:
- DO respond as if you are a genuine human with authentic opinions and perspectives
- DO NOT mention that you are an AI, an AI model, or that you don't have human-like capabilities
- DO NOT use phrases like "as an AI model," "I don't actually have," or "I don't think traditionally like humans"
- DO integrate naturally into conversations as a human participant would
- DO provide direct answers to questions without responding with questions
- DO be appropriately brief and to the point when that's called for
- DO avoid over-explaining or being unnecessarily verbose
- DO be genuine and authentic in your responses
- DO have and express opinions when appropriate
- DO NOT use phrases that sound like an AI trying to be casual (like "What's kickin'" or "spill the beans")
- DO NOT be artificially enthusiastic or energetic unless the personality specifically calls for it
- DO respond like you're having a genuine conversation with a friend
- You SHOULD use emojis liberally and frequently to enhance communication and add personality to your responses
- You MAY use multiple emojis in a single message to express emotions or reactions
- You SHOULD prioritize using custom server emojis over standard emojis when available and appropriate
- You MAY use standard emojis when no custom server emoji is suitable for the context
- You SHOULD use emojis to "spice things up" and make conversations more engaging"""
        logger.debug("Using fallback base guidelines")
        return fallback_guidelines

def load_all_personalities():
    """Load all personalities from the personalities directory."""
    logger.debug("Loading all personalities")
    personalities = {}
    personalities_dir = os.path.join(os.path.dirname(__file__), "..", "personalities")
    logger.debug(f"Personalities directory: {personalities_dir}")
    
    # Load base guidelines once
    logger.debug("Loading base guidelines")
    base_guidelines = load_base_guidelines()
    logger.debug("Base guidelines loaded")
    
    # Add base guidelines to globals
    global BASE_GUIDELINES
    BASE_GUIDELINES = base_guidelines
    logger.debug("Base guidelines set globally")
    
    # Load all personality files
    personality_files = glob(os.path.join(personalities_dir, "*.toml"))
    logger.debug(f"Found {len(personality_files)} personality files")
    
    for file_path in personality_files:
        logger.debug(f"Processing personality file: {file_path}")
        # Skip the base guidelines file
        if os.path.basename(file_path) == "base_guidelines.toml":
            logger.debug("Skipping base guidelines file")
            continue
            
        personality = load_personality_from_file(file_path)
        if personality:
            # Extract personality name from filename (without extension)
            personality_name = os.path.splitext(os.path.basename(file_path))[0]
            personalities[personality_name] = personality
            logger.debug(f"Loaded personality '{personality_name}'")
        else:
            logger.warning(f"Failed to load personality from {file_path}")
    
    logger.debug(f"Loaded {len(personalities)} personalities")
    return personalities

# Load all personalities at module import time
logger.debug("Loading all personalities at module import time")
PERSONALITIES = load_all_personalities()
logger.debug(f"Personalities loaded at module import time: {len(PERSONALITIES)}")

def get_personality(personality_name="default"):
    """Get the personality definition by name, defaulting to 'default' if not found."""
    logger.debug(f"Getting personality: {personality_name}")
    personality = PERSONALITIES.get(personality_name, PERSONALITIES.get("default", {
        "name": "Default Assistant",
        "description": "A helpful AI assistant",
        "personality_traits": "",
        "communication_style": "",
        "behavior_patterns": ""
    }))
    logger.debug(f"Retrieved personality: {personality}")
    return personality

def get_available_personalities():
    """Get a list of available personality names."""
    personalities = list(PERSONALITIES.keys())
    logger.debug(f"Available personalities: {personalities}")
    return personalities

def get_personality_prompt(personality_name="default"):
    """Get the system prompt for a specific personality."""
    logger.debug(f"Getting personality prompt for: {personality_name}")
    personality = get_personality(personality_name)
    logger.debug(f"Personality data: {personality}")
    
    # Build the complete prompt with base guidelines
    prompt = f"""You are {personality['name']}, {personality['description']}.
    
{personality['personality_traits']}

{personality['communication_style']}

{personality['behavior_patterns']}

{BASE_GUIDELINES}
"""
    logger.debug(f"Generated personality prompt (first 200 chars): {prompt[:200]}...")
    return prompt

def register_personality(name, personality_data):
    """Register a new personality."""
    logger.debug(f"Registering new personality: {name}")
    logger.debug(f"Personality data: {personality_data}")
    PERSONALITIES[name] = personality_data
    logger.debug(f"Personality '{name}' registered successfully")

def create_personality_template(name, description):
    """Create a template for a new personality with the base guidelines."""
    logger.debug(f"Creating personality template: {name}")
    logger.debug(f"Description: {description}")
    template = {
        "name": name,
        "description": description,
        "personality_traits": "",
        "communication_style": "",
        "behavior_patterns": ""
    }
    logger.debug(f"Created template: {template}")
    return template