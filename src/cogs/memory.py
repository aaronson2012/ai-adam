# src/cogs/memory.py

import discord
from discord.ext import commands
import logging
import json

logger = logging.getLogger(__name__)

def setup(bot):
    # Get the database manager from the bot
    db_manager = bot.db_manager
    logger.info("Setting up memory commands")
    
    @bot.slash_command(name="memory", description="Retrieve memory information")
    async def memory(ctx: discord.ApplicationContext,
                     target: discord.Option(str, "Target memory type", 
                                          choices=["user", "server"], 
                                          default="user") = "user",
                     user: discord.Option(discord.Member, "Specific user to retrieve memory for (only for user target)", 
                                        required=False) = None):
        """Retrieve memory information"""
        # Log the command execution
        logger.info(f"Memory command executed by {ctx.author} in guild {ctx.guild.id if ctx.guild else 'DM'}")
        logger.info(f"Requested target: {target}, user: {user}")
        
        try:
            if target == "server":
                # Check if in a guild
                if not ctx.guild:
                    await ctx.respond("Server memory can only be accessed in a server.", ephemeral=True)
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
                            
                            await ctx.respond(embed=embed)
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
                            
                            await ctx.respond(embed=embed)
                        else:
                            await ctx.respond(f"No personal memory found for {target_user.mention}.", ephemeral=True)
                    except json.JSONDecodeError:
                        await ctx.respond(f"No personal memory found for {target_user.mention}.", ephemeral=True)
                else:
                    await ctx.respond(f"No personal memory found for {target_user.mention}.", ephemeral=True)
                    
        except Exception as e:
            logger.error(f"Error retrieving memory: {e}")
            await ctx.respond("Error retrieving memory.", ephemeral=True)
    
    logger.info("Memory commands setup completed")