# tests/test_imports.py

import sys
import os

# Add the project root directory to the Python path so imports work correctly
# when running this script directly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Now try to import the main modules of the project
try:
    import src.main
    print("✅ src.main imported successfully.")
except ImportError as e:
    print(f"❌ Failed to import src.main: {e}")

try:
    from src.database.manager import DatabaseManager
    print("✅ src.database.manager imported successfully.")
except ImportError as e:
    print(f"❌ Failed to import src.database.manager: {e}")

try:
    from src.utils.personalities import get_personality
    print("✅ src.utils.personalities imported successfully.")
except ImportError as e:
    print(f"❌ Failed to import src.utils.personalities: {e}")

try:
    from src.utils.emoji_helper import get_server_emojis
    print("✅ src.utils.emoji_helper imported successfully.")
except ImportError as e:
    print(f"❌ Failed to import src.utils.emoji_helper: {e}")

try:
    from src.utils.emoji_analyzer import create_enhanced_emoji_prompt
    print("✅ src.utils.emoji_analyzer imported successfully.")
except ImportError as e:
    print(f"❌ Failed to import src.utils.emoji_analyzer: {e}")

# Add other key modules as the project grows