# AI-Adam Project Context

This is a Python-based Discord bot named AI-Adam that uses AI to provide natural, conversational responses. The bot is designed to learn from interactions and remember users to provide personalized responses over time.

## Project Overview

AI-Adam is a Discord bot with the following key features:
- Natural Language Processing using LiteLLM to interface with various AI models
- Configurable personalities that change the bot's behavior and responses
- Memory learning system that remembers user interactions
- Emoji intelligence that analyzes and understands server emojis
- Slash commands for easy bot interaction
- Support for numerous LLM providers through LiteLLM
- Server-specific customization with per-server personality settings
- Memory management with appropriate permissions
- Automatic command synchronization on startup
- Background emoji caching to prevent duplicate processing

## Technology Stack

- **Language**: Python 3.11+
- **Discord Library**: Pycord (py-cord==2.6.1)
- **AI Interface**: LiteLLM (litellm==1.74.15)
- **Database**: SQLite with aiosqlite (aiosqlite==0.20.0)
- **Configuration**: TOML format with python-dotenv (python-dotenv==1.0.1)
- **Testing**: pytest (pytest==8.3.2) with pytest-asyncio (pytest-asyncio==0.23.7)

## Project Structure

```
ai-adam/
├── src/
│   ├── cogs/                 # Discord bot commands and features
│   │   ├── personality.py    # Personality management commands
│   │   ├── memory.py         # Memory management commands
│   │   └── reactions.py      # Automatic reaction functionality
│   ├── database/             # Database management
│   │   └── manager.py        # SQLite database operations
│   ├── utils/                # Utility functions
│   │   ├── personalities.py  # Personality definitions and management
│   │   ├── emoji_analyzer.py # Emoji analysis and understanding
│   │   ├── emoji_helper.py   # Basic emoji handling utilities
│   │   └── emoji_manager.py  # Emoji caching and management
│   ├── personalities/        # Personality definition files
│   │   ├── base_guidelines.toml  # Base guidelines for all personalities
│   │   ├── default.toml      # Default personality
│   │   ├── tech_expert.toml  # Technical expert personality
│   │   ├── memer.toml        # Meme-focused personality
│   │   ├── karen.toml        # Karen personality
│   │   ├── noughties_memer.toml # 2000s internet culture personality
│   │   ├── reddit_mod.toml   # Reddit/Discord moderator personality
│   │   └── tifa_lockhart.toml # Tifa Lockhart character personality
│   ├── main.py               # Main bot entry point
├── tests/                    # All tests organized by type
│   ├── unit/                 # Unit tests for individual components
│   ├── integration/          # Integration tests for component interactions
│   ├── e2e/                  # End-to-end tests for complete workflows
├── data/                     # Database files
│   └── ai_adam.db            # SQLite database
├── config.example.toml       # Example configuration file
├── config.toml               # Actual configuration file
├── .env.example              # Example environment variables
├── .env                      # Actual environment variables (git-ignored)
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Project metadata and dependencies
└── README.md                 # Project documentation
```

## Key Components

### Main Bot (src/main.py)
- Entry point for the Discord bot
- Handles configuration loading from TOML files and environment variables
- Manages Discord intents and event listeners
- Integrates with LiteLLM for AI interactions
- Uses DatabaseManager for user memory storage
- Loads personality system for customized responses
- Implements emoji analysis for contextual understanding
- Automatically syncs commands on startup
- Manages background emoji caching

### Database Manager (src/database/manager.py)
- Uses SQLite with aiosqlite for async database operations
- Stores user memory with known facts and interaction history
- Maintains last 20 interactions per user for context
- Provides methods to get and update user memory
- Provides methods to clear user and server memory
- Caches emoji descriptions to avoid repeated processing across bot restarts
- Stores server personality settings
- Stores server-wide memory for community facts

### Personality System (src/utils/personalities.py)
- Defines personality traits, communication styles, and behavior patterns
- Includes base guidelines that apply to all personalities
- Default personality designed to be genuine, conversational, and authentic
- Provides functions to get, register, and create personalities
- Loads personalities from TOML files in the personalities directory

### Emoji Intelligence (src/utils/emoji_analyzer.py)
- Analyzes custom server emojis using vision models
- Creates enhanced prompts with emoji descriptions for better AI understanding
- Caches emoji descriptions in the database to avoid repeated processing across bot restarts
- Falls back to simple text descriptions for non-vision models

### Emoji Manager (src/utils/emoji_manager.py)
- Manages emoji caching for all servers
- Runs background tasks to periodically check for new emojis
- Caches emojis on startup
- Prevents duplicate caching operations

### Slash Commands

#### Personality Commands (src/cogs/personality.py)
- Implements slash command for personality management
- `/personality` - Set the bot's personality (shows autocomplete list of available personalities)
- Requires "Manage Server" permissions to change personality

#### Memory Commands (src/cogs/memory.py)
- Implements slash command for memory management
- `/memory` - Retrieve or clear memory information for users or servers
- Supports retrieving memory for specific users
- Supports clearing memory for users or servers with confirmation
- Shows memory information in formatted embeds
- All responses are ephemeral for privacy

#### Reactions (src/cogs/reactions.py)
- Automatically reacts to messages using AI analysis
- Determines when and how to react based on message content
- Uses personality context for appropriate reactions
- Avoids spam with intelligent reaction frequency controls

## Configuration

The bot uses two main configuration files:
1. `config.toml` - Main configuration settings
2. `.env` - Environment variables including API keys

Key configuration options:
- Discord bot token
- Default AI model (currently set to `gemini/gemini-2.5-flash-lite`)
- Vision model for emoji analysis (optional)
- Database path
- Logging level

## Development Workflow

### Building and Running
1. Create a virtual environment: `python -m venv .venv`
2. Activate it: `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Configure the bot by copying example files and adding your keys
5. Run the bot: `python src/main.py`

### Testing
- Run tests with: `pytest`
- Tests use pytest-asyncio for async testing
- Database tests use temporary files for isolation
- Tests are organized into unit, integration, and end-to-end categories

### Adding New Features
1. For new commands, add them as cogs in the `src/cogs/` directory
2. For new personalities, add TOML files in the `src/personalities/` directory
3. For new utilities, add them in the `src/utils/` directory
4. Always add corresponding tests in the `tests/` directory

## Environment Variables
The bot supports numerous AI provider API keys through environment variables, including:
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GEMINI_API_KEY
- And many others (see .env.example for the complete list)

## Current Status
The bot is configured to use `gemini/gemini-2.5-flash-lite` as the default AI model. It implements a memory system that learns from user interactions and can adapt its personality based on server preferences. The bot has three main slash commands: `/personality` for setting the bot's personality, `/memory` for viewing or clearing user/server memory, and automatic reactions that enhance conversations with appropriate emojis.

## Recent Improvements
- Enhanced memory command with user parameter to retrieve memory for specific users
- Enhanced memory command with clear functionality for users and servers
- Improved emoji handling with better caching and reduced API usage
- Added automatic reaction system that intelligently reacts to messages
- Better error handling and logging throughout the codebase
- More comprehensive test coverage organized by type
- Automatic command synchronization on bot startup
- Background emoji caching to prevent duplicate processing
- Server-wide memory system for community facts
- Comprehensive integration testing with multiple user scenarios