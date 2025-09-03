# src/database/manager.py

import aiosqlite
import logging
import os
import json
from typing import List

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    async def init_db(self):
        """Initialize the database and create tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            # Create user_memory table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_memory (
                    user_id TEXT PRIMARY KEY,
                    known_facts TEXT, -- JSON string to store known facts
                    interaction_history TEXT, -- JSON string to store recent interactions
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create emoji_descriptions table for caching emoji analysis results
            await db.execute('''
                CREATE TABLE IF NOT EXISTS emoji_descriptions (
                    emoji_key TEXT PRIMARY KEY, -- Format: guild_id:emoji_name
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create server_personalities table for storing server personality settings
            await db.execute('''
                CREATE TABLE IF NOT EXISTS server_personalities (
                    guild_id TEXT PRIMARY KEY,
                    personality_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.commit()
            logger.info("Database initialized.")

    async def get_user_memory(self, user_id: str):
        """Retrieve memory data for a specific user."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT known_facts, interaction_history FROM user_memory WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    # In a more complex setup, you might parse the JSON strings here
                    return {"known_facts": row[0], "interaction_history": row[1]}
                else:
                    # Return default/empty memory if user not found
                    return {"known_facts": "{}", "interaction_history": "[]"}

    async def update_user_memory(self, user_id: str, new_fact: str = None, interaction: dict = None):
        """Update memory data for a specific user."""
        # This is a simplified example. A real implementation would need more robust logic
        # to manage known facts and interaction history (e.g., appending, deduplication).
        # For now, it just replaces or inserts basic data.
        current_memory = await self.get_user_memory(user_id)
        
        # Handle known facts (for future expansion)
        updated_facts = new_fact or current_memory['known_facts']
        
        # Handle interaction history
        try:
            history_list = json.loads(current_memory['interaction_history'])
        except json.JSONDecodeError:
            history_list = []
            
        if interaction:
             history_list.append(interaction)
             
        # Keep last 20 interactions to allow for better context
        updated_history = json.dumps(history_list[-20:]) # Keep last 20 interactions

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO user_memory (user_id, known_facts, interaction_history)
                VALUES (?, ?, ?)
            ''', (user_id, updated_facts, updated_history))
            await db.commit()
            logger.debug(f"Updated memory for user {user_id}")

    async def get_emoji_description(self, guild_id: int, emoji_name: str) -> str:
        """Retrieve cached description for an emoji."""
        emoji_key = f"{guild_id}:{emoji_name}"
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT description FROM emoji_descriptions WHERE emoji_key = ?", (emoji_key,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0]
                else:
                    return None

    async def save_emoji_description(self, guild_id: int, emoji_name: str, description: str):
        """Save emoji description to cache."""
        emoji_key = f"{guild_id}:{emoji_name}"
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO emoji_descriptions (emoji_key, description, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (emoji_key, description))
            await db.commit()
            logger.debug(f"Saved description for emoji {emoji_key}")
            
    async def remove_emoji_description(self, guild_id: int, emoji_name: str):
        """Remove emoji description from cache."""
        emoji_key = f"{guild_id}:{emoji_name}"
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                DELETE FROM emoji_descriptions WHERE emoji_key = ?
            ''', (emoji_key,))
            await db.commit()
            logger.debug(f"Removed description for emoji {emoji_key}")
            
    async def get_all_emoji_keys_for_guild(self, guild_id: int) -> List[str]:
        """Get all emoji keys for a specific guild."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT emoji_key FROM emoji_descriptions WHERE emoji_key LIKE ?", (f"{guild_id}:%",)
            ) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows] if rows else []
            
    async def get_server_personality(self, guild_id: str) -> str:
        """Retrieve the personality setting for a server."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT personality_name FROM server_personalities WHERE guild_id = ?", (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0]
                else:
                    return "default"  # Default personality

    async def set_server_personality(self, guild_id: str, personality_name: str):
        """Save the personality setting for a server."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO server_personalities (guild_id, personality_name, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (guild_id, personality_name))
            await db.commit()
            logger.debug(f"Set personality '{personality_name}' for guild {guild_id}")