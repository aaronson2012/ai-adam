# src/cogs/reactions.py

import discord
from discord.ext import commands
import logging
import asyncio
import random
from typing import Dict, List, Set
import json
import litellm
from collections import deque

logger = logging.getLogger(__name__)

class ReactionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_manager = bot.db_manager
        # Track recently reacted messages to avoid spam
        self.recently_reacted: Dict[int, Set[int]] = {}  # guild_id -> set of message IDs
        self.message_counters: Dict[int, int] = {}  # guild_id -> message count
        self.messages_since_last_reaction: Dict[int, int] = {}  # guild_id -> count since last reaction
        self.max_recent_messages = 50  # Track last 50 messages per guild
        
    async def get_recently_reacted(self, guild_id: int) -> Set[int]:
        """Get recently reacted message IDs for a guild."""
        logger.debug(f"Getting recently reacted messages for guild ID: {guild_id}")
        if guild_id not in self.recently_reacted:
            self.recently_reacted[guild_id] = set()
            logger.debug(f"Initialized recently reacted set for guild {guild_id}")
        logger.debug(f"Recently reacted messages for guild {guild_id}: {self.recently_reacted[guild_id]}")
        return self.recently_reacted[guild_id]
        
    async def add_recently_reacted(self, guild_id: int, message_id: int):
        """Add a message ID to the recently reacted set for a guild."""
        logger.debug(f"Adding message {message_id} to recently reacted set for guild {guild_id}")
        if guild_id not in self.recently_reacted:
            self.recently_reacted[guild_id] = set()
            logger.debug(f"Initialized recently reacted set for guild {guild_id}")
        
        self.recently_reacted[guild_id].add(message_id)
        logger.debug(f"Added message {message_id} to recently reacted set for guild {guild_id}")
        
        # Keep only the most recent messages
        if len(self.recently_reacted[guild_id]) > self.max_recent_messages:
            logger.debug(f"Recently reacted set exceeds max size ({self.max_recent_messages}), removing oldest entry")
            # Remove the oldest entries (this is a simple approach, could be improved)
            oldest = next(iter(self.recently_reacted[guild_id]))
            self.recently_reacted[guild_id].remove(oldest)
            logger.debug(f"Removed oldest message {oldest} from recently reacted set for guild {guild_id}")
            
    async def is_recently_reacted(self, guild_id: int, message_id: int) -> bool:
        """Check if a message has been recently reacted to."""
        logger.debug(f"Checking if message {message_id} was recently reacted to in guild {guild_id}")
        recently_reacted = await self.get_recently_reacted(guild_id)
        is_recent = message_id in recently_reacted
        logger.debug(f"Message {message_id} recently reacted status: {is_recent}")
        return is_recent
        
    async def clean_old_reactions(self, guild_id: int):
        """Clean up old reactions to prevent memory bloat."""
        logger.debug(f"Cleaning old reactions for guild {guild_id}")
        if guild_id in self.recently_reacted:
            logger.debug(f"Guild {guild_id} has {len(self.recently_reacted[guild_id])} recently reacted messages")
            # Keep only the most recent entries
            if len(self.recently_reacted[guild_id]) > self.max_recent_messages:
                logger.debug(f"Recently reacted set exceeds max size ({self.max_recent_messages}), cleaning up")
                # Convert to list, sort, and keep only recent ones
                recent_list = list(self.recently_reacted[guild_id])
                logger.debug(f"Original list size: {len(recent_list)}")
                # Keep the most recent entries (this is a simplification)
                self.recently_reacted[guild_id] = set(recent_list[-self.max_recent_messages:])
                logger.debug(f"Cleaned list size: {len(self.recently_reacted[guild_id])}")
            else:
                logger.debug(f"Recently reacted set is within size limit ({len(self.recently_reacted[guild_id])} <= {self.max_recent_messages})")
        else:
            logger.debug(f"No recently reacted messages found for guild {guild_id}")
                
    async def increment_message_counter(self, guild_id: int) -> int:
        """Increment and return the message counter for a guild."""
        logger.debug(f"Incrementing message counter for guild {guild_id}")
        if guild_id not in self.message_counters:
            self.message_counters[guild_id] = 0
            logger.debug(f"Initialized message counter for guild {guild_id} to 0")
            
        self.message_counters[guild_id] += 1
        logger.debug(f"Message counter for guild {guild_id} incremented to {self.message_counters[guild_id]}")
        return self.message_counters[guild_id]
        
    async def get_messages_since_last_reaction(self, guild_id: int) -> int:
        """Get the number of messages since the last reaction."""
        count = self.messages_since_last_reaction.get(guild_id, 0)
        logger.debug(f"Messages since last reaction for guild {guild_id}: {count}")
        return count
        
    async def reset_messages_since_last_reaction(self, guild_id: int):
        """Reset the counter after a reaction."""
        logger.debug(f"Resetting messages since last reaction counter for guild {guild_id}")
        self.messages_since_last_reaction[guild_id] = 0
        logger.debug(f"Messages since last reaction counter for guild {guild_id} reset to 0")
        
    async def increment_messages_since_last_reaction(self, guild_id: int) -> int:
        """Increment the counter of messages since last reaction."""
        logger.debug(f"Incrementing messages since last reaction counter for guild {guild_id}")
        if guild_id not in self.messages_since_last_reaction:
            self.messages_since_last_reaction[guild_id] = 0
            logger.debug(f"Initialized messages since last reaction counter for guild {guild_id} to 0")
        self.messages_since_last_reaction[guild_id] += 1
        logger.debug(f"Messages since last reaction counter for guild {guild_id} incremented to {self.messages_since_last_reaction[guild_id]}")
        return self.messages_since_last_reaction[guild_id]
                
    async def get_recent_reactions_in_channel(self, channel: discord.TextChannel, limit: int = 10) -> List[dict]:
        """Get recent reactions in the channel to avoid spam."""
        logger.debug(f"Getting recent reactions in channel {channel.name} (ID: {channel.id}) with limit {limit}")
        recent_reactions = []
        try:
            async for message in channel.history(limit=limit):
                if message.author == self.bot.user and message.reactions:
                    # This is a message we reacted to
                    reaction_info = {
                        "message_id": message.id,
                        "content": message.content[:100] if message.content else "",  # First 100 chars
                        "timestamp": message.created_at
                    }
                    recent_reactions.append(reaction_info)
                    logger.debug(f"Found reacted message: {reaction_info}")
        except Exception as e:
            logger.warning(f"Could not fetch recent reactions: {e}")
        logger.debug(f"Found {len(recent_reactions)} recent reactions in channel {channel.name}")
        return recent_reactions
                
    async def get_relevant_context(self, message: discord.Message) -> str:
        """Get relevant context for the AI to decide on reactions."""
        logger.debug(f"Getting relevant context for message {message.id} in channel {message.channel.name}")
        context_parts = []
        
        # Add recent message history (last 5 messages in the channel)
        try:
            logger.debug("Fetching recent message history")
            history = []
            async for msg in message.channel.history(limit=5, before=message):
                # Skip bot messages except for AI responses
                if not msg.author.bot or msg.author == self.bot.user:
                    # SAFELY handle message content
                    content = ""
                    if msg.content and isinstance(msg.content, str):
                        content = msg.content
                    history.append(f"{msg.author.display_name}: {content}")
                    logger.debug(f"Added message to history: {msg.author.display_name}: {content[:50]}...")
            
            if history:
                context_parts.append("Recent conversation context:")
                context_parts.append("\n".join(reversed(history)))  # Reverse to chronological order
                logger.debug(f"Added conversation context with {len(history)} messages")
            else:
                logger.debug("No conversation history found")
        except Exception as e:
            logger.warning(f"Could not fetch message history: {e}")
            
        # Add user memory if available
        try:
            logger.debug(f"Fetching user memory for user {message.author.id}")
            user_id = str(message.author.id)
            user_memory = await self.db_manager.get_user_memory(user_id)
            logger.debug(f"User memory retrieved: {user_memory}")
            if user_memory and user_memory.get("known_facts"):
                context_parts.append(f"User context: {user_memory['known_facts']}")
                logger.debug("Added user context to context parts")
            else:
                logger.debug("No user memory found")
        except Exception as e:
            logger.warning(f"Could not fetch user memory: {e}")
            
        # Add recent reactions in channel to avoid spam
        try:
            logger.debug("Fetching recent reactions in channel")
            recent_reactions = await self.get_recent_reactions_in_channel(message.channel)
            if recent_reactions:
                context_parts.append(f"Recent bot reactions in this channel: {len(recent_reactions)} in last 10 messages")
                logger.debug(f"Added reaction context: {len(recent_reactions)} recent reactions")
            else:
                logger.debug("No recent reactions found")
        except Exception as e:
            logger.warning(f"Could not fetch recent reactions: {e}")
            
        context = "\n\n".join(context_parts)
        logger.debug(f"Generated context with {len(context_parts)} parts, total length: {len(context)} characters")
        return context
        
    async def should_react_to_message(self, message: discord.Message) -> bool:
        """Determine if the bot should react to a message using AI analysis."""
        logger.debug(f"Determining if bot should react to message {message.id}")
        try:
            # Don't react to bot messages (including ourselves)
            if message.author.bot:
                logger.debug("Message is from a bot, not reacting")
                # Increment counter but don't react
                await self.increment_messages_since_last_reaction(message.guild.id)
                return False
                
            # Don't react in DMs
            if not message.guild:
                logger.debug("Message is in DM, not reacting")
                # Increment counter but don't react
                await self.increment_messages_since_last_reaction(message.guild.id)
                return False
                
            # Don't react if we've already reacted recently to this message
            if await self.is_recently_reacted(message.guild.id, message.id):
                logger.debug("Message was recently reacted to, not reacting")
                # Increment counter but don't react
                await self.increment_messages_since_last_reaction(message.guild.id)
                return False
                
            # COMPREHENSIVE content validation
            if not hasattr(message, 'content') or message.content is None or not isinstance(message.content, str):
                logger.debug("Message content is invalid, not reacting")
                # Increment counter but don't react
                await self.increment_messages_since_last_reaction(message.guild.id)
                return False
                
            # Additional safety check
            content = message.content
            if not content:
                logger.debug("Message content is empty, not reacting")
                # Increment counter but don't react
                await self.increment_messages_since_last_reaction(message.guild.id)
                return False
                
            # Now it's safe to strip
            content = content.strip()
            content_lower = content.lower()
            if len(content) < 3:
                logger.debug("Message content is too short, not reacting")
                # Increment counter but don't react
                await self.increment_messages_since_last_reaction(message.guild.id)
                return False
                
            # Check for explicit reaction requests before other filters
            # This handles cases like "this message should be reacted to with a dog emoji"
            if ("should be reacted to" in content_lower or 
                "react to this" in content_lower or 
                "please react" in content_lower or
                "react with" in content_lower):
                logger.debug("Message contains explicit reaction request")
                # For explicit requests, give a higher chance to react
                # But still increment the counter to avoid spam
                await self.increment_messages_since_last_reaction(message.guild.id)
                # 70% chance to react to explicit requests
                should_react = random.random() < 0.7
                logger.debug(f"Explicit request reaction decision: {should_react}")
                return should_react
                
            # Skip common short responses
            if content_lower in ['yes', 'no', 'yeah', 'yep', 'nope', 'ok', 'okay', 'k', 'thanks', 'thx']:
                logger.debug("Message contains common short response, not reacting")
                # Increment counter but don't react
                await self.increment_messages_since_last_reaction(message.guild.id)
                return False
                
            # Skip messages that are just mentions or links
            if len(content.split()) < 2 and (content.startswith('<@') or content.startswith('http')):
                logger.debug("Message is just a mention or link, not reacting")
                # Increment counter but don't react
                await self.increment_messages_since_last_reaction(message.guild.id)
                return False
                
            # Increment message counter for this guild
            message_count = await self.increment_message_counter(message.guild.id)
            messages_since_last = await self.increment_messages_since_last_reaction(message.guild.id)
            logger.debug(f"Message count: {message_count}, Messages since last reaction: {messages_since_last}")
            
            # Get server personality for context
            try:
                guild_id = str(message.guild.id)
                personality_name = await self.db_manager.get_server_personality(guild_id)
                logger.debug(f"Server personality: {personality_name}")
            except Exception as e:
                logger.warning(f"Error getting server personality: {e}")
                personality_name = "default"
                
            # Create prompt for AI to decide if reaction is appropriate
            logger.debug("Generating AI prompt for reaction decision")
            prompt = f"""
You are an AI assistant that decides whether to react to Discord messages with emojis. 
Your response must be ONLY a valid JSON object with this exact format:
{{"should_react": true, "interest_level": "low", "reason": "brief explanation"}}

Valid interest levels: "low", "medium", "high", "very_high"

Factors to consider:
- Is the message interesting, funny, thought-provoking, or emotionally significant?
- Does it warrant a reaction?
- Would a reaction enhance the conversation?
- Avoid reacting to short, common responses like "yes", "no", "yeah"
- Consider the recent conversation context

Message to analyze: "{content}"

Context: {await self.get_relevant_context(message)}
Messages since last reaction: {messages_since_last}

Personality: {personality_name}

Respond ONLY with the JSON format specified above. Do not include any other text.
"""
            logger.debug(f"AI prompt generated (first 200 chars): {prompt[:200]}...")
            
            try:
                logger.debug("Calling AI to determine if should react")
                response = litellm.completion(
                    model=self.bot.config['ai']['default_model'],  # Use the same model as the bot
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=500  # Increased token limit to prevent MAX_TOKENS finish reason
                )
                logger.debug("AI response received")
                
                # Check if the response was cut off due to token limit
                if (response and 
                    'choices' in response and 
                    len(response['choices']) > 0 and 
                    response['choices'][0] and 
                    'finish_reason' in response['choices'][0] and
                    response['choices'][0]['finish_reason'] == 'length'):
                    logger.warning("AI response was cut off due to token limit, using conservative approach")
                    # Conservative approach: only react if it's been a while
                    if messages_since_last >= 8:
                        should_react = random.random() < 0.1  # 10% chance if it's been a while
                        logger.debug(f"Token limit cut off, conservative reaction decision: {should_react}")
                        return should_react
                    logger.debug("Token limit cut off, not reacting (not enough messages since last reaction)")
                    return False
                
                # SAFELY handle AI response content
                content_response = ""
                if (response and 
                    'choices' in response and 
                    len(response['choices']) > 0 and 
                    response['choices'][0] and 
                    'message' in response['choices'][0] and 
                    response['choices'][0]['message'] and 
                    'content' in response['choices'][0]['message']):
                    content_response = response['choices'][0]['message']['content']
                
                # Validate content_response
                if not content_response or not isinstance(content_response, str):
                    content_response = ""
                else:
                    content_response = content_response.strip()
                logger.debug(f"AI response content: {content_response}")
                
                # Parse JSON response
                if content_response.startswith("```json"):
                    content_response = content_response[7:]
                if content_response.startswith("```"):
                    content_response = content_response[3:]
                if content_response.endswith("```"):
                    content_response = content_response[:-3]
                    
                # Additional safety check before JSON parsing
                if not content_response or not isinstance(content_response, str):
                    result = {"should_react": False, "interest_level": "low", "reason": "Invalid AI response"}
                    logger.debug("Invalid AI response, using default result")
                else:
                    try:
                        result = json.loads(content_response)
                        logger.debug(f"Parsed AI response: {result}")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse AI response as JSON: {e}. Response was: {content_response}")
                        # Try to extract information from the response even if it's not valid JSON
                        # Check if the response contains words indicating a reaction should happen
                        response_lower = content_response.lower()  # Don't strip here to preserve content
                        should_react = (
                            "true" in response_lower or 
                            "yes" in response_lower or 
                            "should react" in response_lower or 
                            "react" in response_lower
                        )
                        result = {"should_react": should_react, "interest_level": "low", "reason": "Fallback parsing"}
                        logger.debug(f"Fallback parsing result: {result}")
                    
                should_react = result.get("should_react", False)
                interest_level = result.get("interest_level", "low")
                logger.debug(f"AI decision: should_react={should_react}, interest_level={interest_level}")
                
                # Let the LLM decision be the final decision, with minimal frequency management
                # Only prevent reactions if we've had too many in a very short time
                if should_react:
                    # Very minimal frequency management to prevent extreme spam
                    if messages_since_last >= 1:  # At least 1 message since last reaction
                        logger.debug("AI said to react and enough messages since last reaction, reacting")
                        return True
                    else:
                        # Even if it's been a very short time, still mostly respect the AI's decision
                        # Only prevent if it would be truly excessive (like multiple reactions per second)
                        decision = random.random() < 0.9  # 90% chance to respect AI decision even if it's been a short time
                        logger.debug(f"AI said to react, <1 message since last reaction, 90% chance decision: {decision}")
                        return decision
                else:
                    logger.debug("AI said not to react")
                    return False
                    
            except Exception as e:
                logger.error(f"Error in AI completion: {e}")
                # Only react if it's been a very long time (fallback behavior)
                if messages_since_last >= 10:
                    decision = random.random() < 0.1  # 10% chance if it's been a very long time
                    logger.debug(f"AI error, conservative reaction decision (>= 10 messages): {decision}")
                    return decision
                logger.debug("AI error, conservative reaction decision (< 10 messages): False")
                return False
                
        except Exception as e:
            logger.error(f"Error determining if should react: {e}", exc_info=True)
            # Always increment counter even on error
            try:
                await self.increment_messages_since_last_reaction(message.guild.id)
            except:
                pass
            return False
            
    async def get_appropriate_reaction_emojis(self, message: discord.Message) -> List[str]:
        """Get appropriate emojis to react with using AI analysis."""
        logger.debug(f"Getting appropriate reaction emojis for message {message.id}")
        try:
            # COMPREHENSIVE content validation
            if not hasattr(message, 'content') or message.content is None or not isinstance(message.content, str):
                logger.debug("Message content is invalid, returning fallback reaction")
                return ["👍"]  # Fallback reaction
                
            # Additional safety check
            content = message.content
            if not content:
                logger.debug("Message content is empty, returning fallback reaction")
                return ["👍"]  # Fallback reaction
                
            # Now it's safe to strip
            content = content.strip()
            content_lower = content.lower()
            logger.debug(f"Message content: {content}")
            
            # Check for explicit reaction requests and try to extract the requested emoji
            # This handles cases like "this message should be reacted to with a dog emoji"
            if ("should be reacted to" in content_lower or 
                "react to this" in content_lower or 
                "please react" in content_lower or
                "react with" in content_lower):
                logger.debug("Message contains explicit reaction request, trying to extract requested emoji")
                # Try to extract the requested emoji
                # Look for common patterns like "with a [emoji] emoji" or "with [emoji]"
                import re
                
                # Pattern 1: "with a dog emoji" or "with dog emoji"
                match = re.search(r"with a? ([^ ]+) emoji", content_lower)
                if match:
                    emoji_request = match.group(1)
                    logger.debug(f"Found emoji request pattern 1: {emoji_request}")
                    # Try to find a matching emoji
                    for emoji in message.guild.emojis:
                        if emoji_request in emoji.name.lower():
                            logger.debug(f"Found matching custom emoji: {emoji}")
                            return [str(emoji)]
                
                # Pattern 2: "with [emoji]"
                match = re.search(r"with ([^ ]+)", content_lower)
                if match:
                    emoji_request = match.group(1)
                    logger.debug(f"Found emoji request pattern 2: {emoji_request}")
                    # Try to find a matching emoji
                    for emoji in message.guild.emojis:
                        if emoji_request in emoji.name.lower():
                            logger.debug(f"Found matching custom emoji: {emoji}")
                            return [str(emoji)]
                    # Check if it's already an emoji character
                    if len(emoji_request) <= 2 and any(ord(char) > 127 for char in emoji_request):
                        logger.debug(f"Found emoji character: {emoji_request}")
                        return [emoji_request]
                    # Check if it's in the Discord custom emoji format <:name:id> and extract the name
                    discord_emoji_match = re.search(r"<:([^:]+):\d+>", emoji_request)
                    if discord_emoji_match:
                        emoji_name = discord_emoji_match.group(1)
                        logger.debug(f"Found Discord emoji format, extracted name: {emoji_name}")
                        # Try to find matching emoji by name
                        for emoji in message.guild.emojis:
                            if emoji_name.lower() == emoji.name.lower():
                                logger.debug(f"Found matching custom emoji: {emoji}")
                                return [str(emoji)]
                
                # Fallback if we can't determine the specific emoji
                logger.debug("Could not determine specific emoji, returning fallback reaction")
                return ["👍"]
                
            # Get server personality for context
            try:
                guild_id = str(message.guild.id)
                personality_name = await self.db_manager.get_server_personality(guild_id)
                logger.debug(f"Server personality: {personality_name}")
            except Exception as e:
                logger.warning(f"Error getting server personality: {e}")
                personality_name = "default"
                
            # Create prompt for AI to decide on appropriate reactions
            # Get available emojis (limit to first 30 to avoid overwhelming the model)
            logger.debug("Collecting available emojis")
            available_emojis = []
            for emoji in message.guild.emojis:
                available_emojis.append(f"{emoji.name} ({emoji.id})")
                if len(available_emojis) >= 30:
                    logger.debug("Reached emoji limit of 30")
                    break
            logger.debug(f"Available emojis: {len(available_emojis)}")
                    
            logger.debug("Generating AI prompt for emoji selection")
            prompt = f"""
You are an AI assistant that selects appropriate emojis to react to Discord messages.
Your response should be ONLY a JSON array of emoji identifiers.

Message: "{content}"

Context: {await self.get_relevant_context(message)}

Personality: {personality_name}

Available custom emojis in this server (name and ID):
{', '.join(available_emojis) if available_emojis else "No custom emojis available"}

Select 1-3 appropriate emojis to react with. For custom emojis, use just the name.
For Unicode emojis, use the actual emoji character.
Respond ONLY with a JSON array like:
["👍", "😂", "🔥"]

OR for custom emojis:
["custom_emoji_name", "👍", "😂"]

IMPORTANT: For custom emoji names, use ONLY the name part (e.g., "jakeylook"), not the full Discord format like "<:jakeylook:1267924153114038272>".
"""
            logger.debug(f"AI prompt generated (first 200 chars): {prompt[:200]}...")
            
            try:
                logger.debug("Calling AI to select appropriate emojis")
                response = litellm.completion(
                    model=self.bot.config['ai']['default_model'],  # Use the same model as the bot
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=300
                )
                logger.debug("AI response received")
                
                # SAFELY handle AI response content
                content_response = ""
                if (response and 
                    'choices' in response and 
                    len(response['choices']) > 0 and 
                    response['choices'][0] and 
                    'message' in response['choices'][0] and 
                    response['choices'][0]['message'] and 
                    'content' in response['choices'][0]['message']):
                    content_response = response['choices'][0]['message']['content']
                
                # Validate content_response
                if not content_response or not isinstance(content_response, str):
                    content_response = ""
                else:
                    content_response = content_response.strip()
                logger.debug(f"AI response content: {content_response}")
                
                # Parse JSON response
                if content_response.startswith("```json"):
                    content_response = content_response[7:]
                if content_response.startswith("```"):
                    content_response = content_response[3:]
                if content_response.endswith("```"):
                    content_response = content_response[:-3]
                    
                # Additional safety check before JSON parsing
                if not content_response or not isinstance(content_response, str):
                    emoji_names = ["👍"]  # Safe fallback
                    logger.debug("Invalid AI response, using fallback reaction")
                else:
                    try:
                        emoji_names = json.loads(content_response)
                        logger.debug(f"Parsed emoji names: {emoji_names}")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse emoji response as JSON: {e}. Response was: {content_response}")
                        # Fallback to simple reactions
                        emoji_names = ["👍"]
                        logger.debug("JSON parsing failed, using fallback reaction")
                
                # Ensure we have a list
                if not isinstance(emoji_names, list):
                    emoji_names = ["👍"]
                    logger.debug("Emoji names is not a list, using fallback reaction")
                
                # Convert to actual emoji objects or unicode emojis
                logger.debug("Converting emoji names to actual emojis")
                reactions = []
                for emoji_name in emoji_names[:3]:  # Limit to 3 emojis
                    # Check if it's a custom emoji name
                    emoji_obj = discord.utils.get(message.guild.emojis, name=emoji_name)
                    if emoji_obj:
                        # For custom emojis, we need to use the proper Discord format
                        # The emoji_obj already contains the correct formatting when converted to string
                        reactions.append(str(emoji_obj))
                        logger.debug(f"Added custom emoji: {emoji_obj}")
                    else:
                        # Check if it's already in the proper Discord custom emoji format <:name:id>
                        # or if it's a unicode emoji
                        reactions.append(emoji_name)
                        logger.debug(f"Added emoji: {emoji_name}")
                        
                # Ensure we have at least one reaction
                if not reactions:
                    reactions = ["👍"]
                    logger.debug("No reactions found, using fallback reaction")
                        
                logger.debug(f"Final reactions: {reactions}")
                return reactions[:3]  # Ensure we don't exceed 3
                
            except Exception as e:
                logger.error(f"Error getting reaction emojis: {e}")
                # Fallback to simple reactions
                logger.debug("Returning fallback reaction due to error")
                return ["👍"]
        except Exception as e:
            logger.error(f"Error in get_appropriate_reaction_emojis: {e}", exc_info=True)
            logger.debug("Returning fallback reaction due to exception")
            return ["👍"]  # Safe fallback
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for messages and react appropriately using AI."""
        try:
            logger.debug(f"ReactionCog.on_message called for message ID {message.id}")
            
            # Only process messages in guilds (not DMs)
            if not message.guild:
                logger.debug("Message is not in a guild, skipping reactions")
                return
                
            # Don't react to bot messages (including ourselves)
            if message.author.bot:
                logger.debug("Message is from a bot, skipping reactions")
                return
                
            logger.debug(f"Processing message from {message.author} in guild {message.guild.id}: {message.content[:100]}")
                
            # Check if we should react to this message (using AI)
            should_react = await self.should_react_to_message(message)
            logger.debug(f"should_react_to_message returned: {should_react}")
            
            if not should_react:
                logger.debug("AI determined not to react to this message")
                return
                
            # Get appropriate reactions (using AI)
            reactions = await self.get_appropriate_reaction_emojis(message)
            logger.debug(f"get_appropriate_reaction_emojis returned: {reactions}")
            
            if reactions:
                try:
                    logger.debug(f"Attempting to add reactions {reactions} to message {message.id}")
                    # Add reactions to the message
                    for emoji in reactions:
                        logger.debug(f"Adding reaction: {emoji}")
                        await message.add_reaction(emoji)
                        # Small delay between reactions to avoid rate limiting
                        await asyncio.sleep(0.5)
                        logger.debug(f"Successfully added reaction: {emoji}")
                        
                    # Mark this message as recently reacted to
                    await self.add_recently_reacted(message.guild.id, message.id)
                    
                    # Reset the counter since we just reacted
                    await self.reset_messages_since_last_reaction(message.guild.id)
                    
                    # Clean up old reactions periodically
                    await self.clean_old_reactions(message.guild.id)
                    
                    logger.info(f"Added reactions {reactions} to message {message.id} in guild {message.guild.id}")
                    
                except discord.Forbidden:
                    # Bot doesn't have permission to add reactions
                    logger.warning(f"Bot lacks permission to add reactions in guild {message.guild.id}")
                except discord.HTTPException as e:
                    # Other HTTP errors
                    logger.error(f"HTTP error when adding reactions: {e}")
                except Exception as e:
                    # Other errors
                    logger.error(f"Unexpected error when adding reactions: {e}", exc_info=True)
            else:
                logger.debug("No reactions to add")
        except Exception as e:
            logger.error(f"Error in on_message listener: {e}", exc_info=True)

def setup(bot):
    """Setup function for the cog."""
    logger.debug("Setting up ReactionCog")
    cog = ReactionCog(bot)
    bot.add_cog(cog)
    logger.info("ReactionCog loaded successfully")