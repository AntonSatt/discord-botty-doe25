# Short Tutorial: Automate Discord Bot Deployment to DigitalOcean Droplet via GitHub Actions

This guide assumes you have:

- A GitHub repo with your Discord bot code (e.g., the `discord-botty-doe25` one).
- A running DigitalOcean Droplet (Ubuntu-based) with root SSH access and your bot's dependencies installed.
- Basic familiarity with Git, SSH, and systemd.

We'll set up a workflow that deploys on push to main: SSH into the Droplet, pull latest code, upgrade deps, and restart the bot service.

## Step 1: Prep Your Droplet

SSH into your Droplet:

```
ssh root@your-droplet-ip
```

Clone your repo:

```
cd /root/devopsuser/bot-app && git clone https://github.com/AntonSatt/discord-botty-doe25.git
```

Set up virtual env:

```
cd discord-botty-doe25 && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

Create a systemd service for the bot (e.g., `/etc/systemd/system/discord-bot.service`):

```
[Unit]
Description=Discord Bot
After=network.target

[Service]
User=root
WorkingDirectory=/root/devopsuser/bot-app/discord-botty-doe25
ExecStart=/root/devopsuser/bot-app/discord-botty-doe25/venv/bin/python bot.py  # Adjust to your main script
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable & start:

```
systemctl daemon-reload && systemctl enable discord-bot && systemctl start discord-bot
```

Test:

```
systemctl status discord-bot
```

(Should be active.)

## Step 2: Generate SSH Key Pair

On your local machine:

```
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/id_ed25519_droplet
```

Add public key to Droplet:

```
cat ~/.ssh/id_ed25519_droplet.pub | ssh root@your-droplet-ip "cat >> ~/.ssh/authorized_keys"
```

Test SSH:

```
ssh -i ~/.ssh/id_ed25519_droplet root@your-droplet-ip
```

(Should log in without passphrase.)

## Step 3: Add GitHub Secrets

Go to your repo on GitHub > Settings > Secrets and variables > Actions.

Add these:

- `DROPLET_HOST`: Your Droplet's IP (e.g., `123.456.78.90`).
- `SSH_PRIVATE_KEY`: Contents of your private key file (`cat ~/.ssh/id_ed25519_droplet`—paste the whole thing, including `-----BEGIN...`).

## Step 4: Create the Workflow File

In your repo, create `.github/workflows/deploy.yml` (commit & push to main).

Paste this YAML (tweaked from your earlier one for safety):

```yaml
name: Deploy to Droplet
on:
  push:
    branches: [ main ]
permissions:
  contents: read  # Minimal perms
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Deploy via SSH
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets.DROPLET_HOST }}
        username: root
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        script: |
          cd /root/devopsuser/bot-app/discord-botty-doe25
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt --upgrade
          systemctl restart discord-bot
```

Commit & push:

```
git add .github/workflows/deploy.yml && git commit -m "Add deploy workflow" && git push origin main
```

## Step 5: Test & Monitor

Make a small code change (e.g., add a log line to your bot), commit & push to main.

Watch it deploy: GitHub > Actions tab > See the "Deploy to Droplet" run (green check = success).

On Droplet:

```
systemctl status discord-bot
```

(Logs via `journalctl -u discord-bot -f`.)

### Troubleshooting

- SSH fails? Check key perms (600) and `authorized_keys`.
- Bot crashes? Verify paths/script in systemd & workflow.
- Rate limits? Add `env: GIT_SSH_COMMAND: "ssh -o StrictHostKeyChecking=no"` to the SSH step.

Boom—your bot auto-deploys on pushes! For class collabs, add branch protection (as we discussed) to avoid workflow tweaks. If issues, share error logs.