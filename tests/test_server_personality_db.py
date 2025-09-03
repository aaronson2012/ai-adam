"""
Tests for the server personality database functionality.
"""

import sys
import os
import pytest
import asyncio
import tempfile
import aiosqlite

# Add the 'src' directory to the Python path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_server_personality_db_functions():
    """Test that the server personality database functions work correctly."""
    from src.database.manager import DatabaseManager
    
    # Create a temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager(db_path)
        
        # Create a new event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize the database
            loop.run_until_complete(db_manager.init_db())
            
            # Test setting and getting server personality
            guild_id = "123456789"
            personality_name = "tech_expert"
            
            # Initially should return default
            result = loop.run_until_complete(db_manager.get_server_personality(guild_id))
            assert result == "default"
            
            # Set a personality
            loop.run_until_complete(db_manager.set_server_personality(guild_id, personality_name))
            
            # Should now return the set personality
            result = loop.run_until_complete(db_manager.get_server_personality(guild_id))
            assert result == personality_name
            
            # Test updating personality
            new_personality = "default"
            loop.run_until_complete(db_manager.set_server_personality(guild_id, new_personality))
            
            # Should now return the updated personality
            result = loop.run_until_complete(db_manager.get_server_personality(guild_id))
            assert result == new_personality
            
        finally:
            loop.close()
    finally:
        # Clean up the temporary database file
        os.unlink(db_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])