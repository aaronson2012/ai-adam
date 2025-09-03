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
        self.is_caching = False  # Flag to indicate if caching is in progress
        
    async def start_background_caching(self, bot):
        """
        Start background caching of emojis for all guilds the bot is in.
        """
        logger.info("Starting background emoji caching")
        logger.debug(f"Bot is in {len(bot.guilds)} guilds")
        self.background_task = asyncio.create_task(self._background_emoji_caching(bot))
        logger.debug("Background emoji caching task created")
        
    async def _background_emoji_caching(self, bot):
        """
        Background task that periodically checks for emoji changes and caches new emojis.
        """
        logger.debug("Starting background emoji caching loop")
        while True:
            try:
                logger.debug("Beginning emoji caching cycle")
                # Cache emojis for all guilds
                self.is_caching = True
                logger.debug("Set is_caching flag to True")
                guild_count = len(bot.guilds)
                logger.debug(f"Caching emojis for {guild_count} guilds")
                for i, guild in enumerate(bot.guilds):
                    logger.debug(f"Processing guild {i+1}/{guild_count}: {guild.name} (ID: {guild.id})")
                    await self._cache_guild_emojis(guild)
                    # Add a small delay between processing each guild to prevent overwhelming the system
                    logger.debug("Waiting 1 second before processing next guild")
                    await asyncio.sleep(1)
                self.is_caching = False
                logger.debug("Set is_caching flag to False")
                logger.debug("Emoji caching cycle completed")
                
                # Wait for a period before next check (e.g., 30 minutes)
                logger.debug("Sleeping for 30 minutes before next caching cycle")
                await asyncio.sleep(30 * 60)  # 30 minutes
            except asyncio.CancelledError:
                logger.info("Background emoji caching task cancelled")
                self.is_caching = False
                break
            except Exception as e:
                logger.error(f"Error in background emoji caching: {e}")
                self.is_caching = False
                # Wait before retrying (increased from 1 minute to 5 minutes to prevent excessive retries)
                logger.debug("Sleeping for 5 minutes before retrying")
                await asyncio.sleep(5 * 60)  # 5 minutes
                
    async def check_emojis_for_guild(self, guild: discord.Guild):
        """
        Check for emoji changes in a specific guild (can be called on demand).
        """
        logger.debug(f"Checking emojis for guild: {guild.name} (ID: {guild.id})")
        await self._cache_guild_emojis(guild)
        logger.debug(f"Finished checking emojis for guild: {guild.name}")
                
    def is_caching_in_progress(self) -> bool:
        """
        Check if emoji caching is currently in progress.
        """
        logger.debug(f"Checking if emoji caching is in progress: {self.is_caching}")
        return self.is_caching
                
    async def _cache_guild_emojis(self, guild: discord.Guild):
        """
        Cache all emojis for a specific guild.
        """
        logger.debug(f"Caching emojis for guild: {guild.name if guild else 'None'} (ID: {guild.id if guild else 'None'})")
        if guild is None:
            logger.debug("Guild is None, returning")
            return
            
        try:
            logger.info(f"Caching emojis for guild: {guild.name} ({guild.id})")
            
            # Get current emojis
            logger.debug("Getting current emoji names")
            current_emoji_names = {emoji.name for emoji in guild.emojis}
            logger.debug(f"Found {len(current_emoji_names)} current emojis: {current_emoji_names}")
            
            # Check database for cached emojis for this guild
            logger.debug(f"Getting cached emoji keys for guild {guild.id}")
            cached_names = await self._get_cached_emoji_keys_for_guild(guild.id)
            logger.debug(f"Found {len(cached_names)} cached emojis: {cached_names}")
            
            # Find new emojis
            new_emoji_names = current_emoji_names - cached_names
            removed_emoji_names = cached_names - current_emoji_names
            logger.debug(f"New emojis to cache: {len(new_emoji_names)}")
            logger.debug(f"Removed emojis to delete: {len(removed_emoji_names)}")
            
            # Handle removed emojis
            logger.debug("Processing removed emojis")
            for emoji_name in removed_emoji_names:
                logger.debug(f"Removing cached emoji: {emoji_name}")
                await self._remove_emoji_from_cache(guild.id, emoji_name)
                
            # Handle new emojis
            logger.debug("Processing new emojis")
            new_emojis = [emoji for emoji in guild.emojis if emoji.name in new_emoji_names]
            logger.debug(f"Found {len(new_emojis)} new emojis to process")
            for emoji in new_emojis:
                try:
                    logger.debug(f"Processing new emoji: {emoji.name} (ID: {emoji.id})")
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
        logger.debug(f"Removing emoji from cache: guild_id={guild_id}, emoji_name={emoji_name}")
        try:
            await self.db_manager.remove_emoji_description(guild_id, emoji_name)
            logger.debug(f"Removed emoji from cache: {guild_id}:{emoji_name}")
        except Exception as e:
            logger.warning(f"Failed to remove emoji {emoji_name} from cache: {e}")
            
    async def _get_cached_emoji_keys_for_guild(self, guild_id: int) -> Set[str]:
        """
        Get all cached emoji names for a specific guild from the database.
        """
        logger.debug(f"Getting cached emoji keys for guild: {guild_id}")
        try:
            emoji_keys = await self.db_manager.get_all_emoji_keys_for_guild(guild_id)
            logger.debug(f"Retrieved {len(emoji_keys)} emoji keys from database")
            # Extract emoji names from keys (format: guild_id:emoji_name)
            emoji_names = {key.split(':', 1)[1] for key in emoji_keys}
            logger.debug(f"Extracted {len(emoji_names)} emoji names: {emoji_names}")
            return emoji_names
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
            self.is_caching = True
            logger.debug(f"Set is_caching flag to True for startup caching")
            guild_count = len(bot.guilds)
            logger.debug(f"Caching emojis for {guild_count} guilds on startup")
            for i, guild in enumerate(bot.guilds):
                logger.debug(f"Processing guild {i+1}/{guild_count} on startup: {guild.name} (ID: {guild.id})")
                await self._cache_guild_emojis(guild)
                # Add a small delay between processing each guild to prevent overwhelming the system
                logger.debug("Waiting 1 second before processing next guild")
                await asyncio.sleep(1)
            self.is_caching = False
            logger.debug(f"Set is_caching flag to False after startup caching")
            logger.info("Finished emoji caching on startup")
        except Exception as e:
            logger.error(f"Error during startup emoji caching: {e}")
            self.is_caching = False
            
    def cancel_background_task(self):
        """
        Cancel the background caching task.
        """
        logger.debug("Cancelling background emoji caching task")
        if self.background_task and not self.background_task.done():
            logger.debug("Background task is not done, cancelling it")
            self.background_task.cancel()
            logger.debug("Background task cancelled")
        else:
            logger.debug("Background task is already done or doesn't exist")