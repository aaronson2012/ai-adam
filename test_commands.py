import sys
import os

# Add the src directory to the path
sys.path.insert(0, 'src')

# Test importing the personality cog
import src.cogs.personality as personality_cog
print('Personality cog imported successfully')

# Test the setup function
class MockBot:
    def __init__(self):
        self.commands = []
        self.pending_application_commands = []
    
    def slash_command(self, name, description):
        def decorator(func):
            cmd = {'name': name, 'description': description, 'func': func}
            self.commands.append(cmd)
            self.pending_application_commands.append(cmd)
            print(f'Registered command: {name} - {description}')
            return func
        return decorator

mock_bot = MockBot()
personality_cog.setup(mock_bot)
print(f'Total commands registered: {len(mock_bot.commands)}')

# Test get_available_personalities
from src.utils.personalities import get_available_personalities
personalities = get_available_personalities()
print(f'Available personalities: {personalities}')