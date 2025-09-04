# src/utils/ai_response_validator.py

import logging
import litellm
import json
from typing import List, Dict, Tuple, Optional
from src.utils.emoji_parser import find_invalid_emoji_tags
from src.utils.emoji_formatter import validate_emoji_formatting

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
    
    # Check for improper emoji formatting
    improper_formatting = not validate_emoji_formatting(response_text)
    
    if not invalid_emojis and not improper_formatting:
        logger.debug("No invalid emoji tags or improper formatting found in response")
        return response_text, False
    
    logger.debug(f"Found issues - invalid emoji tags: {invalid_emojis}, improper formatting: {improper_formatting}")
    
    # If we have issues, we need to retry
    current_response = response_text
    retry_count = 0
    
    while (invalid_emojis or improper_formatting) and retry_count < max_retries:
        retry_count += 1
        logger.debug(f"Retry attempt {retry_count}/{max_retries}")
        
        # Create a retry prompt that specifically addresses the issues
        issues = []
        if invalid_emojis:
            issues.append(f"invalid emoji references: {', '.join(invalid_emojis)}")
        if improper_formatting:
            issues.append("improper emoji formatting")
            
        retry_prompt = f"""
{original_prompt}

Your previous response contained {', '.join(issues)}.
Please rewrite your response using only valid emojis from the server or standard Unicode emojis.
Remember to enclose custom emoji names in curly braces like {{emoji_name}} for custom emojis or use Unicode emojis directly.
Do NOT use the Discord emoji format like <:emoji_name:123456789>.

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
            
            # Check for issues again
            invalid_emojis = find_invalid_emoji_tags(current_response, guild)
            improper_formatting = not validate_emoji_formatting(current_response)
            logger.debug(f"Issues after retry - invalid emojis: {invalid_emojis}, improper formatting: {improper_formatting}")
            
        except Exception as e:
            logger.error(f"Error during retry attempt {retry_count}: {e}")
            # If there's an error in retry, we'll return the original response
            break
    
    if invalid_emojis or improper_formatting:
        logger.warning(f"Still have issues after {retry_count} retries - invalid emojis: {invalid_emojis}, improper formatting: {improper_formatting}")
    
    return current_response, True