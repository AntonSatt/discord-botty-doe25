import os
import discord
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
AI_API_TOKEN = os.getenv('OPENROUTER_API_KEY')  # Or change to 'OpenRouterAPIKey' if that's your .env name

# Create an instance of the bot with command prefix
intents = discord.Intents.default()
intents.message_content = True  # Enable reading message content
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} has logged in!')  # Confirm it's working

@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == client.user:
        return

    if message.content.startswith('!'):
        command = message.content.split()[0][1:]
        if command == 'help':
            await message.channel.send('Current commands: !help, !ping, !meme, !roast me')
        elif command == 'ping':
            await message.channel.send('PongPongBong!')
        elif command == 'meme':
            await message.channel.send('https://i.imgur.com/ljHAAuL.png')

    if message.content.startswith('!roast me'):
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {AI_API_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "model": "x-ai/grok-4-fast:free",
                "messages": [
                    {
                        "role": "user",
                        "content": f"Write a short, brutal, funny roast for Discord user {message.author.name}. Keep it Discord-safe, under 50 words."
                    }
                ],
            }
        )
        if response.status_code == 200:
            roast = response.json()['choices'][0]['message']['content']
            await message.channel.send(roast)
        else:
            await message.channel.send(f"Oof, roast failed: {response.status_code}. Try again?")

# Run the bot with your token
client.run(TOKEN)