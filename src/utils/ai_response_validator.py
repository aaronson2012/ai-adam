# src/utils/ai_response_validator.py

import logging
import litellm
import json
from typing import List, Dict, Tuple, Optional
from src.utils.emoji_parser import find_invalid_emoji_tags

logger = logging.getLogger(__name__)

async def validate_and_retry_ai_response(
    response_text: str,
    guild,
    config: Dict,
    original_prompt: str,
    max_retries: int = 3
) -> Tuple[str, bool]:
    """
    Validate AI response and retry if invalid emoji tags are found.
    
    Args:
        response_text (str): The AI response to validate
        guild: The Discord guild to validate emojis against
        config (Dict): Configuration dictionary
        original_prompt (str): The original prompt sent to the AI
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        Tuple[str, bool]: Tuple of (final_response_text, was_retry_performed)
    """
    logger.debug(f"Validating AI response: {response_text[:100]}...")
    
    # Check for invalid emoji tags
    invalid_emojis = find_invalid_emoji_tags(response_text, guild)
    
    if not invalid_emojis:
        logger.debug("No invalid emoji tags found in response")
        return response_text, False
    
    logger.debug(f"Found invalid emoji tags: {invalid_emojis}")
    
    # If we have invalid emojis, we need to retry
    current_response = response_text
    retry_count = 0
    
    while invalid_emojis and retry_count < max_retries:
        retry_count += 1
        logger.debug(f"Retry attempt {retry_count}/{max_retries}")
        
        # Create a retry prompt that specifically addresses the invalid emojis
        retry_prompt = f"""
{original_prompt}

Your previous response contained invalid emoji references: {', '.join(invalid_emojis)}
Please rewrite your response using only valid emojis from the server or standard Unicode emojis.
Remember to enclose emoji names in curly braces like {{emoji_name}} for custom emojis or use Unicode emojis directly.

Previous response: {current_response}
""".strip()
        
        logger.debug(f"Retry prompt: {retry_prompt[:200]}...")
        
        try:
            # Retry with the AI
            retry_response = litellm.completion(
                model=config['ai']['default_model'],
                messages=[{"role": "user", "content": retry_prompt}],
                temperature=0.7,
                max_tokens=3000
            )
            
            # Extract the new response
            new_response = ""
            if (retry_response and 
                'choices' in retry_response and 
                len(retry_response['choices']) > 0 and 
                retry_response['choices'][0] and 
                'message' in retry_response['choices'][0] and 
                retry_response['choices'][0]['message'] and 
                'content' in retry_response['choices'][0]['message']):
                new_response = retry_response['choices'][0]['message']['content']
            
            logger.debug(f"Retry response: {new_response[:100]}...")
            
            # Update current response
            current_response = new_response
            
            # Check for invalid emojis again
            invalid_emojis = find_invalid_emoji_tags(current_response, guild)
            logger.debug(f"Invalid emojis after retry: {invalid_emojis}")
            
        except Exception as e:
            logger.error(f"Error during retry attempt {retry_count}: {e}")
            # If there's an error in retry, we'll return the original response
            break
    
    if invalid_emojis:
        logger.warning(f"Still have invalid emojis after {retry_count} retries: {invalid_emojis}")
    
    return current_response, True