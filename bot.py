import os
import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from dotenv import load_dotenv
import asyncio
from utils.captcha import generate_captcha, verify_captcha
from utils.minecraft_api import add_to_whitelist
from utils.floodgate_api import verify_floodgate_uuid, get_bedrock_fuid
from utils.user_input import get_user_input, get_confirmation
from utils.ip_tracker import IPTracker
from aiohttp import web

# Load environment variables
load_dotenv()

# Bot configuration
TOKEN = os.getenv('DISCORD_TOKEN')
ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID', '0'))
MINECRAFT_CONSOLE_CHANNEL_ID = int(os.getenv('MINECRAFT_CONSOLE_CHANNEL_ID', '0'))
TIMER_CHANNEL_ID = int(os.getenv('TIMER_CHANNEL_ID', '0'))
NOTIFICATION_ROLE_ID = 1361879960347738366
WHITELISTED_ROLE_ID = 1361879960347738366
WHITELIST_CHANNEL_ID = 1361880186735300618
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'
TEST_DAY = int(os.getenv('TEST_DAY', '-1'))

# Bot setup with all required intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Store the last embed message for event bot
last_embed_message = None
ip_tracker = IPTracker()

# Event Bot Functions
def get_current_time():
    """Get current time, or simulated time if in test mode"""
    now = datetime.now()
    if TEST_MODE and TEST_DAY >= 0:
        current_day = now.weekday()
        days_diff = TEST_DAY - current_day
        return now + timedelta(days=days_diff)
    return now

def get_next_weekend():
    """Calculate the time until next weekend (Saturday or Sunday)"""
    now = datetime.now()
    days_until_weekend = (5 - now.weekday()) % 7
    if days_until_weekend == 0 and now.hour >= 0:
        days_until_weekend = 7
    next_weekend = now + timedelta(days=days_until_weekend)
    next_weekend = next_weekend.replace(hour=0, minute=0, second=0, microsecond=0)
    return next_weekend

def get_next_weekday():
    """Calculate the time until next Monday"""
    now = datetime.now()
    days_until_monday = (7 - now.weekday()) % 7
    if days_until_monday == 0 and now.hour >= 0:
        days_until_monday = 7
    next_monday = now + timedelta(days=days_until_monday)
    next_monday = next_monday.replace(hour=0, minute=0, second=0, microsecond=0)
    return next_monday

def format_time_remaining(target_time):
    """Format the time remaining until the target time"""
    now = datetime.now()
    time_diff = target_time - now
    days = time_diff.days
    hours = time_diff.seconds // 3600
    minutes = (time_diff.seconds % 3600) // 60
    return f"{days} days, {hours} hours, and {minutes} minutes"

async def send_status_embed(channel, is_disabled, force_new=False):
    """Send or update status embed in the timer channel"""
    global last_embed_message
    
    if is_disabled:
        next_time = get_next_weekend()
        title = "Infinity Caves Status"
        description = f"Infinity Caves is disabled until {next_time.strftime('%A, %B %d, %Y')}"
        color = discord.Color.red()
    else:
        next_time = get_next_weekday()
        title = "Infinity Caves Status"
        description = f"Infinity Caves is open until {next_time.strftime('%A, %B %d, %Y')}"
        color = discord.Color.green()

    time_remaining = format_time_remaining(next_time)
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    embed.add_field(
        name="Time Remaining",
        value=time_remaining,
        inline=False
    )
    
    try:
        if last_embed_message and not force_new:
            await last_embed_message.edit(embed=embed)
        else:
            last_embed_message = await channel.send(embed=embed)
            if force_new:
                await channel.send(f"<@&{NOTIFICATION_ROLE_ID}>")
    except discord.NotFound:
        last_embed_message = await channel.send(embed=embed)
        if force_new:
            await channel.send(f"<@&{NOTIFICATION_ROLE_ID}>")
    except Exception as e:
        print(f"Error updating embed: {e}")
        last_embed_message = await channel.send(embed=embed)
        if force_new:
            await channel.send(f"<@&{NOTIFICATION_ROLE_ID}>")

