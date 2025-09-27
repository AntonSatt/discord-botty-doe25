# Devlog - Discord bot
## Satuday 27th of September 2025
### Things that was done today:
- Made a workflow for autodeployment of the Discord chat bot to my digitalocean droplet.
- Figured out how GitHub Actions worked.
- Setting up SSH-keys for GitHub and the Droplet.
- Autodeployment of new code and restarts bot on the droplet from just git push in the code editor. 

### Things that I struggled with:
- It a little while to get the autodeployment to work with GitHub Actions 
    - Why? It was messy to get GitHub to connect to the Droplet. SSH failed a few times. When looking back at it I think it was because did a typo or something to do with chmod 600 ~/.ssh/authorized_keys. Not sure. 