# src/database/manager.py

import aiosqlite
import logging
import os
import json
from typing import List, Dict
import litellm
import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    async def init_db(self):
        """Initialize the database and create tables if they don't exist."""
        logger.debug(f"Initializing database at {self.db_path}")
        async with aiosqlite.connect(self.db_path) as db:
            logger.debug("Creating user_memory table")
            # Create user_memory table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_memory (
                    user_id TEXT PRIMARY KEY,
                    known_facts TEXT, -- JSON string to store known facts
                    interaction_history TEXT, -- JSON string to store recent interactions
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            logger.debug("Creating emoji_descriptions table")
            # Create emoji_descriptions table for caching emoji analysis results
            await db.execute('''
                CREATE TABLE IF NOT EXISTS emoji_descriptions (
                    emoji_key TEXT PRIMARY KEY, -- Format: guild_id:emoji_name
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            logger.debug("Creating server_personalities table")
            # Create server_personalities table for storing server personality settings
            await db.execute('''
                CREATE TABLE IF NOT EXISTS server_personalities (
                    guild_id TEXT PRIMARY KEY,
                    personality_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            logger.debug("Creating server_memory table")
            # Create server_memory table for storing server-wide facts
            await db.execute('''
                CREATE TABLE IF NOT EXISTS server_memory (
                    guild_id TEXT PRIMARY KEY,
                    known_facts TEXT, -- JSON string to store known facts
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.commit()
            logger.info("Database initialized.")

    async def get_user_memory(self, user_id: str):
        """Retrieve memory data for a specific user."""
        logger.debug(f"Retrieving memory for user ID: {user_id}")
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT known_facts, interaction_history FROM user_memory WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    logger.debug(f"Found memory for user {user_id}")
                    # In a more complex setup, you might parse the JSON strings here
                    result = {"known_facts": row[0], "interaction_history": row[1]}
                    logger.debug(f"User memory: {result}")
                    return result
                else:
                    logger.debug(f"No memory found for user {user_id}, returning defaults")
                    # Return default/empty memory if user not found
                    return {"known_facts": "{}", "interaction_history": "[]"}

    async def extract_facts_from_interaction(self, user_message: str, ai_response: str = None, context_user_id: str = None) -> Dict[str, str]:
        """Extract facts from an interaction using an LLM."""
        logger.debug(f"Extracting facts from interaction for user ID: {context_user_id}")
        logger.debug(f"User message: {user_message}")
        logger.debug(f"AI response: {ai_response}")
        
        # Create a prompt to extract facts from the conversation
        prompt = f"""
        Extract any factual information about users from this conversation.
        Focus on personal details like name, preferences, interests, experiences, etc.
        
        Return ONLY a JSON object with key-value pairs of facts using these specific categories when applicable:
        - name: User's name
        - age: User's age
        - location: User's location
        - occupation: User's job/occupation
        - interests: Comma-separated list of user interests
        - preferences: Comma-separated list of user preferences
        - hobbies: Comma-separated list of user hobbies
        - experiences: Comma-separated list of relevant experiences
        
        Guidelines:
        - Use simple key-value pairs (e.g., "name": "John", not nested objects)
        - Avoid redundant entries (e.g., if you extract "interests": "dogs", don't also add "preferences": "dogs")
        - If no facts can be extracted, return an empty JSON object {{}}
        - Be concise and avoid lengthy values
        - ONLY extract facts that are explicitly stated or VERY strongly implied
        - If the message mentions someone else, ONLY extract facts if it's absolutely clear who is being referenced
        - If you're unsure who is being referenced, DO NOT extract facts - better to be conservative
        - If facts are clearly about the context user (ID: {context_user_id}), include them
        - If facts are about someone else but you can't clearly identify who, DO NOT include them
        - Be especially conservative about achievements, milestones, or specific numbers unless they are clearly stated
        - When in doubt, extract fewer facts rather than potentially incorrect ones
        
        User message: {user_message}
        """
        
        if ai_response:
            prompt += f"\nAI response: {ai_response}"
            
        prompt += "\n\nExtracted facts as JSON:"
        logger.debug(f"Fact extraction prompt: {prompt}")
        
        try:
            # Use the same model as configured for the bot
            # For now, we'll use a simple approach - in a real implementation, 
            # you might want to use a smaller, faster model for this task
            logger.debug("Calling LLM for fact extraction")
            response = litellm.completion(
                model="gemini/gemini-2.5-flash-lite",  # Using the same model as the bot
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            # Extract the content and parse as JSON
            content = response['choices'][0]['message']['content'].strip()
            logger.debug(f"LLM response content: {content}")
            # Remove any markdown code block formatting
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            # Parse the JSON
            facts = json.loads(content)
            logger.debug(f"Extracted facts: {facts}")
            return facts if isinstance(facts, dict) else {}
        except Exception as e:
            logger.error(f"Error extracting facts: {e}")
            return {}

    async def merge_facts(self, existing_facts: Dict[str, str], new_facts: Dict[str, str]) -> Dict[str, str]:
        """Merge new facts with existing facts, updating existing ones and adding new ones."""
        merged = existing_facts.copy()
        merged.update(new_facts)
        return merged

    async def _merge_interaction_with_history(self, history_list: list, new_interaction: dict) -> list:
        """Merge a new interaction with the history, updating existing entries with the same timestamp."""
        # Only try to merge if the new interaction has a timestamp
        if 'timestamp' in new_interaction:
            # Check if there's already an entry with the same timestamp
            existing_entry_index = None
            for i, existing_interaction in enumerate(history_list):
                if existing_interaction.get('timestamp') == new_interaction.get('timestamp'):
                    existing_entry_index = i
                    break
            
            # If we found an existing entry with the same timestamp, update it
            if existing_entry_index is not None:
                # Update the existing entry with the new interaction data
                history_list[existing_entry_index].update(new_interaction)
                return history_list
        
        # If no timestamp or no matching entry, just add as a new entry
        history_list.append(new_interaction)
        return history_list

    async def update_user_memory(self, user_id: str, user_message: str = None, ai_response: str = None, interaction: dict = None, additional_facts: dict = None, passive_mode: bool = False):
        """Update memory data for a specific user."""
        logger.debug(f"Updating memory for user ID: {user_id}")
        logger.debug(f"Passive mode: {passive_mode}")
        logger.debug(f"User message: {user_message}")
        logger.debug(f"AI response: {ai_response}")
        logger.debug(f"Additional facts: {additional_facts}")
        
        # Get current memory
        logger.debug("Retrieving current memory")
        current_memory = await self.get_user_memory(user_id)
        logger.debug(f"Current memory: {current_memory}")
        
        # Parse existing facts
        try:
            existing_facts = json.loads(current_memory['known_facts']) if current_memory['known_facts'] else {}
            logger.debug(f"Existing facts: {existing_facts}")
        except json.JSONDecodeError as e:
            logger.warning(f"Error parsing existing facts: {e}")
            existing_facts = {}
            
        # Extract new facts from the conversation if we have a user message
        new_facts = {}
        if additional_facts:
            logger.debug("Using explicitly provided facts")
            # Use explicitly provided facts
            new_facts = additional_facts
        elif user_message:
            logger.debug("Extracting facts from message")
            # Extract facts from the message
            if passive_mode:
                logger.debug("Passive mode - being conservative about fact extraction")
                # In passive mode, be more conservative about fact extraction
                # Only extract very clear, explicit facts
                new_facts = await self.extract_facts_from_interaction(user_message, ai_response, context_user_id=user_id)
            else:
                logger.debug("Active mode - normal fact extraction")
                # In active mode, extract facts normally
                new_facts = await self.extract_facts_from_interaction(user_message, ai_response, context_user_id=user_id)
        
        logger.debug(f"New facts to add: {new_facts}")
        
        # Merge facts
        logger.debug("Merging facts")
        updated_facts = await self.merge_facts(existing_facts, new_facts)
        logger.debug(f"Updated facts: {updated_facts}")
        
        # Convert facts back to JSON string
        updated_facts_json = json.dumps(updated_facts)
        logger.debug(f"Updated facts JSON: {updated_facts_json}")
        
        # Handle interaction history
        try:
            history_list = json.loads(current_memory['interaction_history'])
            logger.debug(f"Current history list: {history_list}")
        except json.JSONDecodeError as e:
            logger.warning(f"Error parsing interaction history: {e}")
            history_list = []
            
        # Handle interaction based on what parameters are provided
        if interaction:
            logger.debug("Using provided interaction")
            # Use the new merge logic to handle duplicates
            history_list = await self._merge_interaction_with_history(history_list, interaction)
        elif user_message:
            logger.debug("Creating interaction entry from message")
            # Create an interaction entry with the current timestamp
            timestamp = str(datetime.datetime.now())
            interaction_entry = {
                "user_message": user_message,
                "timestamp": timestamp
            }
            
            # Add AI response if provided
            if ai_response:
                interaction_entry["ai_response"] = ai_response
                logger.debug("Added AI response to interaction entry")
                
            # Use the merge logic to handle duplicates
            history_list = await self._merge_interaction_with_history(history_list, interaction_entry)
            logger.debug(f"History list after merge: {history_list}")
             
        # Keep last 20 interactions to allow for better context
        updated_history = json.dumps(history_list[-20:]) # Keep last 20 interactions
        logger.debug(f"Updated history JSON: {updated_history}")

        async with aiosqlite.connect(self.db_path) as db:
            logger.debug("Updating database with new memory")
            await db.execute('''
                INSERT OR REPLACE INTO user_memory (user_id, known_facts, interaction_history)
                VALUES (?, ?, ?)
            ''', (user_id, updated_facts_json, updated_history))
            await db.commit()
            logger.debug(f"Updated memory for user {user_id}")

    async def get_emoji_description(self, guild_id: int, emoji_name: str) -> str:
        """Retrieve cached description for an emoji."""
        emoji_key = f"{guild_id}:{emoji_name}"
        logger.debug(f"Retrieving emoji description for key: {emoji_key}")
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT description FROM emoji_descriptions WHERE emoji_key = ?", (emoji_key,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    logger.debug(f"Found emoji description for {emoji_key}")
                    return row[0]
                else:
                    logger.debug(f"No emoji description found for {emoji_key}")
                    return None

    async def save_emoji_description(self, guild_id: int, emoji_name: str, description: str):
        """Save emoji description to cache."""
        emoji_key = f"{guild_id}:{emoji_name}"
        logger.debug(f"Saving emoji description for key: {emoji_key}")
        logger.debug(f"Description: {description}")
        
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
        logger.debug(f"Removing emoji description for key: {emoji_key}")
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                DELETE FROM emoji_descriptions WHERE emoji_key = ?
            ''', (emoji_key,))
            await db.commit()
            logger.debug(f"Removed description for emoji {emoji_key}")
            
    async def get_all_emoji_keys_for_guild(self, guild_id: int) -> List[str]:
        """Get all emoji keys for a specific guild."""
        logger.debug(f"Retrieving all emoji keys for guild ID: {guild_id}")
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT emoji_key FROM emoji_descriptions WHERE emoji_key LIKE ?", (f"{guild_id}:%",)
            ) as cursor:
                rows = await cursor.fetchall()
                keys = [row[0] for row in rows] if rows else []
                logger.debug(f"Found {len(keys)} emoji keys for guild {guild_id}")
                return keys
            
    async def clear_user_memory(self, user_id: str):
        """Clear all memory data for a specific user."""
        logger.debug(f"Clearing memory for user ID: {user_id}")
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                DELETE FROM user_memory WHERE user_id = ?
            ''', (user_id,))
            await db.commit()
            logger.debug(f"Cleared memory for user {user_id}")
            
    async def clear_server_memory(self, guild_id: str):
        """Clear all memory data for a specific server."""
        logger.debug(f"Clearing memory for server ID: {guild_id}")
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                DELETE FROM server_memory WHERE guild_id = ?
            ''', (guild_id,))
            await db.commit()
            logger.debug(f"Cleared memory for server {guild_id}")
            
    async def get_server_memory(self, guild_id: str):
        """Retrieve memory data for a specific server."""
        logger.debug(f"Retrieving memory for server ID: {guild_id}")
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT known_facts FROM server_memory WHERE guild_id = ?", (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    logger.debug(f"Found memory for server {guild_id}")
                    result = {"known_facts": row[0]}
                    logger.debug(f"Server memory: {result}")
                    return result
                else:
                    logger.debug(f"No memory found for server {guild_id}, returning defaults")
                    # Return default/empty memory if server not found
                    return {"known_facts": "{}"}
                    
    async def update_server_memory(self, guild_id: str, user_message: str = None, ai_response: str = None, additional_facts: dict = None):
        """Update memory data for a specific server."""
        logger.debug(f"Updating memory for server ID: {guild_id}")
        logger.debug(f"User message: {user_message}")
        logger.debug(f"AI response: {ai_response}")
        logger.debug(f"Additional facts: {additional_facts}")
        
        # Get current server memory
        logger.debug("Retrieving current server memory")
        current_memory = await self.get_server_memory(guild_id)
        logger.debug(f"Current server memory: {current_memory}")
        
        # Parse existing facts
        try:
            existing_facts = json.loads(current_memory['known_facts']) if current_memory['known_facts'] else {}
            logger.debug(f"Existing server facts: {existing_facts}")
        except json.JSONDecodeError as e:
            logger.warning(f"Error parsing existing server facts: {e}")
            existing_facts = {}
            
        # Extract new facts from the conversation if we have a user message
        new_facts = {}
        if additional_facts:
            logger.debug("Using explicitly provided server facts")
            # Use explicitly provided facts
            new_facts = additional_facts
        elif user_message:
            logger.debug("Extracting server facts from message")
            # Extract server-wide facts from the message
            new_facts = await self.extract_server_facts(user_message, ai_response, guild_id)
        
        logger.debug(f"New server facts to add: {new_facts}")
        
        # Merge facts
        logger.debug("Merging server facts")
        updated_facts = await self.merge_facts(existing_facts, new_facts)
        logger.debug(f"Updated server facts: {updated_facts}")
        
        # Convert facts back to JSON string
        updated_facts_json = json.dumps(updated_facts)
        logger.debug(f"Updated server facts JSON: {updated_facts_json}")
        
        async with aiosqlite.connect(self.db_path) as db:
            logger.debug("Updating database with new server memory")
            await db.execute('''
                INSERT OR REPLACE INTO server_memory (guild_id, known_facts)
                VALUES (?, ?)
            ''', (guild_id, updated_facts_json))
            await db.commit()
            logger.debug(f"Updated memory for server {guild_id}")
            
    async def extract_server_facts(self, user_message: str, ai_response: str = None, guild_id: str = None) -> Dict[str, str]:
        """Extract server-wide facts from an interaction using an LLM."""
        logger.debug(f"Extracting server facts from interaction for guild ID: {guild_id}")
        logger.debug(f"User message: {user_message}")
        logger.debug(f"AI response: {ai_response}")
        
        # Create a prompt to extract server-wide facts from the conversation
        prompt = f"""
        Extract any factual information that is relevant to the entire server/community from this conversation.
        Focus on server details like server culture, inside jokes, server rules, community events, 
        shared experiences, server traditions, notable server milestones, etc.
        
        Return ONLY a JSON object with key-value pairs of facts using these specific categories when applicable:
        - server_culture: Description of the server's culture or vibe
        - inside_jokes: Comma-separated list of server inside jokes
        - server_rules: Comma-separated list of notable server rules
        - community_events: Comma-separated list of regular or notable server events
        - shared_experiences: Comma-separated list of shared experiences among server members
        - server_traditions: Comma-separated list of server traditions or customs
        - notable_milestones: Comma-separated list of notable server milestones or achievements
        - server_topics: Comma-separated list of topics frequently discussed in the server
        
        Guidelines:
        - Use simple key-value pairs (e.g., "server_culture": "gaming focused", not nested objects)
        - Avoid redundant entries
        - If no facts can be extracted, return an empty JSON object {{}}
        - Be concise and avoid lengthy values
        - ONLY extract facts that are explicitly stated or VERY strongly implied to be server-wide
        - Focus on things that apply to the server/community as a whole, not individual users
        - Be especially conservative - it's better to extract nothing than potentially incorrect server-wide facts
        - When in doubt, extract fewer facts rather than potentially incorrect ones
        
        User message: {user_message}
        """
        
        if ai_response:
            prompt += f"\nAI response: {ai_response}"
            
        prompt += "\n\nExtracted facts as JSON:"
        logger.debug(f"Server fact extraction prompt: {prompt}")
        
        try:
            # Use the same model as configured for the bot
            logger.debug("Calling LLM for server fact extraction")
            response = litellm.completion(
                model="gemini/gemini-2.5-flash-lite",  # Using the same model as the bot
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            # Extract the content and parse as JSON
            content = response['choices'][0]['message']['content'].strip()
            logger.debug(f"LLM response content: {content}")
            # Remove any markdown code block formatting
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            # Parse the JSON
            facts = json.loads(content)
            logger.debug(f"Extracted server facts: {facts}")
            return facts if isinstance(facts, dict) else {}
        except Exception as e:
            logger.error(f"Error extracting server facts: {e}")
            return {}

    async def get_server_personality(self, guild_id: str) -> str:
        """Retrieve the personality setting for a server."""
        logger.debug(f"Retrieving personality for guild ID: {guild_id}")
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT personality_name FROM server_personalities WHERE guild_id = ?", (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    logger.debug(f"Found personality for guild {guild_id}: {row[0]}")
                    return row[0]
                else:
                    logger.debug(f"No personality found for guild {guild_id}, returning default")
                    return "default"  # Default personality

    async def set_server_personality(self, guild_id: str, personality_name: str):
        """Save the personality setting for a server."""
        logger.debug(f"Setting personality '{personality_name}' for guild ID: {guild_id}")
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO server_personalities (guild_id, personality_name, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (guild_id, personality_name))
            await db.commit()
            logger.debug(f"Set personality '{personality_name}' for guild {guild_id}")