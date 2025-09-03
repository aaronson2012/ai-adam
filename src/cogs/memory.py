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
        
        try:
            if target == "server":
                # Check if in a guild
                if not ctx.guild:
                    await ctx.respond("Server memory can only be accessed in a server.", ephemeral=True)
                    return
                
                # Handle clear option for server
                if clear:
                    # Check permissions
                    if not ctx.author.guild_permissions.manage_guild:
                        await ctx.respond("You need 'Manage Server' permissions to clear server memory.", ephemeral=True)
                        return
                    
                    # Confirm with the user before clearing memory
                    confirm_view = ConfirmClearView(ctx.author, ctx.guild, db_manager, target="server")
                    msg = (f"Are you sure you want to clear all memory for {ctx.guild.name}? "
                           "This action cannot be undone.")
                    await ctx.respond(msg, view=confirm_view, ephemeral=True)
                    return
                    
                # Get server memory
                server_memory = await db_manager.get_server_memory(str(ctx.guild.id))
                if server_memory and server_memory.get("known_facts"):
                    try:
                        facts = json.loads(server_memory["known_facts"])
                        if facts:
                            embed = discord.Embed(
                                title=f"Server Memory for {ctx.guild.name}",
                                description="Server-wide facts and information",
                                color=discord.Color.blue()
                            )
                            
                            for key, value in facts.items():
                                # Truncate long values
                                if len(str(value)) > 1024:
                                    value = str(value)[:1021] + "..."
                                embed.add_field(name=key.replace("_", " ").title(), value=str(value), inline=False)
                            
                            await ctx.respond(embed=embed, ephemeral=True)
                        else:
                            await ctx.respond("No server memory found.", ephemeral=True)
                    except json.JSONDecodeError:
                        await ctx.respond("No server memory found.", ephemeral=True)
                else:
                    await ctx.respond("No server memory found.", ephemeral=True)
                    
            else:  # target == "user"
                # Determine which user's memory to retrieve
                target_user = user if user else ctx.author
                target_user_id = str(target_user.id)
                
                # Handle clear option for user
                if clear:
                    # Check permissions
                    if not ctx.author.guild_permissions.manage_guild:
                        await ctx.respond("You need 'Manage Server' permissions to clear user memory.", ephemeral=True)
                        return
                    
                    # Confirm with the user before clearing memory
                    confirm_view = ConfirmClearView(ctx.author, target_user, db_manager, target="user")
                    msg = (f"Are you sure you want to clear all memory for {target_user.display_name}? "
                           "This action cannot be undone.")
                    await ctx.respond(msg, view=confirm_view, ephemeral=True)
                    return
                
                # Get user memory
                user_memory = await db_manager.get_user_memory(target_user_id)
                if user_memory and user_memory.get("known_facts"):
                    try:
                        facts = json.loads(user_memory["known_facts"])
                        if facts:
                            embed = discord.Embed(
                                title=f"Memory for {target_user.display_name}",
                                description=f"Personal facts and information for {target_user.mention}",
                                color=discord.Color.green()
                            )
                            
                            for key, value in facts.items():
                                # Truncate long values
                                if len(str(value)) > 1024:
                                    value = str(value)[:1021] + "..."
                                embed.add_field(name=key.replace("_", " ").title(), value=str(value), inline=False)
                            
                            await ctx.respond(embed=embed, ephemeral=True)
                        else:
                            msg = f"No personal memory found for {target_user.mention}."
                            await ctx.respond(msg, ephemeral=True)
                    except json.JSONDecodeError:
                        await ctx.respond(f"No personal memory found for {target_user.mention}.", ephemeral=True)
                else:
                    await ctx.respond(f"No personal memory found for {target_user.mention}.", ephemeral=True)
                    
        except Exception as e:
            logger.error(f"Error retrieving memory: {e}")
            await ctx.respond("Error retrieving memory.", ephemeral=True)
    
    logger.info("Memory commands setup completed")


class ConfirmClearView(discord.ui.View):
    def __init__(self, command_user, target_entity, db_manager, target="user"):
        super().__init__(timeout=60)
        self.command_user = command_user
        self.target_entity = target_entity
        self.db_manager = db_manager
        self.target = target  # "user" or "server"
    
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Check if the interaction is from the user who initiated the command
        if interaction.user != self.command_user:
            await interaction.response.send_message("You cannot confirm this action.", ephemeral=True)
            return
            
        try:
            if self.target == "user":
                # Clear the user's memory
                user_id = str(self.target_entity.id)
                await self.db_manager.clear_user_memory(user_id)
                msg = f"Successfully cleared memory for {self.target_entity.display_name}."
                await interaction.response.send_message(msg, ephemeral=True)
            else:  # server
                # Clear the server's memory
                guild_id = str(self.target_entity.id)
                await self.db_manager.clear_server_memory(guild_id)
                msg = f"Successfully cleared memory for {self.target_entity.name}."
                await interaction.response.send_message(msg, ephemeral=True)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error clearing memory: {e}")
            await interaction.response.send_message("Error clearing memory.", ephemeral=True)
        
        # Disable the buttons after use
        self.stop()
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Check if the interaction is from the user who initiated the command
        if interaction.user != self.command_user:
            await interaction.response.send_message("You cannot cancel this action.", ephemeral=True)
            return
            
        await interaction.response.send_message("Memory clear operation cancelled.", ephemeral=True)
        
        # Disable the buttons after use
        self.stop()
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)