import sys
import os
import pytest
import tempfile
from unittest.mock import patch

# Add the 'src' directory to the Python path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_config_loading():
    """Test that the config file is loaded correctly."""
    # We'll test this by importing the main module and checking the config
    import src.main
    
    # The config should be a dictionary
    assert isinstance(src.main.config, dict)
    
    # Should have the expected sections
    assert 'discord' in src.main.config
    assert 'ai' in src.main.config
    assert 'database' in src.main.config
    assert 'logging' in src.main.config
    
    # Check some specific values
    assert 'default_model' in src.main.config['ai']
    assert 'path' in src.main.config['database']
    assert 'level' in src.main.config['logging']

def test_discord_token_loading():
    """Test that the Discord token is loaded correctly."""
    import src.main
    
    # The DISCORD_TOKEN should be set (from our .env file)
    assert src.main.DISCORD_TOKEN is not None
    assert isinstance(src.main.DISCORD_TOKEN, str)
    assert len(src.main.DISCORD_TOKEN) > 0