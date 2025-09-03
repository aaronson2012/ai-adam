# src/utils/emoji_manager.py

import asyncio
import logging
import discord
from typing import Dict, List, Set
from src.utils.emoji_analyzer import get_custom_emoji_description, analyze_server_emojis
from src.database.manager import DatabaseManager

logger = logging.getLogger(__name__)

class EmojiManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.cached_emojis: Dict[int, Set[str]] = {}  # guild_id -> set of emoji names
        self.background_task = None
        
    async def start_background_caching(self, bot):
        """
        Start background caching of emojis for all guilds the bot is in.
        """
        logger.info("Starting background emoji caching")
        self.background_task = asyncio.create_task(self._background_emoji_caching(bot))
        
    async def _background_emoji_caching(self, bot):
        """
        Background task that periodically checks for emoji changes and caches new emojis.
        """
        while True:
            try:
                # Cache emojis for all guilds
                for guild in bot.guilds:
                    await self._cache_guild_emojis(guild)
                
                # Wait for a period before next check (e.g., 30 minutes)
                await asyncio.sleep(30 * 60)  # 30 minutes
            except asyncio.CancelledError:
                logger.info("Background emoji caching task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in background emoji caching: {e}")
                # Wait before retrying
                await asyncio.sleep(60)  # 1 minute
                
    async def check_emojis_for_guild(self, guild: discord.Guild):
        """
        Check for emoji changes in a specific guild (can be called on demand).
        """
        await self._cache_guild_emojis(guild)
                
    async def _cache_guild_emojis(self, guild: discord.Guild):
        """
        Cache all emojis for a specific guild.
        """
        if guild is None:
            return
            
        try:
            logger.info(f"Caching emojis for guild: {guild.name} ({guild.id})")
            
            # Get current emojis
            current_emoji_names = {emoji.name for emoji in guild.emojis}
            
            # Check database for cached emojis for this guild
            cached_names = await self._get_cached_emoji_keys_for_guild(guild.id)
            
            # Find new emojis
            new_emoji_names = current_emoji_names - cached_names
            removed_emoji_names = cached_names - current_emoji_names
            
            # Handle removed emojis
            for emoji_name in removed_emoji_names:
                await self._remove_emoji_from_cache(guild.id, emoji_name)
                
            # Handle new emojis
            new_emojis = [emoji for emoji in guild.emojis if emoji.name in new_emoji_names]
            for emoji in new_emojis:
                try:
                    await get_custom_emoji_description(emoji, self.db_manager)
                    logger.debug(f"Cached emoji: {emoji.name}")
                except Exception as e:
                    logger.warning(f"Failed to cache emoji {emoji.name}: {e}")
            
            logger.info(f"Finished caching emojis for guild: {guild.name}. "
                       f"New: {len(new_emojis)}, Removed: {len(removed_emoji_names)}")
                       
        except Exception as e:
            logger.error(f"Error caching emojis for guild {guild.id}: {e}")
            
    async def _remove_emoji_from_cache(self, guild_id: int, emoji_name: str):
        """
        Remove an emoji from the database cache.
        """
        try:
            await self.db_manager.remove_emoji_description(guild_id, emoji_name)
            logger.debug(f"Removed emoji from cache: {guild_id}:{emoji_name}")
        except Exception as e:
            logger.warning(f"Failed to remove emoji {emoji_name} from cache: {e}")
            
    async def _get_cached_emoji_keys_for_guild(self, guild_id: int) -> Set[str]:
        """
        Get all cached emoji names for a specific guild from the database.
        """
        try:
            emoji_keys = await self.db_manager.get_all_emoji_keys_for_guild(guild_id)
            # Extract emoji names from keys (format: guild_id:emoji_name)
            return {key.split(':', 1)[1] for key in emoji_keys}
        except Exception as e:
            logger.warning(f"Failed to get cached emoji keys for guild {guild_id}: {e}")
            return set()
            
    async def cache_emojis_on_startup(self, bot):
        """
        Cache all emojis for all guilds when the bot starts up.
        This runs in the background and doesn't block the bot.
        """
        logger.info("Starting emoji caching on startup")
        try:
            for guild in bot.guilds:
                await self._cache_guild_emojis(guild)
            logger.info("Finished emoji caching on startup")
        except Exception as e:
            logger.error(f"Error during startup emoji caching: {e}")
            
    def cancel_background_task(self):
        """
        Cancel the background caching task.
        """
        if self.background_task and not self.background_task.done():
            self.background_task.cancel()