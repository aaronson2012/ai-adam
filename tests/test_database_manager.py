import sys
import os
import asyncio
import tempfile
import pytest
import pytest_asyncio

# Add the 'src' directory to the Python path so imports work correctly
# when running this script directly.
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
async def test_init_db(db_manager):
    # The database should be initialized without errors
    # Since init_db is called in the fixture, we just verify it worked
    assert db_manager is not None

@pytest.mark.asyncio
async def test_get_user_memory_new_user(db_manager):
    # Get memory for a user that doesn't exist yet
    user_memory = await db_manager.get_user_memory("123456789")
    
    # Should return default empty memory
    assert user_memory == {"known_facts": "{}", "interaction_history": "[]"}

@pytest.mark.asyncio
async def test_update_and_get_user_memory(db_manager):
    user_id = "987654321"
    
    # Update user memory with a new interaction
    interaction = {"user_message": "Hello", "ai_response": "Hi there!"}
    await db_manager.update_user_memory(user_id, interaction=interaction)
    
    # Retrieve the user's memory
    user_memory = await db_manager.get_user_memory(user_id)
    
    # Verify the memory was updated correctly
    assert user_memory["known_facts"] == "{}"  # Default value for known_facts
    assert "interaction_history" in user_memory
    
    # Parse the interaction history and check it
    import json
    history = json.loads(user_memory["interaction_history"])
    assert len(history) == 1
    assert history[0] == interaction

@pytest.mark.asyncio
async def test_update_user_memory_multiple_interactions(db_manager):
    user_id = "111222333"
    
    # Add multiple interactions
    interactions = [
        {"user_message": "Hello", "ai_response": "Hi there!"},
        {"user_message": "How are you?", "ai_response": "I'm doing well, thanks!"},
        {"user_message": "What's your name?", "ai_response": "I'm AI Adam."}
    ]
    
    for interaction in interactions:
        await db_manager.update_user_memory(user_id, interaction=interaction)
    
    # Retrieve the user's memory
    user_memory = await db_manager.get_user_memory(user_id)
    
    # Parse the interaction history and check it
    import json
    history = json.loads(user_memory["interaction_history"])
    
    # Should have all three interactions
    assert len(history) == 3
    assert history == interactions

@pytest.mark.asyncio
async def test_update_user_memory_limit_interactions(db_manager):
    user_id = "444555666"
    
    # Add more than 20 interactions
    for i in range(25):
        interaction = {"user_message": f"Message {i}", "ai_response": f"Response {i}"}
        await db_manager.update_user_memory(user_id, interaction=interaction)
    
    # Retrieve the user's memory
    user_memory = await db_manager.get_user_memory(user_id)
    
    # Parse the interaction history and check it
    import json
    history = json.loads(user_memory["interaction_history"])
    
    # Should only have the last 20 interactions
    assert len(history) == 20
    
    # Check that these are the last 20 interactions (5-24)
    for i, interaction in enumerate(history):
        expected_index = i + 5  # 25 total, last 20 means indices 5-24
        assert interaction == {"user_message": f"Message {expected_index}", "ai_response": f"Response {expected_index}"}