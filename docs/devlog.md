# Devlog - Discord bot
## Wednesday November 13th, 2025 (Evening Update)
### Fixed !inactive Command:
- **Problem**: Command only scanned the current channel, missing most server members
- **Solution**: Now scans ALL server members and checks activity across all text channels
- Changes made:
  - Fetches complete member list using `guild.members`
  - Scans message history across all accessible text channels (100 messages per channel)
  - Uses member join date as fallback if no messages found
  - Added progress status messages during scan
  - Better error handling for missing permissions
  - Enabled `intents.members = True` in code
- Command now works properly in large servers with many members

## Wednesday November 13th, 2025
### Things that were done today:
- Added comprehensive safety features to prevent bot abuse:
  - **DM Blocking**: Bot now refuses to respond to Direct Messages
  - **Rate Limiting**: 3-second cooldown between any commands per user
  - **Command Cooldowns**: 30-second cooldown for expensive commands (AI, scanning)
  - **Anti-Spam Detection**: Tracks message frequency (max 10/minute) with automatic 60s mute
  - **Enhanced Error Handling**: Timeout protection, better error messages, API validation
- Created SAFETY_FEATURES.md documentation
- All safety parameters are configurable at the top of bot.py

### Benefits:
- Prevents command spam and abuse
- Protects API costs (AI calls are rate-limited)
- Better user experience with clear feedback
- Automatic spam muting keeps servers clean
- Server-only operation prevents DM harassment

## Satuday 27th of September 2025
### Things that was done today:
- Made a workflow for autodeployment of the Discord chat bot to my digitalocean droplet.
- Figured out how GitHub Actions worked.
- Setting up SSH-keys for GitHub and the Droplet.
- Autodeployment of new code and restarts bot on the droplet from just git push in the code editor. 

### Things that I struggled with:
- It a little while to get the autodeployment to work with GitHub Actions 
    - Why? It was messy to get GitHub to connect to the Droplet. SSH failed a few times. When looking back at it I think it was because did a typo or something to do with chmod 600 ~/.ssh/authorized_keys. Not sure. 

### Fixed workflow for develop branch
- Had problems with workflow.