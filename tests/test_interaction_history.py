import sys
import os
import pytest
import pytest_asyncio
import json
import tempfile
from unittest.mock import AsyncMock, Mock, patch

# Add the 'src' directory to the Python path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.manager import DatabaseManager

@pytest_asyncio.fixture
async def db_manager():
    # Create a temporary database file for testing
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    
    # Initialize the database manager with the temporary database
    manager = DatabaseManager(temp_db.name)
    
    # Initialize the database
    await manager.init_db()
    
    yield manager
    
    # Clean up the temporary database file after tests
    os.unlink(temp_db.name)

@pytest.mark.asyncio
async def test_update_user_memory_no_duplicates(db_manager):
    """Test that user memory updates don't create duplicate entries with the same timestamp."""
    user_id = "12345"
    timestamp = "2023-01-01T12:00:00"
    
    # First, add an interaction with just the user message
    interaction1 = {
        "user_message": "Hello there!",
        "timestamp": timestamp
    }
    await db_manager.update_user_memory(
        user_id, 
        user_message="Hello there!", 
        interaction=interaction1
    )
    
    # Then, add an interaction with the same timestamp but including AI response
    interaction2 = {
        "user_message": "Hello there!",
        "ai_response": "Hi! How can I help you?",
        "timestamp": timestamp
    }
    await db_manager.update_user_memory(
        user_id, 
        user_message="Hello there!", 
        ai_response="Hi! How can I help you?", 
        interaction=interaction2
    )
    
    # Retrieve the user memory
    memory = await db_manager.get_user_memory(user_id)
    
    # Check that there's only one interaction in the history
    history = json.loads(memory["interaction_history"])
    assert len(history) == 1
    
    # Check that the single interaction has both user message and AI response
    interaction = history[0]
    assert interaction["user_message"] == "Hello there!"
    assert interaction["ai_response"] == "Hi! How can I help you?"
    assert interaction["timestamp"] == timestamp

@pytest.mark.asyncio
async def test_update_user_memory_separate_timestamps(db_manager):
    """Test that interactions with different timestamps are stored separately."""
    user_id = "12345"
    timestamp1 = "2023-01-01T12:00:00"
    timestamp2 = "2023-01-01T12:01:00"
    
    # Add first interaction
    interaction1 = {
        "user_message": "Hello there!",
        "timestamp": timestamp1
    }
    await db_manager.update_user_memory(
        user_id, 
        user_message="Hello there!", 
        interaction=interaction1
    )
    
    # Add second interaction with different timestamp
    interaction2 = {
        "user_message": "How are you?",
        "ai_response": "I'm doing well, thanks!",
        "timestamp": timestamp2
    }
    await db_manager.update_user_memory(
        user_id, 
        user_message="How are you?", 
        ai_response="I'm doing well, thanks!", 
        interaction=interaction2
    )
    
    # Retrieve the user memory
    memory = await db_manager.get_user_memory(user_id)
    
    # Check that there are two interactions in the history
    history = json.loads(memory["interaction_history"])
    assert len(history) == 2
    
    # Check that both interactions are stored correctly
    assert history[0]["user_message"] == "Hello there!"
    assert "ai_response" not in history[0]
    assert history[0]["timestamp"] == timestamp1
    
    assert history[1]["user_message"] == "How are you?"
    assert history[1]["ai_response"] == "I'm doing well, thanks!"
    assert history[1]["timestamp"] == timestamp2