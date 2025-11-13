# Devlog - Discord bot
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