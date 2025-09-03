# src/cogs/personality.py

import discord
from discord.ext import commands
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
    @bot.slash_command(name="personality_list", description="List available personalities")
    async def personality_list(ctx: discord.ApplicationContext):
        """List all available personalities."""
        personalities = get_available_personalities()
        personality_list = "\n".join([f"- {name}: {get_personality(name)['description']}" for name in personalities])
        
        embed = discord.Embed(
            title="Available Personalities",
            description=personality_list,
            color=discord.Color.blue()
        )
        
        await ctx.respond(embed=embed, ephemeral=True)

    @bot.slash_command(name="personality_current", description="Show the current personality")
    async def personality_current(ctx: discord.ApplicationContext):
        """Show the current personality for this server."""
        current = get_server_personality(ctx.guild.id if ctx.guild else "default")
        personality_data = get_personality(current)
        
        embed = discord.Embed(
            title="Current Personality",
            description=f"**{personality_data['name']}**\n{personality_data['description']}",
            color=discord.Color.green()
        )
        
        await ctx.respond(embed=embed, ephemeral=True)

    @bot.slash_command(name="personality_set", description="Set the bot's personality")
    @commands.has_permissions(manage_guild=True)
    async def personality_set(ctx: discord.ApplicationContext, 
                            name: discord.Option(str, "The personality to set", 
                                               choices=get_available_personalities())):
        """Set the bot's personality for this server."""
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