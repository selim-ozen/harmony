"""
Main bot class and setup
"""

import os
import logging
import discord
from discord.ext import commands
from database import DatabaseManager
from config import Config

class MusicBot(commands.Bot):
    """Main bot class"""
    
    def __init__(self):
        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        
        super().__init__(
            command_prefix=Config.PREFIX,
            intents=intents,
            help_command=None
        )
        
        self.logger = logging.getLogger(__name__)
        self.db = DatabaseManager()
        
    async def setup_hook(self):
        """Setup hook called when bot is starting"""
        self.logger.info("Setting up bot...")
        
        # Initialize database
        await self.db.initialize()
        
        # Set up Spotify auth with proper redirect URI
        from spotify_auth import SpotifyAuthManager
        from keep_alive import set_spotify_auth, set_bot_instance
        
        # Set redirect URI to current Replit URL
        import os
        if 'REPL_ID' in os.environ:
            redirect_uri = f"https://{os.environ.get('REPL_ID')}.{os.environ.get('REPLIT_DOMAINS', 'replit.app')}/callback"
        else:
            redirect_uri = "http://localhost:5000/callback"
        
        os.environ['SPOTIFY_REDIRECT_URI'] = redirect_uri
        self.logger.info(f"Set Spotify redirect URI to: {redirect_uri}")
        
        # Initialize Spotify auth
        self.spotify_auth = SpotifyAuthManager()
        set_spotify_auth(self.spotify_auth)
        set_bot_instance(self)
        
        # Load cogs
        await self.load_cogs()
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            self.logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            self.logger.error(f"Failed to sync slash commands: {e}")
    
    async def load_cogs(self):
        """Load all bot cogs"""
        cogs_to_load = [
            'cogs.music',
            'cogs.admin'
        ]
        
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                self.logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                self.logger.error(f"Failed to load cog {cog}: {e}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        self.logger.info(f"{self.user} has connected to Discord!")
        self.logger.info(f"Bot is in {len(self.guilds)} guilds")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name="your music preferences"
        )
        await self.change_presence(activity=activity)
    
    async def on_guild_join(self, guild):
        """Called when bot joins a new guild"""
        self.logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
    
    async def on_guild_remove(self, guild):
        """Called when bot leaves a guild"""
        self.logger.info(f"Left guild: {guild.name} (ID: {guild.id})")
    
    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        self.logger.error(f"Command error in {ctx.command}: {error}")
        
        if ctx.interaction:
            if not ctx.interaction.response.is_done():
                await ctx.interaction.response.send_message(
                    "An error occurred while processing your command.",
                    ephemeral=True
                )
        else:
            await ctx.send("An error occurred while processing your command.")
