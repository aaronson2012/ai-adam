# src/cogs/memory.py

import json
import logging

import discord

logger = logging.getLogger(__name__)

def setup(bot):
    # Get the database manager from the bot
    db_manager = bot.db_manager
    logger.info("Setting up memory commands")
    
    @bot.slash_command(name="memory", description="Retrieve or clear memory")
    async def memory(ctx: discord.ApplicationContext,
                     target: discord.Option(str, "Target memory type", 
                                          choices=["user", "server"], 
                                          default="user") = "user",
                     user: discord.Option(discord.Member, "User to retrieve memory for", 
                                        required=False) = None,
                     clear: discord.Option(bool, "Clear the memory", 
                                         required=False, default=False) = False):
        """Retrieve memory information"""
        # Log the command execution
        guild_info = ctx.guild.id if ctx.guild else 'DM'
        logger.info(f"Memory command executed by {ctx.author} in guild {guild_info}")
        logger.info(f"Requested target: {target}, user: {user}")
        logger.debug(f"Clear option: {clear}")
        
        try:
            if target == "server":
                logger.debug("Processing server memory request")
                # Check if in a guild
                if not ctx.guild:
                    logger.debug("Command executed in DM, server memory not available")
                    await ctx.respond("Server memory can only be accessed in a server.", ephemeral=True)
                    return
                
                # Handle clear option for server
                if clear:
                    logger.debug("Server memory clear requested")
                    # Check permissions
                    logger.debug(f"Checking permissions for user {ctx.author.id}")
                    if not ctx.author.guild_permissions.manage_guild:
                        logger.warning(f"User {ctx.author} attempted to clear server memory without permission")
                        await ctx.respond("You need 'Manage Server' permissions to clear server memory.", ephemeral=True)
                        return
                    
                    # Confirm with the user before clearing memory
                    logger.debug("Creating confirmation view for server memory clear")
                    confirm_view = ConfirmClearView(ctx.author, ctx.guild, db_manager, target="server")
                    msg = (f"Are you sure you want to clear all memory for {ctx.guild.name}? "
                           "This action cannot be undone.")
                    await ctx.respond(msg, view=confirm_view, ephemeral=True)
                    return
                    
                # Get server memory
                logger.debug(f"Retrieving server memory for guild ID: {ctx.guild.id}")
                server_memory = await db_manager.get_server_memory(str(ctx.guild.id))
                logger.debug(f"Server memory retrieved: {server_memory}")
                if server_memory and server_memory.get("known_facts"):
                    try:
                        logger.debug("Parsing server memory facts")
                        facts = json.loads(server_memory["known_facts"])
                        logger.debug(f"Server facts: {facts}")
                        if facts:
                            logger.debug("Creating embed for server memory")
                            embed = discord.Embed(
                                title=f"Server Memory for {ctx.guild.name}",
                                description="Server-wide facts and information",
                                color=discord.Color.blue()
                            )
                            
                            for key, value in facts.items():
                                logger.debug(f"Adding fact to embed: {key} = {value}")
                                # Truncate long values
                                if len(str(value)) > 1024:
                                    value = str(value)[:1021] + "..."
                                embed.add_field(name=key.replace("_", " ").title(), value=str(value), inline=False)
                            
                            logger.debug("Sending server memory embed")
                            await ctx.respond(embed=embed, ephemeral=True)
                        else:
                            logger.debug("No server facts found")
                            await ctx.respond("No server memory found.", ephemeral=True)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Error parsing server memory JSON: {e}")
                        await ctx.respond("No server memory found.", ephemeral=True)
                else:
                    logger.debug("No server memory found")
                    await ctx.respond("No server memory found.", ephemeral=True)
                    
            else:  # target == "user"
                logger.debug("Processing user memory request")
                # Determine which user's memory to retrieve
                target_user = user if user else ctx.author
                target_user_id = str(target_user.id)
                logger.debug(f"Target user: {target_user.display_name} (ID: {target_user_id})")
                
                # Handle clear option for user
                if clear:
                    logger.debug("User memory clear requested")
                    # Check permissions
                    logger.debug(f"Checking permissions for user {ctx.author.id}")
                    if not ctx.author.guild_permissions.manage_guild:
                        logger.warning(f"User {ctx.author} attempted to clear user memory without permission")
                        await ctx.respond("You need 'Manage Server' permissions to clear user memory.", ephemeral=True)
                        return
                    
                    # Confirm with the user before clearing memory
                    logger.debug("Creating confirmation view for user memory clear")
                    confirm_view = ConfirmClearView(ctx.author, target_user, db_manager, target="user")
                    msg = (f"Are you sure you want to clear all memory for {target_user.display_name}? "
                           "This action cannot be undone.")
                    await ctx.respond(msg, view=confirm_view, ephemeral=True)
                    return
                
                # Get user memory
                logger.debug(f"Retrieving user memory for user ID: {target_user_id}")
                user_memory = await db_manager.get_user_memory(target_user_id)
                logger.debug(f"User memory retrieved: {user_memory}")
                if user_memory and user_memory.get("known_facts"):
                    try:
                        logger.debug("Parsing user memory facts")
                        facts = json.loads(user_memory["known_facts"])
                        logger.debug(f"User facts: {facts}")
                        if facts:
                            logger.debug("Creating embed for user memory")
                            embed = discord.Embed(
                                title=f"Memory for {target_user.display_name}",
                                description=f"Personal facts and information for {target_user.mention}",
                                color=discord.Color.green()
                            )
                            
                            for key, value in facts.items():
                                logger.debug(f"Adding fact to embed: {key} = {value}")
                                # Truncate long values
                                if len(str(value)) > 1024:
                                    value = str(value)[:1021] + "..."
                                embed.add_field(name=key.replace("_", " ").title(), value=str(value), inline=False)
                            
                            logger.debug("Sending user memory embed")
                            await ctx.respond(embed=embed, ephemeral=True)
                        else:
                            msg = f"No personal memory found for {target_user.mention}."
                            logger.debug(msg)
                            await ctx.respond(msg, ephemeral=True)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Error parsing user memory JSON: {e}")
                        await ctx.respond(f"No personal memory found for {target_user.mention}.", ephemeral=True)
                else:
                    msg = f"No personal memory found for {target_user.mention}."
                    logger.debug(msg)
                    await ctx.respond(msg, ephemeral=True)
                    
        except Exception as e:
            logger.error(f"Error retrieving memory: {e}", exc_info=True)
            await ctx.respond("Error retrieving memory.", ephemeral=True)
    
    logger.info("Memory commands setup completed")


