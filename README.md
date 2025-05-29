# Meowcraft Discord Bot

A Discord bot for managing Minecraft server whitelisting and mob spawning events.

## Features

- **Whitelist Management**
  - CAPTCHA verification
  - Support for both Java and Bedrock players
  - Automatic role assignment
  - Nickname updates
  - Welcome messages

- **Mob Spawning Control**
  - Automatic weekend/weekday scheduling
  - Status updates with countdown
  - Role notifications
  - Admin commands for manual control

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/meowcraft-bot.git
   cd meowcraft-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Create a `.env` file with the following variables:
   ```
   # Discord Bot Token
   DISCORD_TOKEN=your_discord_bot_token_here

   # Role IDs
   ADMIN_ROLE_ID=your_admin_role_id_here

   # Channel IDs
   MINECRAFT_CONSOLE_CHANNEL_ID=your_console_channel_id_here
   TIMER_CHANNEL_ID=your_timer_channel_id_here

   # Test Mode (optional)
   TEST_MODE=false
   TEST_DAY=-1

   # Port for HTTP Server (optional)
   PORT=10000
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

## Bot Permissions

The bot requires the following permissions:
- Manage Roles
- Manage Nicknames
- Send Messages
- Embed Links
- Attach Files
- Read Message History

Make sure the bot's role is higher in the server's role hierarchy than the roles it needs to manage.

## Commands

### Whitelist Commands
- `/whitelist` - Start the whitelist process
- `/status` - Check whitelist status
- `/instructions` - Resend whitelist instructions

### Admin Commands
- `/disablemobs` - Disable mob spawning and show countdown
- `/testday` - Test the bot with a specific day of the week

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 