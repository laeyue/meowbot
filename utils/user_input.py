import discord
from discord.ext import commands

async def get_user_input(bot, user, channel):
    """Get user input from the channel."""
    def check(m):
        return m.author == user and m.channel == channel
    
    try:
        message = await bot.wait_for('message', check=check, timeout=300.0)
        return message.content.strip()
    except TimeoutError:
        return None

async def get_confirmation(bot, user, channel, message):
    """Get user confirmation (yes/no) from the channel."""
    await channel.send(message)
    
    def check(m):
        return m.author == user and m.channel == channel and m.content.lower() in ['yes', 'no']
    
    try:
        message = await bot.wait_for('message', check=check, timeout=300.0)
        return message.content.lower() == 'yes'
    except TimeoutError:
        return False 