# Whitelister Bot Functions
async def send_whitelist_instructions():
    """Send whitelist instructions embed to the whitelist channel."""
    try:
        channel = bot.get_channel(WHITELIST_CHANNEL_ID)
        if channel:
            pinned_messages = await channel.pins()
            for message in pinned_messages:
                if message.author == bot.user:
                    await message.unpin()
            
            embed = discord.Embed(
                title="🎮 Minecraft Server Whitelist",
                description="Welcome to the whitelist process! Follow these steps to get whitelisted:",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="1️⃣ Start the Process",
                value="Use `/whitelist` to begin the whitelist process",
                inline=False
            )
            
            embed.add_field(
                name="2️⃣ Solve CAPTCHA",
                value="You'll be asked to solve a CAPTCHA to verify you're human",
                inline=False
            )
            
            embed.add_field(
                name="3️⃣ Enter Minecraft Username",
                value="Provide your Minecraft username (Java or Bedrock)",
                inline=False
            )
            
            embed.add_field(
                name="4️⃣ Select Account Type",
                value="Choose whether you have a Java or Bedrock account",
                inline=False
            )
            
            embed.add_field(
                name="📝 Important Notes",
                value=(
                    "• Make sure to use your correct Minecraft username\n"
                    "• Bedrock players need to have their account linked\n"
                    "• You can only whitelist one account per Discord user\n"
                    "• Your Discord nickname will be updated to your Minecraft username"
                ),
                inline=False
            )
            
            embed.add_field(
                name="❓ Need Help?",
                value="If you encounter any issues, please contact a server administrator",
                inline=False
            )
            
            embed.set_footer(text="Meowcraft Whitelist System")
            
            message = await channel.send(embed=embed)
            await message.pin()
    except Exception as e:
        print(f"Error sending whitelist instructions: {e}")

async def send_welcome_message(member):
    """Send welcome message with pings after successful whitelisting."""
    try:
        welcome_channel = bot.get_channel(1361877511624982661)
        if welcome_channel:
            await welcome_channel.send(f"{member.mention}")
            
            embed = discord.Embed(
                title="🎉 Welcome to Meowcraft!",
                description="We're glad to have you join our community!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📜 Rules",
                value=f"Please read our rules in <#1361913484681412821>",
                inline=False
            )
            
            embed.add_field(
                name="🌐 Server Information",
                value=f"Find our server IP in <#1362668740621369484>",
                inline=False
            )
            
            embed.set_footer(text="Enjoy your stay at Meowcraft!")
            
            await welcome_channel.send(embed=embed)
            return True
    except Exception as e:
        print(f"Error sending welcome message: {e}")
        return False

async def assign_whitelisted_role(member):
    """Assign the whitelisted role to a member."""
    try:
        whitelisted_role = member.guild.get_role(WHITELISTED_ROLE_ID)
        if whitelisted_role:
            if member.guild.me.guild_permissions.manage_roles:
                await member.add_roles(whitelisted_role)
                return True
            else:
                print("Bot doesn't have permission to manage roles")
                return False
        return False
    except Exception as e:
        print(f"Error assigning role: {e}")
        return False

async def rename_member(member, new_name):
    """Rename a member to their Minecraft username."""
    try:
        if member.guild.me.guild_permissions.manage_nicknames:
            await member.edit(nick=new_name)
            return True
        else:
            print("Bot doesn't have permission to manage nicknames")
            return False
    except Exception as e:
        print(f"Error renaming member: {e}")
        return False

def is_whitelist_channel():
    """Check if the command is being used in the whitelist channel."""
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.channel_id != WHITELIST_CHANNEL_ID:
            try:
                await interaction.response.send_message(
                    f"This command can only be used in the whitelist channel! Please go to <#{WHITELIST_CHANNEL_ID}>", 
                    ephemeral=True
                )
            except Exception as e:
                print(f"Error sending channel check message: {e}")
            return False
        return True
    return app_commands.check(predicate)

