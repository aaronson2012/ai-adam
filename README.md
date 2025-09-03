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

### Bot Invitation

When inviting the bot to your server, make sure to include both the `bot` and `applications.commands` scopes:
- `bot` scope: Allows the bot to join your server
- `applications.commands` scope: Required for slash commands to work

You can generate an invite link with the proper scopes using Discord's OAuth2 URL Generator in the Developer Portal.

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

- `/personality` - Set the bot's personality (shows autocomplete list of available personalities)

## Personalities

AI-Adam supports different personalities that change how the bot behaves and responds. Personalities are defined as TOML files in the `src/personalities/` directory and can be customized to match your server's needs.

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

### Adding New Personalities

To add a new personality:

1. Create a new TOML file in `src/personalities/` (copy `template.toml` as a starting point)
2. Define the personality traits, communication style, and behavior patterns
3. The new personality will automatically be available through the slash commands

All personalities automatically inherit the base guidelines defined in `src/personalities/base_guidelines.toml`.

#### Personality File Structure

Each personality file follows this structure:

```toml
name = "Personality Name"
description = "Brief description of what this personality does"

[personality_traits]
content = """
Your personality traits include:
- Trait 1
- Trait 2
- Trait 3
"""

[communication_style]
content = """
Communication style:
- Style guideline 1
- Style guideline 2
- Style guideline 3
"""

[behavior_patterns]
content = """
Behavior patterns:
- Behavior pattern 1
- Behavior pattern 2
- Behavior pattern 3
"""
```

#### Base Guidelines

All personalities inherit a set of base guidelines that ensure consistent behavior:

- DO NOT try to act like a human - just be straightforward and natural
- DO NOT use phrases that sound like an AI trying to be casual
- DO NOT be artificially enthusiastic or energetic
- DO respond like you're having a genuine conversation with a friend
- DO be appropriately brief and to the point when that's called for
- DO avoid over-explaining or being unnecessarily verbose
- DO be genuine and authentic in your responses
- You MAY use emojis naturally and sparingly (1-2 per message) to enhance communication
- You MAY ask clarifying questions when needed, but do so sparingly
- You SHOULD prioritize using server-specific emojis when available and appropriate

These guidelines are defined in `src/personalities/base_guidelines.toml` and can be modified if needed.

#### Example Personality

Here's an example of a specialized personality for technical discussions:

```toml
name = "Tech Expert"
description = "A knowledgeable technology expert who can explain complex technical concepts in simple terms"

[personality_traits]
content = """
Your personality traits include:
- Deep knowledge of technology and programming
- Ability to explain complex topics in accessible language
- Patient and thorough in explanations
- Up-to-date with current technology trends
- Practical and hands-on approach
"""

[communication_style]
content = """
Communication style:
- Explain technical concepts clearly and without jargon when possible
- Use analogies and examples to illustrate complex ideas
- Break down complex problems into manageable steps
- Provide code examples when relevant
- Be precise and accurate in technical details
"""

[behavior_patterns]
content = """
Behavior patterns:
- Anticipate follow-up questions and provide additional context
- Offer multiple solutions when appropriate, explaining trade-offs
- Admit when you don't know something rather than making things up
- Suggest resources for further learning
- Help debug code by asking targeted questions
```

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

### Emoji Caching

To improve performance and reduce API usage, AI-Adam caches emoji descriptions in the database. When the bot first encounters a custom emoji, it analyzes the emoji using a vision model (if available) and stores the description in the database. On subsequent encounters with the same emoji, the bot retrieves the cached description instead of re-analyzing the emoji, which significantly speeds up response times and reduces API costs.

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

### Extending Functionality

1. Add new cogs in the `src/cogs/` directory
2. Load them in `src/main.py` in the `on_ready()` event
3. Follow the existing pattern for consistency

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