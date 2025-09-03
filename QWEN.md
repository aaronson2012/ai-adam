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
│   │   └── personality.py    # Personality management commands
│   ├── database/             # Database management
│   │   └── manager.py        # SQLite database operations
│   ├── utils/                # Utility functions
│   │   ├── personalities.py  # Personality definitions and management
│   │   ├── emoji_analyzer.py # Emoji analysis and understanding
│   │   └── emoji_helper.py   # Basic emoji handling utilities
│   ├── main.py               # Main bot entry point
├── tests/                    # Unit tests
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

### Database Manager (src/database/manager.py)
- Uses SQLite with aiosqlite for async database operations
- Stores user memory with known facts and interaction history
- Maintains last 20 interactions per user for context
- Provides methods to get and update user memory
- Caches emoji descriptions to avoid repeated processing across bot restarts

### Personality System (src/utils/personalities.py)
- Defines personality traits, communication styles, and behavior patterns
- Includes base guidelines that apply to all personalities
- Default personality designed to be genuine, conversational, and authentic
- Provides functions to get, register, and create personalities

### Emoji Intelligence (src/utils/emoji_analyzer.py)
- Analyzes custom server emojis using vision models
- Creates enhanced prompts with emoji descriptions for better AI understanding
- Caches emoji descriptions in the database to avoid repeated processing across bot restarts
- Falls back to simple text descriptions for non-vision models

### Slash Commands (src/cogs/personality.py)
- Implements a single slash command for personality management
- `/personality` - Set the bot's personality (shows autocomplete list of available personalities)

## Configuration

The bot uses two main configuration files:
1. `config.toml` - Main configuration settings
2. `.env` - Environment variables including API keys

Key configuration options:
- Discord bot token
- Default AI model (currently set to `gemini/gemini-2.5-flash-lite`)
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

### Adding New Features
1. For new commands, add them as cogs in the `src/cogs/` directory
2. For new personalities, modify `src/utils/personalities.py`
3. For new utilities, add them in the `src/utils/` directory
4. Always add corresponding tests in the `tests/` directory

## Environment Variables
The bot supports numerous AI provider API keys through environment variables, including:
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GEMINI_API_KEY
- And many others (see .env.example for the complete list)

## Current Status
The bot is configured to use `gemini/gemini-2.5-flash-lite` as the default AI model. It implements a memory system that learns from user interactions and can adapt its personality based on server preferences.