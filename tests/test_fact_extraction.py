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
async def test_extract_facts_from_interaction():
    """Test that facts are correctly extracted from an interaction."""
    # Create a database manager with a temporary file
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    db_manager = DatabaseManager(temp_db.name)
    
    # Mock the LLM response
    mock_response = {
        'choices': [{
            'message': {
                'content': '{"name": "John", "interests": "AI and robotics"}'
            }
        }]
    }
    
    with patch('src.database.manager.litellm.completion', return_value=mock_response):
        facts = await db_manager.extract_facts_from_interaction(
            "Hi, I'm John. I'm really interested in AI and robotics.",
            "Nice to meet you John! AI and robotics are fascinating fields."
        )
        
        assert isinstance(facts, dict)
        assert "name" in facts
        assert facts["name"] == "John"
        assert "interests" in facts
        assert "AI and robotics" in facts["interests"]
    
    # Clean up
    os.unlink(temp_db.name)

@pytest.mark.asyncio
async def test_merge_facts():
    """Test that facts are correctly merged."""
    # Create a database manager with a temporary file
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    db_manager = DatabaseManager(temp_db.name)
    
    existing_facts = {"name": "John", "age": "30"}
    new_facts = {"name": "Jonathan", "interests": "AI"}
    
    merged_facts = await db_manager.merge_facts(existing_facts, new_facts)
    
    # Should update existing facts and add new ones
    assert merged_facts["name"] == "Jonathan"  # Updated
    assert merged_facts["age"] == "30"         # Preserved
    assert merged_facts["interests"] == "AI"   # Added
    
    # Clean up
    os.unlink(temp_db.name)

@pytest.mark.asyncio
async def test_update_user_memory_with_fact_extraction(db_manager):
    """Test that user memory is updated with fact extraction."""
    # Mock the LLM response for fact extraction
    mock_response = {
        'choices': [{
            'message': {
                'content': '{"name": "Alice", "favorite_color": "blue"}'
            }
        }]
    }
    
    with patch('src.database.manager.litellm.completion', return_value=mock_response):
        # Update user memory with a conversation
        await db_manager.update_user_memory(
            "12345",
            user_message="Hi, I'm Alice and my favorite color is blue.",
            ai_response="Nice to meet you Alice!",
            interaction={
                "user_message": "Hi, I'm Alice and my favorite color is blue.",
                "ai_response": "Nice to meet you Alice!",
                "timestamp": "2023-01-01T12:00:00"
            }
        )
        
        # Retrieve the user memory
        memory = await db_manager.get_user_memory("12345")
        
        # Check that facts were extracted and stored
        facts = json.loads(memory["known_facts"])
        assert "name" in facts
        assert facts["name"] == "Alice"
        assert "favorite_color" in facts
        assert facts["favorite_color"] == "blue"
        
        # Check that interaction history was stored
        history = json.loads(memory["interaction_history"])
        assert len(history) == 1
        assert history[0]["user_message"] == "Hi, I'm Alice and my favorite color is blue."

@pytest.mark.asyncio
async def test_extract_facts_avoid_redundancy():
    """Test that fact extraction avoids redundant entries."""
    # Create a database manager with a temporary file
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    db_manager = DatabaseManager(temp_db.name)
    
    # Mock the LLM response that might create redundancy
    mock_response = {
        'choices': [{
            'message': {
                'content': '{"interests": "dogs", "preferences": "animals"}'
            }
        }]
    }
    
    with patch('src.database.manager.litellm.completion', return_value=mock_response):
        facts = await db_manager.extract_facts_from_interaction(
            "I like dogs",
            "That's great! Dogs are wonderful companions."
        )
        
        assert isinstance(facts, dict)
        # Should have extracted facts without creating overly complex nested structures
        assert "interests" in facts or "preferences" in facts
        # Should not have nested objects
        for key, value in facts.items():
            assert not isinstance(value, dict), f"Value for key '{key}' should not be a dict: {value}"
    
    # Clean up
    os.unlink(temp_db.name)