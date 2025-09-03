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
        if guild_id not in self.recently_reacted:
            self.recently_reacted[guild_id] = set()
        return self.recently_reacted[guild_id]
        
    async def add_recently_reacted(self, guild_id: int, message_id: int):
        """Add a message ID to the recently reacted set for a guild."""
        if guild_id not in self.recently_reacted:
            self.recently_reacted[guild_id] = set()
        
        self.recently_reacted[guild_id].add(message_id)
        
        # Keep only the most recent messages
        if len(self.recently_reacted[guild_id]) > self.max_recent_messages:
            # Remove the oldest entries (this is a simple approach, could be improved)
            oldest = next(iter(self.recently_reacted[guild_id]))
            self.recently_reacted[guild_id].remove(oldest)
            
    async def is_recently_reacted(self, guild_id: int, message_id: int) -> bool:
        """Check if a message has been recently reacted to."""
        recently_reacted = await self.get_recently_reacted(guild_id)
        return message_id in recently_reacted
        
    async def clean_old_reactions(self, guild_id: int):
        """Clean up old reactions to prevent memory bloat."""
        if guild_id in self.recently_reacted:
            # Keep only the most recent entries
            if len(self.recently_reacted[guild_id]) > self.max_recent_messages:
                # Convert to list, sort, and keep only recent ones
                recent_list = list(self.recently_reacted[guild_id])
                # Keep the most recent entries (this is a simplification)
                self.recently_reacted[guild_id] = set(recent_list[-self.max_recent_messages:])
                
    async def increment_message_counter(self, guild_id: int) -> int:
        """Increment and return the message counter for a guild."""
        if guild_id not in self.message_counters:
            self.message_counters[guild_id] = 0
            
        self.message_counters[guild_id] += 1
        return self.message_counters[guild_id]
        
    async def get_messages_since_last_reaction(self, guild_id: int) -> int:
        """Get the number of messages since the last reaction."""
        return self.messages_since_last_reaction.get(guild_id, 0)
        
    async def reset_messages_since_last_reaction(self, guild_id: int):
        """Reset the counter after a reaction."""
        self.messages_since_last_reaction[guild_id] = 0
        
    async def increment_messages_since_last_reaction(self, guild_id: int) -> int:
        """Increment the counter of messages since last reaction."""
        if guild_id not in self.messages_since_last_reaction:
            self.messages_since_last_reaction[guild_id] = 0
        self.messages_since_last_reaction[guild_id] += 1
        return self.messages_since_last_reaction[guild_id]
                
    async def get_recent_reactions_in_channel(self, channel: discord.TextChannel, limit: int = 10) -> List[dict]:
        """Get recent reactions in the channel to avoid spam."""
        recent_reactions = []
        try:
            async for message in channel.history(limit=limit):
                if message.author == self.bot.user and message.reactions:
                    # This is a message we reacted to
                    reaction_info = {
                        "message_id": message.id,
                        "content": message.content[:100],  # First 100 chars
                        "timestamp": message.created_at
                    }
                    recent_reactions.append(reaction_info)
        except Exception as e:
            logger.warning(f"Could not fetch recent reactions: {e}")
        return recent_reactions
                
    async def get_relevant_context(self, message: discord.Message) -> str:
        """Get relevant context for the AI to decide on reactions."""
        context_parts = []
        
        # Add recent message history (last 5 messages in the channel)
        try:
            history = []
            async for msg in message.channel.history(limit=5, before=message):
                # Skip bot messages except for AI responses
                if not msg.author.bot or msg.author == self.bot.user:
                    history.append(f"{msg.author.display_name}: {msg.content}")
            
            if history:
                context_parts.append("Recent conversation context:")
                context_parts.append("\n".join(reversed(history)))  # Reverse to chronological order
        except Exception as e:
            logger.warning(f"Could not fetch message history: {e}")
            
        # Add user memory if available
        try:
            user_id = str(message.author.id)
            user_memory = await self.db_manager.get_user_memory(user_id)
            if user_memory and user_memory.get("known_facts"):
                context_parts.append(f"User context: {user_memory['known_facts']}")
        except Exception as e:
            logger.warning(f"Could not fetch user memory: {e}")
            
        # Add recent reactions in channel to avoid spam
        try:
            recent_reactions = await self.get_recent_reactions_in_channel(message.channel)
            if recent_reactions:
                context_parts.append(f"Recent bot reactions in this channel: {len(recent_reactions)} in last 10 messages")
        except Exception as e:
            logger.warning(f"Could not fetch recent reactions: {e}")
            
        return "\n\n".join(context_parts)
        
    async def should_react_to_message(self, message: discord.Message) -> bool:
        """Determine if the bot should react to a message using AI analysis."""
        # Don't react to bot messages (including ourselves)
        if message.author.bot:
            # Increment counter but don't react
            await self.increment_messages_since_last_reaction(message.guild.id)
            return False
            
        # Don't react in DMs
        if not message.guild:
            # Increment counter but don't react
            await self.increment_messages_since_last_reaction(message.guild.id)
            return False
            
        # Don't react if we've already reacted recently to this message
        if await self.is_recently_reacted(message.guild.id, message.id):
            # Increment counter but don't react
            await self.increment_messages_since_last_reaction(message.guild.id)
            return False
            
        # Don't react if the message is too short or uninteresting
        content = message.content.strip().lower()
        if len(content) < 3:
            # Increment counter but don't react
            await self.increment_messages_since_last_reaction(message.guild.id)
            return False
            
        # Skip common short responses
        if content in ['yes', 'no', 'yeah', 'yep', 'nope', 'ok', 'okay', 'k', 'thanks', 'thx']:
            # Increment counter but don't react
            await self.increment_messages_since_last_reaction(message.guild.id)
            return False
            
        # Skip messages that are just mentions or links
        if len(content.split()) < 2 and (content.startswith('<@') or content.startswith('http')):
            # Increment counter but don't react
            await self.increment_messages_since_last_reaction(message.guild.id)
            return False
            
        # Increment message counter for this guild
        message_count = await self.increment_message_counter(message.guild.id)
        messages_since_last = await self.increment_messages_since_last_reaction(message.guild.id)
        
        # Get server personality for context
        try:
            guild_id = str(message.guild.id)
            personality_name = await self.db_manager.get_server_personality(guild_id)
        except Exception:
            personality_name = "default"
            
        # Create prompt for AI to decide if reaction is appropriate
        prompt = f"""
You are an AI assistant that decides whether to react to Discord messages with emojis. 
Your response should be ONLY a JSON object with this format:
{{
    "should_react": true/false,
    "interest_level": "low/medium/high/very_high",
    "reason": "brief explanation"
}}

Interest levels:
- low: Not particularly interesting
- medium: Somewhat interesting
- high: Quite interesting
- very_high: Extremely interesting, thought-provoking, or emotionally significant

Consider these factors:
- Is the message interesting, funny, thought-provoking, or emotionally significant?
- Does it warrant a reaction?
- Would a reaction enhance the conversation?
- Should avoid reacting to short, common responses like "yes", "no", "yeah"
- Consider the recent conversation context

Message to analyze: "{message.content}"

Context: {await self.get_relevant_context(message)}
Messages since last reaction: {messages_since_last}

Personality: {personality_name}

Should you react to this message? Respond ONLY with the JSON format specified above.
"""
        
        try:
            response = litellm.completion(
                model="gemini/gemini-2.5-flash-lite",  # Using the same model as the bot
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            
            content = response['choices'][0]['message']['content'].strip()
            
            # Parse JSON response
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
                
            result = json.loads(content)
            should_react = result.get("should_react", False)
            interest_level = result.get("interest_level", "low")
            
            # Additional logic based on interest level and message frequency
            if interest_level == "very_high":
                # Always react to very interesting content
                return True
            elif interest_level == "high":
                # React to high interest content more frequently
                # But still consider the message count to avoid spam
                if messages_since_last >= 3:  # At least 3 messages since last reaction
                    return should_react
                elif messages_since_last >= 2:  # At least 2 messages since last reaction
                    # 70% chance to react to high interest content
                    return should_react and random.random() < 0.7
            elif interest_level == "medium":
                # React to medium interest content less frequently
                if messages_since_last >= 5:  # At least 5 messages since last reaction
                    return should_react
                elif messages_since_last >= 3:  # At least 3 messages since last reaction
                    # 40% chance to react to medium interest content
                    return should_react and random.random() < 0.4
            elif interest_level == "low":
                # Only react to low interest content very infrequently
                if messages_since_last >= 10:  # At least 10 messages since last reaction
                    # 20% chance to react to low interest content
                    return should_react and random.random() < 0.2
                    
            # Default: Don't react if none of the above conditions are met
            return False
            
        except Exception as e:
            logger.error(f"Error determining if should react: {e}")
            # Conservative approach: only react if it's been a while
            if messages_since_last >= 8:
                return random.random() < 0.1  # 10% chance if it's been a while
            return False
            
    async def get_appropriate_reaction_emojis(self, message: discord.Message) -> List[str]:
        """Get appropriate emojis to react with using AI analysis."""
        # Get server personality for context
        try:
            guild_id = str(message.guild.id)
            personality_name = await self.db_manager.get_server_personality(guild_id)
        except Exception:
            personality_name = "default"
            
        # Create prompt for AI to decide on appropriate reactions
        # Get available emojis (limit to first 30 to avoid overwhelming the model)
        available_emojis = []
        for emoji in message.guild.emojis:
            available_emojis.append(f"{emoji.name} ({emoji.id})")
            if len(available_emojis) >= 30:
                break
                
        prompt = f"""
You are an AI assistant that selects appropriate emojis to react to Discord messages.
Your response should be ONLY a JSON array of emoji identifiers.

Message: "{message.content}"

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
"""
        
        try:
            response = litellm.completion(
                model="gemini/gemini-2.5-flash-lite",  # Using the same model as the bot
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=150
            )
            
            content = response['choices'][0]['message']['content'].strip()
            
            # Parse JSON response
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
                
            emoji_names = json.loads(content)
            
            # Convert to actual emoji objects or unicode emojis
            reactions = []
            for emoji_name in emoji_names[:3]:  # Limit to 3 emojis
                # Check if it's a custom emoji name
                emoji_obj = discord.utils.get(message.guild.emojis, name=emoji_name)
                if emoji_obj:
                    reactions.append(str(emoji_obj))
                else:
                    # Assume it's a unicode emoji
                    reactions.append(emoji_name)
                    
            return reactions[:3]  # Ensure we don't exceed 3
            
        except Exception as e:
            logger.error(f"Error getting reaction emojis: {e}")
            # Fallback to simple reactions
            return ["👍"]
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for messages and react appropriately using AI."""
        # Only process messages in guilds (not DMs)
        if not message.guild:
            return
            
        # Don't react to bot messages (including ourselves)
        if message.author.bot:
            return
            
        # Check if we should react to this message (using AI)
        should_react = await self.should_react_to_message(message)
        if not should_react:
            return
            
        # Get appropriate reactions (using AI)
        reactions = await self.get_appropriate_reaction_emojis(message)
        
        if reactions:
            try:
                # Add reactions to the message
                for emoji in reactions:
                    await message.add_reaction(emoji)
                    # Small delay between reactions to avoid rate limiting
                    await asyncio.sleep(0.5)
                    
                # Mark this message as recently reacted to
                await self.add_recently_reacted(message.guild.id, message.id)
                
                # Reset the counter since we just reacted
                await self.reset_messages_since_last_reaction(message.guild.id)
                
                # Clean up old reactions periodically
                await self.clean_old_reactions(message.guild.id)
                
                logger.debug(f"Added reactions {reactions} to message {message.id} in guild {message.guild.id}")
                
            except discord.Forbidden:
                # Bot doesn't have permission to add reactions
                logger.warning(f"Bot lacks permission to add reactions in guild {message.guild.id}")
            except discord.HTTPException as e:
                # Other HTTP errors
                logger.error(f"HTTP error when adding reactions: {e}")
            except Exception as e:
                # Other errors
                logger.error(f"Unexpected error when adding reactions: {e}")

def setup(bot):
    """Setup function for the cog."""
    cog = ReactionCog(bot)
    bot.add_cog(cog)
    logger.info("ReactionCog loaded successfully")