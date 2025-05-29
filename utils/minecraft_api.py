import aiohttp
import os
from dotenv import load_dotenv
import discord

load_dotenv()

MINECRAFT_API_ENDPOINT = os.getenv('MINECRAFT_API_ENDPOINT')

async def add_to_whitelist(console_channel, username, is_bedrock=False, fuid=None):
    """Add a player to the Minecraft server whitelist."""
    try:
        if is_bedrock and fuid:
            # For Bedrock players, first add FUID
            await console_channel.send(f"fwhitelist add {fuid}")
            # Then add with dot prefix
            await console_channel.send(f"wlu add .{username}")
        else:
            # For Java players, just add username
            await console_channel.send(f"wlu add {username}")
        return True
    except Exception as e:
        print(f"Error adding to whitelist: {e}")
        return False 