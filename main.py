"""
Discord Music Recommendation Bot
Main entry point for the bot application
"""

import os
import asyncio
import logging
from bot import MusicBot
from keep_alive import keep_alive
from utils.logger import setup_logging

def main():
    """Main function to start the bot"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Start the keep-alive server
    keep_alive()
    
    # Get bot token from environment
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables")
        return
    
    # Create and run the bot
    bot = MusicBot()
    
    try:
        bot.run(token)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Bot crashed with error: {e}")

if __name__ == "__main__":
    main()
