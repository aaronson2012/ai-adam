# src/cogs/personality.py

import discord
from discord.ext import commands
import logging
from src.utils.personalities import get_available_personalities, get_personality

# Store the current personality for each server
server_personalities = {}

def get_server_personality(guild_id):
    """Get the current personality for a server."""
    return server_personalities.get(guild_id, "default")

def set_server_personality(guild_id, personality):
    """Set the current personality for a server."""
    server_personalities[guild_id] = personality

def setup(bot):
    logger = logging.getLogger(__name__)
    logger.info("Setting up personality commands")
    
    # Define autocomplete function for personality names
    async def personality_autocomplete(ctx: discord.AutocompleteContext):
        personalities = get_available_personalities()
        logger.info(f"Autocomplete requested with value: {ctx.value}")
        result = [name for name in personalities if ctx.value.lower() in name.lower()][:25]
        logger.info(f"Autocomplete returning: {result}")
        return result
    
    @bot.slash_command(name="personality", description="Set the bot's personality")
    async def personality(ctx: discord.ApplicationContext,
                         name: discord.Option(str, "Personality name", 
                                            autocomplete=personality_autocomplete)):
        """Set the bot's personality"""
        logger.info(f"Personality command called with name: {name}")
        
        # Check if the user has permission to manage the guild
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.respond("You need 'Manage Server' permissions to change the bot's personality.", ephemeral=True)
            return
        
        # Check if the personality exists
        try:
            personality_data = get_personality(name)
        except KeyError:
            await ctx.respond(f"Personality '{name}' not found.", ephemeral=True)
            return
        
        # Set the personality for this server
        set_server_personality(ctx.guild.id if ctx.guild else "default", name)
        
        embed = discord.Embed(
            title="Personality Changed",
            description=f"Personality set to **{personality_data['name']}**",
            color=discord.Color.green()
        )
        
        await ctx.respond(embed=embed)
    
    # Remove the test command as we've identified the issue
    logger.info("Personality commands setup completed")