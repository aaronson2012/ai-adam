# src/cogs/personality.py

import discord
from discord.ext import commands
import logging
from src.utils.personalities import get_available_personalities, get_personality

def setup(bot):
    # Get the database manager from the bot
    db_manager = bot.db_manager
    logger = logging.getLogger(__name__)
    logger.info("Setting up personality commands")
    
    # Define autocomplete function for personality names with descriptions
    async def personality_autocomplete(ctx: discord.AutocompleteContext):
        logger.debug(f"Personality autocomplete requested with value: {ctx.value}")
        from src.utils.personalities import get_available_personalities, get_personality
        personalities = get_available_personalities()
        logger.debug(f"Available personalities: {personalities}")
        results = []
        
        for name in personalities:
            if ctx.value.lower() in name.lower():
                logger.debug(f"Matching personality: {name}")
                personality_data = get_personality(name)
                friendly_name = personality_data.get('name', name)  # Use the friendly name from data
                description = personality_data.get('description', '')
                logger.debug(f"Personality data: name={friendly_name}, description={description}")
                
                # Format the display name with the friendly name and description
                if description:
                    # Truncate description to keep the option name reasonable
                    truncated_desc = (description[:70] + '...') if len(description) > 70 else description
                    display_name = f"{friendly_name} - {truncated_desc}"
                else:
                    display_name = friendly_name
                    
                # Ensure the display name isn't too long (Discord has limits)
                if len(display_name) > 100:
                    display_name = display_name[:97] + "..."
                logger.debug(f"Display name: {display_name}")
                results.append(discord.OptionChoice(name=display_name, value=name))
                
        logger.debug(f"Returning {len(results)} autocomplete results")
        return results[:25]  # Limit to 25 results
    
    @bot.slash_command(name="personality", description="Set the bot's personality")
    async def personality(ctx: discord.ApplicationContext,
                         name: discord.Option(str, "Personality name", 
                                            autocomplete=personality_autocomplete)):
        """Set the bot's personality"""
        # Log the command execution
        logger.info(f"Personality command executed by {ctx.author} in guild {ctx.guild.id if ctx.guild else 'DM'}")
        logger.info(f"Requested personality: {name}")
        
        # Check if the user has permission to manage the guild
        logger.debug(f"Checking permissions for user {ctx.author.id}")
        if not ctx.author.guild_permissions.manage_guild:
            logger.warning(f"User {ctx.author} attempted to change personality without permission")
            await ctx.respond("You need 'Manage Server' permissions to change the bot's personality.", ephemeral=True)
            return
        
        # Check if the personality exists
        logger.debug(f"Checking if personality '{name}' exists")
        personality_data = get_personality(name)
        logger.debug(f"Personality data: {personality_data}")
        if not personality_data or not personality_data.get('name'):
            logger.warning(f"Personality '{name}' not found")
            await ctx.respond(f"Personality '{name}' not found.", ephemeral=True)
            return
        
        # Set the personality for this server using database
        guild_id = ctx.guild.id if ctx.guild else "default"
        logger.info(f"Setting personality '{name}' for guild {guild_id}")
        try:
            await db_manager.set_server_personality(str(guild_id), name)
            logger.debug("Personality saved to database successfully")
        except Exception as e:
            logger.error(f"Error saving personality to database: {e}")
            await ctx.respond("Error saving personality setting.", ephemeral=True)
            return
        
        # Verify the personality was set
        logger.debug("Verifying personality was set")
        try:
            current_personality = await db_manager.get_server_personality(str(guild_id))
            logger.debug(f"Retrieved personality from database: {current_personality}")
        except Exception as e:
            logger.error(f"Error retrieving personality from database: {e}")
            current_personality = name  # Assume it worked
        logger.info(f"Personality set to: {current_personality}")
        
        embed = discord.Embed(
            title="Personality Changed",
            description=f"Personality set to **{personality_data['name']}**",
            color=discord.Color.green()
        )
        
        logger.debug("Sending personality change confirmation")
        await ctx.respond(embed=embed)
    
    logger.info("Personality commands setup completed")