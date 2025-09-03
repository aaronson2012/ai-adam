import discord
from discord.ext import commands
import os
import logging
import tomllib # For reading TOML config
from dotenv import load_dotenv # For loading .env variables
import litellm # For AI interactions
import asyncio # For background tasks
# Import database manager
from src.database.manager import DatabaseManager
# Import personality system
from src.utils.personalities import get_personality_prompt, get_available_personalities, get_personality
# Import emoji analyzer
from src.utils.emoji_analyzer import create_enhanced_emoji_prompt
# Import emoji manager
from src.utils.emoji_manager import EmojiManager

# --- Configuration ---
load_dotenv() # Load environment variables from .env

# Load configuration from config.toml
try:
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)
except FileNotFoundError:
    print("config.toml not found. Please create it based on config.example.toml")
    exit(1)

# Initialize database manager
db_manager = DatabaseManager(config['database']['path'])

# Initialize emoji manager
emoji_manager = EmojiManager(db_manager)

# --- Logging ---
logging.basicConfig(
    level=getattr(logging, config['logging']['level'], logging.INFO),
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# --- Bot Setup ---
# Get token from .env or config (prefer .env for secrets)
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN') or config['discord'].get('token')
if not DISCORD_TOKEN:
    logger.error("Discord token not found! Please set DISCORD_TOKEN in .env or config.toml")
    exit(1)

# Set LiteLLM API keys from environment variables
# LiteLLM will automatically pick these up
# We dynamically set all environment variables that are already defined
# This is more graceful than hardcoding all possible variables
import os

# Common LLM provider environment variables
llm_env_vars = [
    "OPENAI_API_KEY",
    "AZURE_API_KEY",
    "AZURE_ENDPOINT",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_API_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_REGION_NAME",
    "HF_TOKEN",
    "HUGGINGFACE_API_KEY",
    "COHERE_API_KEY",
    "REPLICATE_API_KEY",
    "TOGETHERAI_API_KEY",
    "TOGETHER_API_KEY",
    "OLLAMA_HOST",
    "MISTRAL_API_KEY",
    "GROQ_API_KEY",
    "DEEPSEEK_API_KEY",
    "FIREWORKS_API_KEY",
    "OPENROUTER_API_KEY",
    "AI21_API_KEY",
    "NLPCLOUD_API_KEY",
    "ALEPHALPHA_API_KEY",
    "VOYAGE_API_KEY",
    "JINA_API_KEY",
    "LMSTUDIO_HOST",
    "PERPLEXITYAI_API_KEY",
    "PERPLEXITY_API_KEY",
    "ELEVENLABS_API_KEY",
    "CLARIFAI_PAT",
    "GITHUB_TOKEN",
    "IBM_API_KEY",
    "WATSONX_API_KEY",
    "DATABRICKS_HOST",
    "DATABRICKS_TOKEN",
    "MOONSHOT_API_KEY",
    "XINFERENCE_API_KEY",
    "DEEPINFRA_API_KEY",
    "ANYSCALE_API_KEY",
    "PREDIBASE_API_KEY",
    "CEREBRAS_API_KEY",
    "OCTOAI_TOKEN",
    "BASETEN_API_KEY",
    "SAMBANOVA_API_KEY",
    "FEATHERLESS_API_KEY",
    "DATAROBOT_API_KEY",
    "RECRAFT_API_KEY",
    "NOVITA_API_KEY",
    "DASHSCOPE_API_KEY",
    "VOLCENGINE_API_KEY",
    "NEBIUS_API_KEY",
    "BYTEZ_API_KEY",
    "OCI_CONFIG_FILE",
    "OCI_CONFIG_PROFILE",
    "VLLM_API_KEY",
    "LLAMAFILE_API_KEY",
    "INFINITY_API_KEY",
    "TRITON_API_KEY",
    "GALADRIEL_API_KEY",
    "TOPAZ_API_KEY",
    "FRIENDLI_API_KEY",
    "MORPH_API_KEY",
    "LAMBDA_API_KEY",
    "VERCEL_AI_GATEWAY_API_KEY",
    "V0_API_KEY",
    "AIMLAPI_API_KEY",
    "CLOUDFLARE_API_TOKEN",
    "NVIDIA_API_KEY",
    "HYPERBOLIC_API_KEY",
    "GRADIENTAI_API_KEY",
    "PETALS_API_KEY",
    "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_USER",
    "SNOWFLAKE_PASSWORD",
    "SNOWFLAKE_ROLE",
    "SNOWFLAKE_WAREHOUSE",
    "SNOWFLAKE_DATABASE",
    "SNOWFLAKE_SCHEMA",
    "XAI_API_KEY",
    "NSCALE_API_KEY"
]

# Set environment variables for any that are defined in the actual environment
for var in llm_env_vars:
    if os.getenv(var) is not None:
        os.environ[var] = os.getenv(var)

# Define bot intents (adjust as needed for your features)
intents = discord.Intents.default()
intents.message_content = True # Needed to read message content
intents.members = True # Needed if you plan to track user info
intents.emojis = True # Needed to access server emojis

# Initialize the bot with slash command support
bot = discord.Bot(intents=intents)
# Attach the database manager to the bot so cogs can access it
bot.db_manager = db_manager
# Attach config to bot for use by cogs
bot.config = config

# Force sync commands
@bot.event
async def on_connect():
    logger.info("Bot connected to Discord gateway")
    if bot.auto_sync_commands:
        logger.info("Syncing commands...")
        await bot.sync_commands()
        logger.info("Commands synced successfully")
        
# Also sync commands when the bot is ready
@bot.event
async def on_ready():
    logger.info(f'Bot {bot.user} has connected to Discord!')
    # Initialize database connection
    await db_manager.init_db()
    
    # Start background emoji caching
    asyncio.create_task(emoji_manager.cache_emojis_on_startup(bot))
    # Note: We're not starting the periodic background caching task here to avoid duplicate caching
    # The startup caching will handle initial emoji processing, and we can manually trigger
    # caching checks if needed
    
    # Force sync commands after registration
    logger.info("Syncing commands after registration...")
    await bot.sync_commands()
    logger.info("Commands synced successfully after registration")
    
    # Additional debug info
    logger.info(f"Bot ID: {bot.user.id}")
    logger.info(f"Bot name: {bot.user.name}")



# Load cogs before the bot is ready
try:
    # Import and register the personality commands
    import src.cogs.personality
    src.cogs.personality.setup(bot)
    logger.info("Personality commands registered successfully")
    
    # Import and register the memory commands
    import src.cogs.memory
    src.cogs.memory.setup(bot)
    logger.info("Memory commands registered successfully")
    
    # Import and register the reactions cog
    import src.cogs.reactions
    src.cogs.reactions.setup(bot)
    logger.info("Reactions cog registered successfully")
    
    # Debug information about registered commands
    logger.info(f"Registered slash commands: {[cmd.name for cmd in bot.pending_application_commands]}")
    logger.info(f"Total number of registered commands: {len(bot.pending_application_commands)}")
    
    # Print details of each command
    for cmd in bot.pending_application_commands:
        logger.info(f"Command: {cmd.name}, Description: {cmd.description}")
        
except Exception as e:
    logger.error(f"Failed to register commands: {e}")
    import traceback
    traceback.print_exc()

# Import personality functions after bot setup
from src.utils.personalities import get_server_personality as get_memory_server_personality, set_server_personality as set_memory_server_personality

# Wrapper functions for database-backed personality storage
async def get_server_personality(guild_id):
    """Get the current personality for a server, with database persistence."""
    # Try to get from database first
    try:
        personality = await db_manager.get_server_personality(str(guild_id))
        return personality
    except Exception as e:
        logger.error(f"Error retrieving personality from database: {e}")
        # Fallback to in-memory storage
        return get_memory_server_personality(guild_id)

async def set_server_personality(guild_id, personality):
    """Set the current personality for a server, with database persistence."""
    # Save to database
    try:
        await db_manager.set_server_personality(str(guild_id), personality)
    except Exception as e:
        logger.error(f"Error saving personality to database: {e}")
        # Fallback to in-memory storage
        set_memory_server_personality(guild_id, personality)

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Get user ID
    user_id = str(message.author.id)
    
    # --- AI Learning/Interaction Logic ---
    # Respond only when mentioned or in DM, but always learn from all messages
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        # Show typing indicator
        await message.channel.trigger_typing()
        
        # Record the user's message first
        interaction = {
            "user_message": message.content,
            "timestamp": str(message.created_at)
        }
        await db_manager.update_user_memory(user_id, user_message=message.content, interaction=interaction)
        
        # Check if this is a memory update request (mentioning another user)
        target_user = None
        target_user_id = None
        if message.mentions and len(message.mentions) > 0:
            # Check if the bot is mentioned and someone else is also mentioned
            bot_mentioned = any(mention.id == bot.user.id for mention in message.mentions)
            if bot_mentioned and len(message.mentions) > 1:
                # Find the non-bot mention to target for memory update
                for mention in message.mentions:
                    if mention.id != bot.user.id:
                        target_user = mention
                        target_user_id = str(mention.id)
                        break
        
        # Retrieve user context/memory
        user_memory = await db_manager.get_user_memory(user_id)
        
        # Retrieve server memory if in a guild
        server_memory = {}
        if message.guild:
            server_memory = await db_manager.get_server_memory(str(message.guild.id))
        
        # Retrieve memories of other active users in the conversation (if in a guild)
        other_user_memories = {}
        if message.guild:
            # Get recent message authors from the channel to identify active users
            try:
                recent_authors = set()
                async for msg in message.channel.history(limit=10):
                    if not msg.author.bot and str(msg.author.id) != user_id:
                        recent_authors.add(str(msg.author.id))
                
                # Get memories for recent authors (limit to 3 to avoid overwhelming)
                author_count = 0
                for author_id in recent_authors:
                    if author_count >= 3:
                        break
                    author_memory = await db_manager.get_user_memory(author_id)
                    if author_memory and author_memory.get("known_facts"):
                        other_user_memories[author_id] = author_memory
                    author_count += 1
            except Exception as e:
                logger.warning(f"Could not fetch other user memories: {e}")
        
        # Get the personality prompt for this server
        guild_id = message.guild.id if message.guild else "default"
        personality_name = await get_server_personality(guild_id)
        logger.info(f"Using personality '{personality_name}' for guild {guild_id}")
        personality_prompt = get_personality_prompt(personality_name)
        logger.debug(f"Personality prompt: {personality_prompt[:200]}...")
        
        # Check if emoji caching is in progress
        global emoji_manager
        if emoji_manager.is_caching_in_progress():
            # If caching is in progress, send a waiting message
            await message.channel.send("Emojis are currently being cached and processed. Please wait...")
            # Still create a simple emoji prompt without descriptions for now
            from src.utils.emoji_helper import create_emoji_prompt
            emoji_prompt = create_emoji_prompt(message.guild)
        else:
            # Get enhanced emoji prompt with visual descriptions
            # Note: This now uses cached data, so it won't block
            emoji_prompt = await create_enhanced_emoji_prompt(message.guild, db_manager)
        
        # Prepare prompt with personality, memory, and emoji information
        # But limit how much memory we include to avoid over-referencing
        memory_facts = user_memory.get("known_facts", "{}")
        try:
            facts_dict = json.loads(memory_facts)
            # Only include a subset of facts to avoid overwhelming the conversation
            # And be more selective about which facts to include
            limited_facts = {}
            fact_count = 0
            # Priority order for facts to include (most relevant first)
            priority_keys = ['name', 'interests', 'preferences', 'hobbies']
            # First include priority facts
            for key in priority_keys:
                if key in facts_dict and facts_dict[key] and fact_count < 3:
                    limited_facts[key] = facts_dict[key]
                    fact_count += 1
            # Then include other facts up to the limit
            for key, value in facts_dict.items():
                if key not in priority_keys and value and fact_count < 5:
                    limited_facts[key] = value
                    fact_count += 1
            user_limited_memory = json.dumps(limited_facts) if limited_facts else "{}"
        except:
            user_limited_memory = "{}"
        
        # Include server memory (limited)
        server_facts = server_memory.get("known_facts", "{}")
        try:
            server_facts_dict = json.loads(server_facts)
            # Limit server facts to avoid overwhelming
            limited_server_facts = {}
            server_fact_count = 0
            for key, value in server_facts_dict.items():
                if value and server_fact_count < 3:
                    limited_server_facts[key] = value
                    server_fact_count += 1
            server_limited_memory = json.dumps(limited_server_facts) if limited_server_facts else "{}"
        except:
            server_limited_memory = "{}"
        
        # Include limited other user memories
        other_memories_text = ""
        if other_user_memories:
            other_memories_parts = []
            for user_id, memory in other_user_memories.items():
                try:
                    facts_dict = json.loads(memory.get("known_facts", "{}"))
                    if facts_dict:
                        # Only include the most important fact per user
                        for key in ['name', 'interests', 'hobbies']:
                            if key in facts_dict and facts_dict[key]:
                                other_memories_parts.append(f"User {user_id}: {key}={facts_dict[key]}")
                                break
                        # If no priority facts, include first available fact
                        if not other_memories_parts or not any(f"User {user_id}:" in part for part in other_memories_parts):
                            first_key = next(iter(facts_dict))
                            if facts_dict[first_key]:
                                other_memories_parts.append(f"User {user_id}: {first_key}={facts_dict[first_key]}")
                except:
                    pass
            if other_memories_parts:
                other_memories_text = "\nOther active users: " + ", ".join(other_memories_parts[:3])  # Limit to 3 users
        
        full_prompt = f"{personality_prompt}\n\nUser Memory: {user_limited_memory}\nServer Memory: {server_limited_memory}{other_memories_text}\nUser Message: {message.content}{emoji_prompt}\nRespond as the AI with the personality described above:"
        
        # Call LLM
        try:
            response = litellm.completion(model=config['ai']['default_model'], messages=[{"role": "user", "content": full_prompt}])
            ai_reply = response['choices'][0]['message']['content']
            
            # Send response
            await message.channel.send(ai_reply)
            
            # Update memory with the bot's response
            interaction = {
                "user_message": message.content,
                "ai_response": ai_reply,
                "timestamp": str(message.created_at)
            }
            await db_manager.update_user_memory(user_id, user_message=message.content, ai_response=ai_reply, interaction=interaction)
            
            # If this was a memory update request for another user, update their memory too
            if target_user_id:
                target_facts = await db_manager.extract_targeted_facts(message.content, target_user_id, message.guild.members if message.guild else None)
                if target_facts:
                    # Update the target user's memory
                    await db_manager.update_user_memory(target_user_id, user_message=message.content, additional_facts=target_facts)
                    logger.info(f"Updated memory for target user {target_user_id} with facts: {target_facts}")
        except Exception as e:
            logger.error(f"Error processing AI response: {e}")
            await message.channel.send("Sorry, I encountered an error processing your request.")
    else:
        # Always update user memory with the new message, even if we don't respond
        # This allows the bot to learn from all conversations it can see
        # But be more conservative about fact extraction in passive listening mode
        interaction = {
            "user_message": message.content,
            "timestamp": str(message.created_at)
        }
        
        # For passive listening, only extract facts if there's high confidence
        # and the message contains clear factual information about users
        await db_manager.update_user_memory(user_id, user_message=message.content, interaction=interaction, passive_mode=True)
    
    # Important: Process events for cogs after handling the message
    # This allows other cogs like reactions to process the message as well
    # We need to manually call cog event handlers to avoid infinite loops
    for cog_name, cog in bot.cogs.items():
        if hasattr(cog, 'on_message'):
            try:
                await cog.on_message(message)
            except Exception as e:
                logger.error(f"Error in cog {cog_name} on_message handler: {e}", exc_info=True)

# --- Run the Bot ---
if __name__ == "__main__":
    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    finally:
        # Clean up background tasks
        emoji_manager.cancel_background_task()