class ConfirmClearView(discord.ui.View):
    def __init__(self, command_user, target_entity, db_manager, target="user"):
        super().__init__(timeout=60)
        self.command_user = command_user
        self.target_entity = target_entity
        self.db_manager = db_manager
        self.target = target  # "user" or "server"
        logger.debug(f"ConfirmClearView initialized: target={target}, command_user={command_user}, target_entity={target_entity}")
    
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        logger.debug(f"Confirm button pressed by user {interaction.user}")
        # Check if the interaction is from the user who initiated the command
        if interaction.user != self.command_user:
            logger.warning(f"User {interaction.user} attempted to confirm action they didn't initiate")
            await interaction.response.send_message("You cannot confirm this action.", ephemeral=True)
            return
            
        try:
            if self.target == "user":
                logger.debug(f"Clearing user memory for user ID: {self.target_entity.id}")
                # Clear the user's memory
                user_id = str(self.target_entity.id)
                await self.db_manager.clear_user_memory(user_id)
                msg = f"Successfully cleared memory for {self.target_entity.display_name}."
                logger.info(msg)
                await interaction.response.send_message(msg, ephemeral=True)
            else:  # server
                logger.debug(f"Clearing server memory for guild ID: {self.target_entity.id}")
                # Clear the server's memory
                guild_id = str(self.target_entity.id)
                await self.db_manager.clear_server_memory(guild_id)
                msg = f"Successfully cleared memory for {self.target_entity.name}."
                logger.info(msg)
                await interaction.response.send_message(msg, ephemeral=True)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error clearing memory: {e}", exc_info=True)
            await interaction.response.send_message("Error clearing memory.", ephemeral=True)
        
        # Disable the buttons after use
        logger.debug("Disabling buttons and stopping view")
        self.stop()
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        logger.debug(f"Cancel button pressed by user {interaction.user}")
        # Check if the interaction is from the user who initiated the command
        if interaction.user != self.command_user:
            logger.warning(f"User {interaction.user} attempted to cancel action they didn't initiate")
            await interaction.response.send_message("You cannot cancel this action.", ephemeral=True)
            return
            
        msg = "Memory clear operation cancelled."
        logger.info(msg)
        await interaction.response.send_message(msg, ephemeral=True)
        
        # Disable the buttons after use
        logger.debug("Disabling buttons and stopping view")
        self.stop()
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)