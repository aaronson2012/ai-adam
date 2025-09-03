# src/database/manager.py

import aiosqlite
import logging
import os
import json

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    async def init_db(self):
        """Initialize the database and create tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_memory (
                    user_id TEXT PRIMARY KEY,
                    known_facts TEXT, -- JSON string to store known facts
                    interaction_history TEXT, -- JSON string to store recent interactions
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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