# AI-Adam

A Discord bot with AI chat capabilities and learning features. AI-Adam is designed to be a natural, conversational AI assistant that responds like an actual human while learning from interactions to provide personalized responses.

## Features

- **Natural Language Processing**: Uses LiteLLM to interface with various AI models (OpenAI, Anthropic, Google, etc.)
- **Personality System**: Configurable personalities that change the bot's behavior and responses
- **Memory Learning**: Remembers user interactions to provide personalized responses over time
- **Emoji Intelligence**: Analyzes and understands server emojis for more contextual responses
- **Slash Commands**: Easy-to-use slash commands for bot interaction
- **Multi-model Support**: Works with numerous LLM providers through LiteLLM
- **Server-specific Customization**: Each server can set its own personality
- **Memory Management**: View and clear user memory with appropriate permissions
- **Automatic Reactions**: AI-powered automatic reactions to enhance conversations
- **Server-wide Memory**: Stores community facts and inside jokes

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
- `/memory` - Retrieve or clear memory information for users or servers

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

### Available Personalities

1. **Default** - A natural, conversational AI assistant
2. **Tech Expert** - Knowledgeable technology expert who explains complex concepts simply
3. **Memer** - Meme-focused personality with humorous responses
4. **Karen** - Entitled customer service personality
5. **The Noughties Memer** - 2000s internet culture with l33t speak and classic memes
6. **The Reddit and Discord Mod** - Power-hungry moderator personality
7. **Tifa Lockhart** - Character from Final Fantasy VII with caring and determined personality

### Adding New Personalities

To add a new personality:

1. Create a new TOML file in `src/personalities/` (copy an existing personality as a starting point)
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
- You SHOULD use emojis liberally and frequently to enhance communication and add personality to your responses
- You MAY use multiple emojis in a single message to express emotions or reactions
- You SHOULD prioritize using custom server emojis over standard emojis when available and appropriate
- You MAY use standard emojis when no custom server emoji is suitable for the context
- You SHOULD use emojis to "spice things up" and make conversations more engaging

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

## Memory System

AI-Adam remembers interactions with users to provide personalized responses over time:

1. **Fact Learning**: The bot learns facts about users from conversations
2. **Interaction History**: Last 20 interactions are stored for context
3. **Server Memory**: Server-wide facts and community information
4. **Memory Management**: Server administrators can view or clear user memory
5. **Privacy**: Memory is stored locally and can be managed by server admins

### Memory Commands

- `/memory target:user [user:@User] [clear:true]` - View or clear memory information for a specific user (defaults to command user)
- `/memory target:server [clear:true]` - View or clear server-wide memory information

## Emoji Intelligence

AI-Adam can understand and use server-specific emojis. The bot:

1. Analyzes custom server emojis
2. Uses vision models to understand what emojis represent (when available)
3. Incorporates emoji understanding into conversations
4. Uses emojis liberally to enhance communication

### Emoji Caching

To improve performance and reduce API usage, AI-Adam caches emoji descriptions in the database. When the bot first encounters a custom emoji, it analyzes the emoji using a vision model (if available) and stores the description in the database. On subsequent encounters with the same emoji, the bot retrieves the cached description instead of re-analyzing the emoji, which significantly speeds up response times and reduces API costs.

The bot automatically caches all emojis for all servers it's in when it starts up, and periodically checks for new emojis.

## Automatic Reactions

AI-Adam can automatically react to messages with appropriate emojis:

1. **AI-powered Analysis**: Uses AI to determine when and how to react
2. **Personality Context**: Reactions are influenced by the server's personality
3. **Spam Prevention**: Intelligent controls to avoid excessive reactions
4. **Custom Emoji Support**: Uses server-specific emojis when appropriate

## Database

AI-Adam uses SQLite for storing user memory and interaction history. The database schema includes:

- `user_memory` table with:
  - `user_id`: Discord user ID
  - `known_facts`: JSON string of facts learned about the user
  - `interaction_history`: JSON string of recent interactions (last 20)
  - `last_updated`: Timestamp of last update
- `emoji_descriptions` table with:
  - `emoji_key`: Format guild_id:emoji_name
  - `description`: Cached description of the emoji
  - `created_at`: Timestamp when the description was created
  - `updated_at`: Timestamp when the description was last updated
- `server_personalities` table with:
  - `guild_id`: Discord server ID
  - `personality_name`: Name of the personality set for this server
  - `created_at`: Timestamp when the personality was set
  - `updated_at`: Timestamp when the personality was last updated
- `server_memory` table with:
  - `guild_id`: Discord server ID
  - `known_facts`: JSON string of server-wide facts
  - `last_updated`: Timestamp of last update

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
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run end-to-end tests only
pytest tests/e2e/
```

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