# HTTP Server for Render
async def handle_health_check(request):
    return web.Response(text="Bot is running!")

async def start_http_server():
    app = web.Application()
    app.router.add_get('/', handle_health_check)
    port = int(os.getenv('PORT', 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"HTTP server started on port {port}")

# Bot Events
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    
    # Sync commands with Discord
    try:
        print("Available commands:")
        for cmd in bot.tree.get_commands():
            print(f"- /{cmd.name}")
        
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s):")
        for cmd in synced:
            print(f"- /{cmd.name}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    
    # Update presence
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="Meowcraft Server",
        details="Managing whitelist and events",
        state="Online"
    )
    await bot.change_presence(activity=activity, status=discord.Status.online)
    
    # Send whitelist instructions
    await send_whitelist_instructions()
    
    # Start the background task for event bot
    check_time.start()
    
    # Start HTTP server
    await start_http_server()

# Event Bot Tasks
@tasks.loop(minutes=1)
async def check_time():
    """Background task to check time and manage mob spawning state"""
    now = get_current_time()
    is_weekend = now.weekday() >= 5
    
    minecraft_channel = bot.get_channel(MINECRAFT_CONSOLE_CHANNEL_ID)
    timer_channel = bot.get_channel(TIMER_CHANNEL_ID)
    
    if not minecraft_channel or not timer_channel:
        return
    
    if now.hour == 0 and now.minute == 0:
        if now.weekday() == 0:  # Monday
            print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Disabling mobs - Monday midnight")
            await minecraft_channel.send("function infinity_cave:settings/disable_spawning")
            await send_status_embed(timer_channel, True, force_new=True)
        elif now.weekday() == 5:  # Saturday
            print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Enabling mobs - Saturday midnight")
            await minecraft_channel.send("function infinity_cave:settings/disable_spawning")
            await send_status_embed(timer_channel, False, force_new=True)
    
    if TEST_MODE or now.minute == 0:
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Updating embed - {'Test mode' if TEST_MODE else 'Hourly'} update")
        await send_status_embed(timer_channel, not is_weekend)

# Event Bot Commands
@bot.tree.command(name="disablemobs", description="Disable mob spawning and show countdown to next weekend")
async def disablemobs(interaction: discord.Interaction):
    if not any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    minecraft_channel = bot.get_channel(MINECRAFT_CONSOLE_CHANNEL_ID)
    timer_channel = bot.get_channel(TIMER_CHANNEL_ID)

    if not minecraft_channel or not timer_channel:
        await interaction.response.send_message("Error: Required channels are not configured properly.", ephemeral=True)
        return

    await interaction.response.send_message("Command received, processing...", ephemeral=True)
    await minecraft_channel.send("function infinity_cave:settings/disable_spawning")
    await send_status_embed(timer_channel, True, force_new=True)
    await interaction.followup.send("Command executed successfully!", ephemeral=True)

@bot.tree.command(name="testday", description="Test the bot with a specific day of the week (Admin only)")
async def testday(interaction: discord.Interaction, day: int):
    if not any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    if not 0 <= day <= 6:
        await interaction.response.send_message("Day must be between 0 (Monday) and 6 (Sunday).", ephemeral=True)
        return
    
    global TEST_DAY
    TEST_DAY = day
    
    current_day = datetime.now().weekday()
    days_diff = day - current_day
    now = datetime.now() + timedelta(days=days_diff)
    is_weekend = day >= 5
    
    await interaction.response.send_message(f"Testing with day {day} ({now.strftime('%A')})", ephemeral=True)
    
    timer_channel = bot.get_channel(TIMER_CHANNEL_ID)
    if timer_channel:
        await send_status_embed(timer_channel, not is_weekend, force_new=True)

