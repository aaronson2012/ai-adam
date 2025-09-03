# AI-Adam

A Discord bot with AI chat capabilities and learning features. AI-Adam is designed to be a natural, conversational AI assistant that responds like an actual human while learning from interactions to provide personalized responses.

## Features

- **Natural Language Processing**: Uses LiteLLM to interface with various AI models (OpenAI, Anthropic, Google, etc.)
- **Personality System**: Configurable personalities that change the bot's behavior and responses
- **Memory Learning**: Remembers user interactions to provide personalized responses over time
- **Emoji Intelligence**: Analyzes and understands server emojis for more contextual responses
- **Slash Commands**: Easy-to-use slash commands for bot interaction
- **Multi-model Support**: Works with numerous LLM providers through LiteLLM

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
└── README.md                 # This file
```

## Setup

### Prerequisites

- Python 3.11+
- A Discord account and a bot token from the [Discord Developer Portal](https://discord.com/developers/applications)
- API keys for your chosen AI provider(s) (OpenAI, Anthropic, etc.)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-adam.git
   cd ai-adam
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

1. Copy the example configuration files:
   ```bash
   cp config.example.toml config.toml
   cp .env.example .env
   ```

2. Edit `config.toml` to set your preferences:
   - Set your default AI model
   - Adjust logging levels
   - Configure database path

3. Edit `.env` to add your API keys:
   - Add your `DISCORD_TOKEN`
   - Add your AI provider API keys (OpenAI, Anthropic, etc.)

### Running the Bot

```bash
python src/main.py
```

## Usage

### Basic Interaction

- Mention the bot in a message to get a response: `@AI-Adam Hello!`
- Send a direct message to the bot for private conversation
- The bot learns from all messages it can see, even when not directly responding

### Slash Commands

- `/personality_list` - List all available personalities
- `/personality_current` - Show the current personality
- `/personality_set <name>` - Set the bot's personality (requires Manage Server permission)

## Personalities

AI-Adam supports different personalities that change how the bot behaves and responds. Personalities are defined in `src/utils/personalities.py` and can be customized to match your server's needs.

Each personality includes:
- A name and description
- Personality traits
- Communication style guidelines
- Behavior patterns

### Default Personality

The default personality is designed to be:
- Genuine and authentic
- Conversational and relatable
- Straightforward and honest
- Witty and occasionally humorous
- Curious and engaged
- Appropriately casual

## Database

AI-Adam uses SQLite for storing user memory and interaction history. The database schema includes:

- `user_memory` table with:
  - `user_id`: Discord user ID
  - `known_facts`: JSON string of facts learned about the user
  - `interaction_history`: JSON string of recent interactions (last 20)
  - `last_updated`: Timestamp of last update

## Emoji Intelligence

AI-Adam can understand and use server-specific emojis. The bot:

1. Analyzes custom server emojis
2. Uses vision models to understand what emojis represent (when available)
3. Incorporates emoji understanding into conversations
4. Uses emojis naturally in responses (1-2 per message maximum)

## Supported AI Providers

Through LiteLLM, AI-Adam supports numerous AI providers:

- OpenAI (GPT-3.5, GPT-4, etc.)
- Anthropic (Claude)
- Google (Gemini)
- Azure OpenAI
- HuggingFace
- Cohere
- Together AI
- Ollama (for local models)
- And many more...

## Development

### Running Tests

```bash
pytest
```

### Adding New Personalities

1. Edit `src/utils/personalities.py`
2. Add a new entry to the `PERSONALITIES` dictionary
3. Define the personality traits, communication style, and behavior patterns
4. The new personality will automatically be available through the slash commands

### Extending Functionality

1. Add new cogs in the `src/cogs/` directory
2. Load them in `src/main.py` in the `on_ready()` event
3. Follow the existing pattern for consistency

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

[Add your license information here]

## Acknowledgements

- [LiteLLM](https://github.com/BerriAI/litellm) for AI model abstraction
- [Pycord](https://github.com/Pycord-Development/pycord) for Discord API integration
- [aiosqlite](https://github.com/omnilib/aiosqlite) for async SQLite operations