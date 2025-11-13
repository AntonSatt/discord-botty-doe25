import os
import discord
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta
from collections import defaultdict

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
AI_API_TOKEN = os.getenv('OPENROUTER_API_KEY')  # Or change to 'OpenRouterAPIKey' if that's your .env name

# IMPORTANT: Replace this with your Discord User ID
# To get your ID: Enable Developer Mode in Discord settings, right-click your name, "Copy User ID"
OWNER_ID = 172342196945551361  # Replace with your actual Discord user ID (e.g., 123456789012345678)

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

    # Hardcoded messages
    if message.content.startswith('!'):
        command = message.content.split()[0][1:]
        print(f"Command received: '{command}' from message: '{message.content}'")
        if command == 'help':
            await message.channel.send('Current commands: !help, !ping, !meme, !roast me, !inactive')
        elif command == 'ping':
            await message.channel.send('You pinged? :)')
        elif command == 'meme':
            await message.channel.send('https://i.imgur.com/ljHAAuL.png')
        elif command == 'inactive':
            print(f"!inactive command triggered by {message.author.name} (ID: {message.author.id})")
            print(f"OWNER_ID is set to: {OWNER_ID}")
            
            # Permission check: Only the owner can use this command
            if message.author.id != OWNER_ID:
                await message.channel.send("❌ Permission Denied. This command is owner-only.")
                return
            
            # Send a "processing" message since this might take a moment
            try:
                status_msg = await message.channel.send("🔍 Scanning message history... This may take a moment.")
            except Exception as e:
                print(f"Failed to send status message: {e}")
                return
            
            try:
                # Track last activity time for each user
                user_last_activity = {}
                current_time = datetime.utcnow()
                
                # Scan the last 2000 messages (adjust this limit as needed)
                # For very large servers, you might want to reduce this to 1000
                message_count = 0
                async for msg in message.channel.history(limit=2000):
                    message_count += 1
                    # Skip bot messages
                    if msg.author.bot:
                        continue
                    
                    # Track the most recent message for each user
                    if msg.author.id not in user_last_activity:
                        user_last_activity[msg.author.id] = {
                            'name': msg.author.display_name,
                            'last_seen': msg.created_at
                        }
                
                print(f"Scanned {message_count} messages, found {len(user_last_activity)} unique users")
                
                # Categorize users by inactivity period
                inactive_7_days = []
                inactive_14_days = []
                inactive_30_days = []
                
                for user_id, data in user_last_activity.items():
                    days_inactive = (current_time - data['last_seen']).days
                    
                    if days_inactive >= 30:
                        inactive_30_days.append((data['name'], days_inactive))
                    elif days_inactive >= 14:
                        inactive_14_days.append((data['name'], days_inactive))
                    elif days_inactive >= 7:
                        inactive_7_days.append((data['name'], days_inactive))
                
                # Sort each category by days inactive (most inactive first)
                inactive_7_days.sort(key=lambda x: x[1], reverse=True)
                inactive_14_days.sort(key=lambda x: x[1], reverse=True)
                inactive_30_days.sort(key=lambda x: x[1], reverse=True)
                
                # Create an embed for the report
                embed = discord.Embed(
                    title="📊 User Inactivity Report",
                    description=f"Scanned {message_count} messages in this channel",
                    color=discord.Color.blue(),
                    timestamp=current_time
                )
                
                # Add fields for each category
                if inactive_30_days:
                    users_list = "\n".join([f"• {name} ({days} days)" for name, days in inactive_30_days[:10]])
                    if len(inactive_30_days) > 10:
                        users_list += f"\n... and {len(inactive_30_days) - 10} more"
                    embed.add_field(
                        name=f"🔴 Inactive 30+ Days ({len(inactive_30_days)} users)",
                        value=users_list or "None",
                        inline=False
                    )
                
                if inactive_14_days:
                    users_list = "\n".join([f"• {name} ({days} days)" for name, days in inactive_14_days[:10]])
                    if len(inactive_14_days) > 10:
                        users_list += f"\n... and {len(inactive_14_days) - 10} more"
                    embed.add_field(
                        name=f"🟡 Inactive 14-29 Days ({len(inactive_14_days)} users)",
                        value=users_list or "None",
                        inline=False
                    )
                
                if inactive_7_days:
                    users_list = "\n".join([f"• {name} ({days} days)" for name, days in inactive_7_days[:10]])
                    if len(inactive_7_days) > 10:
                        users_list += f"\n... and {len(inactive_7_days) - 10} more"
                    embed.add_field(
                        name=f"🟢 Inactive 7-13 Days ({len(inactive_7_days)} users)",
                        value=users_list or "None",
                        inline=False
                    )
                
                # If no inactive users found
                if not inactive_7_days and not inactive_14_days and not inactive_30_days:
                    embed.description = f"Scanned {message_count} messages in this channel\n\n✅ No inactive users found in the specified timeframes!"
                
                embed.set_footer(text=f"Total unique users found: {len(user_last_activity)}")
                
                # Delete the status message and send the report
                await status_msg.delete()
                await message.channel.send(embed=embed)
                print("Report sent successfully!")
                
            except discord.Forbidden as e:
                print(f"Permission error: {e}")
                try:
                    await status_msg.edit(content="❌ Error: I don't have permission to read message history in this channel.")
                except:
                    await message.channel.send("❌ Error: I don't have permission to read message history in this channel.")
            except Exception as e:
                print(f"Error in !inactive command: {e}")
                import traceback
                traceback.print_exc()
                try:
                    await status_msg.edit(content=f"❌ An error occurred: {str(e)}")
                except:
                    await message.channel.send(f"❌ An error occurred: {str(e)}")

    if message.content.startswith('!roast me'):
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {AI_API_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "model": "google/gemini-2.0-flash-exp:free",
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