# Whitelister Bot Commands
@bot.tree.command(
    name="whitelist",
    description="Start the whitelist process"
)
@is_whitelist_channel()
async def whitelist(interaction: discord.Interaction):
    """Start the whitelist process for Minecraft server access."""
    try:
        await interaction.response.defer(ephemeral=True)
        
        ip_address = interaction.user.id
        channel = interaction.channel
        
        captcha_text, captcha_path = generate_captcha()
        
        await interaction.followup.send(
            "Please solve this CAPTCHA to continue with the whitelist process:",
            file=discord.File(captcha_path),
            ephemeral=True
        )
        
        try:
            user_input = await get_user_input(bot, interaction.user, channel)
            if not user_input:
                await interaction.followup.send("No response received. Please try the command again.", ephemeral=True)
                return
                
            if verify_captcha(user_input, captcha_text):
                await interaction.followup.send("CAPTCHA verified! Please enter your Minecraft username:", ephemeral=True)
                minecraft_username = await get_user_input(bot, interaction.user, channel)
                if not minecraft_username:
                    await interaction.followup.send("No response received. Please try the command again.", ephemeral=True)
                    return
                
                can_whitelist, message = ip_tracker.can_whitelist(ip_address, minecraft_username)
                if not can_whitelist:
                    await interaction.followup.send(message, ephemeral=True)
                    return
                
                await interaction.followup.send("What type of account do you have? (Type 'java' or 'bedrock'):", ephemeral=True)
                account_type = await get_user_input(bot, interaction.user, channel)
                if not account_type:
                    await interaction.followup.send("No response received. Please try the command again.", ephemeral=True)
                    return
                
                console_channel = bot.get_channel(MINECRAFT_CONSOLE_CHANNEL_ID)
                if not console_channel:
                    await interaction.followup.send("Error: Console channel not found!", ephemeral=True)
                    return
                
                success = False
                if account_type.lower() == 'java':
                    success = await add_to_whitelist(console_channel, minecraft_username)
                elif account_type.lower() == 'bedrock':
                    fuid, gamertag = await get_bedrock_fuid(minecraft_username)
                    if fuid and gamertag:
                        success = await add_to_whitelist(console_channel, gamertag, is_bedrock=True, fuid=fuid)
                    else:
                        await interaction.followup.send("Error: Could not verify Bedrock account. Please make sure your gamertag is correct.", ephemeral=True)
                        return
                
                if success:
                    role_success = await assign_whitelisted_role(interaction.user)
                    rename_success = await rename_member(interaction.user, minecraft_username)
                    
                    if not role_success:
                        await interaction.followup.send("Warning: Could not assign whitelisted role. Please contact an administrator.", ephemeral=True)
                    if not rename_success:
                        await interaction.followup.send("Warning: Could not update your nickname. Please contact an administrator.", ephemeral=True)
                    
                    await send_welcome_message(interaction.user)
                    await interaction.followup.send("Successfully whitelisted! Welcome to the server!", ephemeral=True)
                else:
                    await interaction.followup.send("Error: Failed to whitelist. Please contact an administrator.", ephemeral=True)
            else:
                await interaction.followup.send("Invalid CAPTCHA. Please try again.", ephemeral=True)
        except Exception as e:
            print(f"Error in whitelist process: {e}")
            await interaction.followup.send("An error occurred during the whitelist process. Please try again later.", ephemeral=True)
    except Exception as e:
        print(f"Error in whitelist command: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("An error occurred. Please try again later.", ephemeral=True)

@bot.tree.command(name="status", description="Check whitelist status")
@is_whitelist_channel()
async def status(interaction: discord.Interaction):
    await interaction.response.send_message("Whitelist system is operational!", ephemeral=True)

@bot.tree.command(name="instructions", description="Resend the whitelist instructions")
@is_whitelist_channel()
async def resend_instructions(interaction: discord.Interaction):
    await send_whitelist_instructions()
    await interaction.response.send_message("Instructions have been resent!", ephemeral=True)

# Run the bot
if __name__ == "__main__":
    bot.run(TOKEN) 