# src/cogs/memory.py

import discord
from discord.ext import commands
import logging
import json

def setup(bot):
    # Get the database manager from the bot
    db_manager = bot.db_manager
    logger = logging.getLogger(__name__)
    logger.info("Setting up memory commands")
    
    @bot.slash_command(name="memory", description="Get or clear memory information about a user")
    async def memory(ctx: discord.ApplicationContext,
                     user: discord.Option(discord.User, "User to get memory for"),
                     clear: discord.Option(bool, "Clear user's memory", required=False, default=False)):
        """Get memory information about a specific user, optionally clearing it"""
        # Log the command execution
        logger.info(f"Memory command executed by {ctx.author} in guild {ctx.guild.id if ctx.guild else 'DM'} for user {user.id}")
        
        # Check if the user has permission to manage the guild
        if not ctx.author.guild_permissions.manage_guild:
            logger.warning(f"User {ctx.author} attempted to view memory without permission")
            await ctx.respond("You need 'Manage Server' permissions to view user memory.", ephemeral=True)
            return
            
        # Handle clear option
        if clear:
            # Confirm with the user before clearing memory
            confirm_view = ConfirmClearView(ctx.author, user, db_manager)
            await ctx.respond(f"Are you sure you want to clear all memory for {user.name}? This action cannot be undone.", 
                              view=confirm_view, ephemeral=False)
            return
        
        # Get user memory from database
        user_id = str(user.id)
        try:
            user_memory = await db_manager.get_user_memory(user_id)
        except Exception as e:
            logger.error(f"Error retrieving memory for user {user_id}: {e}")
            await ctx.respond("Error retrieving user memory.", ephemeral=True)
            return
        
        # Parse the memory data
        try:
            known_facts = json.loads(user_memory.get("known_facts", "{}"))
            interaction_history = json.loads(user_memory.get("interaction_history", "[]"))
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing memory data for user {user_id}: {e}")
            await ctx.respond("Error parsing user memory data.", ephemeral=True)
            return
        
        # Create an embed to display the memory information
        embed = discord.Embed(
            title=f"Memory for {user.name}",
            description=f"User ID: {user.id}",
            color=discord.Color.blue()
        )
        
        # Add known facts if any
        if known_facts and isinstance(known_facts, dict) and known_facts:
            facts_text = "\n".join([f"• {key}: {value}" for key, value in known_facts.items()])
            embed.add_field(name="Known Facts", value=facts_text[:1024], inline=False)
        else:
            embed.add_field(name="Known Facts", value="No known facts recorded.", inline=False)
        
        # Add interaction history summary
        if interaction_history and isinstance(interaction_history, list) and interaction_history:
            # Count interactions
            interaction_count = len(interaction_history)
            # Get the most recent interaction if available
            recent_interaction = interaction_history[-1] if interaction_history else None
            
            history_summary = f"Total interactions: {interaction_count}"
            if recent_interaction:
                timestamp = recent_interaction.get("timestamp", "Unknown")
                history_summary += f"\nLast interaction: {timestamp}"
            
            embed.add_field(name="Interaction History", value=history_summary, inline=False)
            
            # Add a sample of recent interactions (last 3)
            recent_interactions_text = ""
            for i, interaction in enumerate(interaction_history[-3:]):
                user_msg = interaction.get("user_message", "N/A")
                ai_resp = interaction.get("ai_response", "N/A")
                timestamp = interaction.get("timestamp", "N/A")
                
                # Truncate long messages
                if len(user_msg) > 100:
                    user_msg = user_msg[:100] + "..."
                if len(ai_resp) > 100:
                    ai_resp = ai_resp[:100] + "..."
                
                recent_interactions_text += f"**Interaction {interaction_count-2+i}**\n"
                recent_interactions_text += f"User: {user_msg}\n"
                recent_interactions_text += f"AI: {ai_resp}\n"
                recent_interactions_text += f"Time: {timestamp}\n\n"
            
            if recent_interactions_text:
                embed.add_field(name="Recent Interactions", value=recent_interactions_text[:1024], inline=False)
        else:
            embed.add_field(name="Interaction History", value="No interaction history recorded.", inline=False)
        
        await ctx.respond(embed=embed)
    
    logger.info("Memory commands setup completed")

class ConfirmClearView(discord.ui.View):
    def __init__(self, command_user, target_user, db_manager):
        super().__init__(timeout=60)
        self.command_user = command_user
        self.target_user = target_user
        self.db_manager = db_manager
    
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Check if the interaction is from the user who initiated the command
        if interaction.user != self.command_user:
            await interaction.response.send_message("You cannot confirm this action.", ephemeral=True)
            return
            
        # Clear the user's memory
        try:
            user_id = str(self.target_user.id)
            await self.db_manager.clear_user_memory(user_id)
            await interaction.response.send_message(f"Successfully cleared memory for {self.target_user.name}.", ephemeral=False)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error clearing memory for user {user_id}: {e}")
            await interaction.response.send_message("Error clearing user memory", ephemeral=False)
        
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
            
        await interaction.response.send_message("Memory clear operation cancelled.", ephemeral=False)
        
        # Disable the buttons after use
        self.stop()
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)