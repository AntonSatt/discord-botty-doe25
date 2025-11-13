# Discord bot for DevOps class DOE25

## Try the bot:
- Add the bot to your discord server: [Invite bot](https://discord.com/oauth2/authorize?client_id=1421000801098141817&permissions=67584&integration_type=0&scope=bot) 

## Commands

- `!help` - Show list of available commands
- `!ping` - Check if bot is responsive
- `!meme` - Get a random meme
- `!roast me` - Get roasted by AI (30s cooldown)
- `!inactive` - **[Owner only]** Check for inactive server members

## !inactive Command Usage

**For Admins/Owners:**

This command helps you identify inactive members in your server. It works privately and securely:

### How to Use:
1. Go to a **private admin channel** (to keep results confidential)
2. Type `!inactive`
3. Wait 10-30 seconds while the bot scans
4. Results appear **only in that channel** - not visible to regular members

### What It Does:
- Scans **ALL text channels** in your server
- Checks the last 100 messages per channel
- Finds when each member last sent a message
- Categories members by inactivity:
  - 🟢 7-13 days inactive
  - 🟡 14-29 days inactive
  - 🔔 30+ days inactive

### Requirements:
The bot needs these permissions enabled in Discord Developer Portal:
- ✅ Server Members Intent
- ✅ Message Content Intent
- ✅ Read Message History permission

### Privacy:
- Results are posted **only** where you run the command
- Perfect for admin/mod channels
- Regular members never see the report

## Safety Features

The bot includes anti-spam and abuse protection:
- **Rate Limiting**: 3-second cooldown between commands
- **AI Cooldowns**: 30-second cooldown for expensive commands
- **Anti-Spam**: Auto-mutes users sending 10+ messages/minute
- **DM Blocking**: Bot only works in servers, not DMs
- **Owner-Only Commands**: Sensitive commands restricted to bot owner

## Development

See [devlog](docs/devlog.md) for development history and updates.

