import os
import discord
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

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
            await message.channel.send('Current commands: !help, !ping')
        elif command == 'ping':
            await message.channel.send('PongPongBong!')
        elif command == 'meme':
            await message.channel.send('https://i.imgur.com/ljHAAuL.png')
    

# Run the bot wi
# th your token
client.run(TOKEN)