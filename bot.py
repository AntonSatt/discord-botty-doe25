import os
import discord
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import time
import asyncio
import traceback

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
AI_API_TOKEN = os.getenv('OPENROUTER_API_KEY')  # Or change to 'OpenRouterAPIKey' if that's your .env name
HUMOR_API_KEY = os.getenv('HUMOR_API_KEY')

# IMPORTANT: Replace this with your Discord User ID(s)
# To get your ID: Enable Developer Mode in Discord settings, right-click your name, "Copy User ID"
OWNER_ID = [172342196945551361, 376786371672801280]  # List of authorized user IDs for !inactive command
NUKE_OWNER_ID = 172342196945551361  # Only this user can use !nuke command

# AI MODEL CONFIGURATION
AI_MODEL = "meta-llama/llama-3.3-70b-instruct:free"

# Safety Configuration
RATE_LIMIT_SECONDS = 3  # Minimum seconds between commands per user
COOLDOWN_EXPENSIVE_COMMANDS = 30  # Cooldown for AI/expensive commands (seconds)
MAX_MESSAGES_PER_MINUTE = 10  # Maximum messages from one user per minute
SPAM_MUTE_DURATION = 60  # Seconds to ignore a spammer

# Scanning Configuration
MESSAGE_SCAN_LIMIT = 1000  # Number of messages to scan per channel for !inactive and !nuke

# Tracking dictionaries for safety features
user_last_command = {}  # Track last command time per user
user_command_cooldowns = defaultdict(dict)  # Track cooldowns per command per user
user_message_history = defaultdict(list)  # Track message timestamps for spam detection
spam_muted_users = {}  # Track temporarily muted users

# Create an instance of the bot with command prefix
intents = discord.Intents.default()
intents.message_content = True  # Enable reading message content
intents.members = True  # Enable access to server members (required for !inactive)
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} has logged in!')  # Confirm it's working
    print(f'Safety features enabled:')
    print(f'- Rate limit: {RATE_LIMIT_SECONDS}s between commands')
    print(f'- AI command cooldown: {COOLDOWN_EXPENSIVE_COMMANDS}s')
    print(f'- Anti-spam: Max {MAX_MESSAGES_PER_MINUTE} messages/minute')

def is_spam(user_id):
    """Check if a user is spamming based on message frequency"""
    current_time = time.time()
    
    # Clean old message timestamps (older than 1 minute)
    user_message_history[user_id] = [
        timestamp for timestamp in user_message_history[user_id]
        if current_time - timestamp < 60
    ]
    
    # Add current message timestamp
    user_message_history[user_id].append(current_time)
    
    # Check if user exceeded the limit
    if len(user_message_history[user_id]) > MAX_MESSAGES_PER_MINUTE:
        return True
    return False

def is_muted(user_id):
    """Check if a user is temporarily muted for spamming"""
    if user_id in spam_muted_users:
        if time.time() - spam_muted_users[user_id] < SPAM_MUTE_DURATION:
            return True
        else:
            # Unmute user after duration
            del spam_muted_users[user_id]
    return False

def check_rate_limit(user_id):
    """Check if user is rate limited (basic cooldown between any commands)"""
    current_time = time.time()
    if user_id in user_last_command:
        time_since_last = current_time - user_last_command[user_id]
        if time_since_last < RATE_LIMIT_SECONDS:
            return False, RATE_LIMIT_SECONDS - time_since_last
    user_last_command[user_id] = current_time
    return True, 0

def check_command_cooldown(user_id, command_name, cooldown_duration):
    """Check if a specific command is on cooldown for a user"""
    current_time = time.time()
    if command_name in user_command_cooldowns[user_id]:
        time_since_last = current_time - user_command_cooldowns[user_id][command_name]
        if time_since_last < cooldown_duration:
            return False, cooldown_duration - time_since_last
    user_command_cooldowns[user_id][command_name] = current_time
    return True, 0

@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == client.user:
        return
    
    # Block DMs - bot only works in servers
    if isinstance(message.channel, discord.DMChannel):
        await message.channel.send("❌ Sorry, I don't respond to DMs. Please use me in a server!")
        print(f"Blocked DM from {message.author.name} (ID: {message.author.id})")
        return
    
    # Check if user is temporarily muted for spamming
    if is_muted(message.author.id):
        # Silently ignore muted users
        return
    
    # Spam detection
    if is_spam(message.author.id):
        spam_muted_users[message.author.id] = time.time()
        try:
            await message.channel.send(
                f"⚠️ {message.author.mention} Slow down! You're sending messages too quickly. "
                f"You've been temporarily muted for {SPAM_MUTE_DURATION} seconds."
            )
        except:
            pass
        print(f"User {message.author.name} (ID: {message.author.id}) muted for spam")
        return

    # Hardcoded messages
    if message.content.startswith('!'):
        command = message.content.split()[0][1:]
        print(f"Command received: '{command}' from message: '{message.content}'")
        
        # Rate limiting check (applies to all commands)
        can_proceed, wait_time = check_rate_limit(message.author.id)
        if not can_proceed:
            try:
                await message.channel.send(
                    f"⏱️ {message.author.mention} Please wait {wait_time:.1f} seconds before using another command.",
                    delete_after=5
                )
            except:
                pass
            return
        
        if command == 'help':
            await message.channel.send('Current commands: !help, !ping, !meme, !roastme, !inactive, !topchatter, !nuke')
        elif command == 'ping':
            await message.channel.send('You pinged? :)')
        elif command == 'meme':
            if not HUMOR_API_KEY:
                await message.channel.send("❌ Humor API key is not configured.")
                return

            try:
                response = requests.get(
                    "https://api.humorapi.com/memes/random",
                    params={"api-key": HUMOR_API_KEY},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    await message.channel.send(data['url'])
                else:
                    await message.channel.send(f"Failed to fetch meme: {response.status_code}")
            except Exception as e:
                print(f"Error fetching meme: {e}")
                await message.channel.send("❌ An error occurred while fetching a meme.")
        elif command == 'inactive':
            print(f"!inactive command triggered by {message.author.name} (ID: {message.author.id})")
            print(f"OWNER_ID is set to: {OWNER_ID}")
            
            # Permission check: Only authorized users can use this command
            if message.author.id not in OWNER_ID:
                await message.channel.send("❌ Permission Denied. This command is owner-only.")
                return
            
            # Make sure this is in a guild (server), not a DM
            if not message.guild:
                await message.channel.send("❌ This command only works in a server!")
                return
            
            # Cooldown check for expensive command
            can_proceed, wait_time = check_command_cooldown(message.author.id, 'inactive', COOLDOWN_EXPENSIVE_COMMANDS)
            if not can_proceed:
                await message.channel.send(
                    f"⏱️ This command is on cooldown. Please wait {wait_time:.1f} seconds."
                )
                return
            
            # Send a "processing" message since this might take a moment
            try:
                status_msg = await message.channel.send(
                    "🔍 **Scanning entire server for inactive members...**\n"
                    "This will check ALL channels (results posted here privately).\n"
                    "Please wait, this may take 10-30 seconds..."
                )
            except Exception as e:
                print(f"Failed to send status message: {e}")
                return
            
            try:
                guild = message.guild
                current_time = datetime.now(timezone.utc)
                
                # Get all members in the server
                print(f"Fetching members from guild: {guild.name}")
                await status_msg.edit(content="🔍 Fetching all server members...")
                
                # Fetch all members (required for large servers)
                all_members = [member for member in guild.members if not member.bot]
                print(f"Found {len(all_members)} non-bot members in the server")
                
                if len(all_members) == 0:
                    await status_msg.edit(content="❌ No members found. Make sure the bot has the Server Members Intent enabled!")
                    return
                
                # Track last activity time for each user
                user_last_activity = {}
                
                # Initialize all members with their join date as a fallback
                for member in all_members:
                    user_last_activity[member.id] = {
                        'name': member.display_name,
                        'last_seen': member.joined_at if member.joined_at else current_time
                    }
                
                # Scan messages across all text channels to find actual activity
                await status_msg.edit(content="🔍 Scanning message history across all server channels...")
                message_count = 0
                channels_scanned = 0
                channels_with_permissions = 0
                
                # Count how many channels we have permission to read
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).read_message_history:
                        channels_with_permissions += 1
                
                print(f"Found {len(guild.text_channels)} text channels, bot has permission to read {channels_with_permissions} of them")
                
                for channel in guild.text_channels:
                    try:
                        # Check if bot has permission to read this channel
                        if not channel.permissions_for(guild.me).read_message_history:
                            print(f"Skipping channel '{channel.name}' - no read permission")
                            continue
                        
                        channels_scanned += 1
                        print(f"Scanning channel '{channel.name}' ({channels_scanned}/{channels_with_permissions})...")
                        
                        # Scan recent messages in each channel (limit per channel to avoid timeout)
                        channel_msg_count = 0
                        async for msg in channel.history(limit=MESSAGE_SCAN_LIMIT):
                            # Skip bot messages
                            if msg.author.bot:
                                continue

                            message_count += 1
                            channel_msg_count += 1
                            
                            # Update to the most recent message if we find a later one
                            if msg.author.id in user_last_activity:
                                if msg.created_at > user_last_activity[msg.author.id]['last_seen']:
                                    user_last_activity[msg.author.id]['last_seen'] = msg.created_at
                        
                        print(f"  → Found {channel_msg_count} messages in '{channel.name}'")
                    
                    except discord.Forbidden:
                        # Skip channels we can't access
                        print(f"Forbidden: Cannot access channel '{channel.name}'")
                        continue
                    except Exception as e:
                        print(f"Error scanning channel {channel.name}: {e}")
                        continue
                
                print(f"✓ Scanned {message_count} messages across {channels_scanned} channels")
                print(f"✓ Tracking {len(user_last_activity)} members")
                
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
                    description=f"Scanned {message_count} messages across {channels_scanned} channels\nTotal server members: {len(all_members)}",
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
                    embed.description = f"Scanned {message_count} messages across {channels_scanned} channels\nTotal server members: {len(all_members)}\n\n✅ No inactive users found in the specified timeframes!"
                
                embed.set_footer(text=f"Total members analyzed: {len(user_last_activity)}")
                
                # Delete the status message and send the report
                await status_msg.delete()
                await message.channel.send(embed=embed)
                print("Inactivity report sent successfully!")
                
            except discord.Forbidden as e:
                print(f"Permission error: {e}")
                try:
                    await status_msg.edit(content="❌ Error: I don't have permission to read message history or access server members. Make sure Server Members Intent and Read Message History are enabled!")
                except:
                    await message.channel.send("❌ Error: I don't have permission to read message history or access server members.")
            except Exception as e:
                print(f"Error in !inactive command: {e}")
                import traceback
                traceback.print_exc()
                try:
                    await status_msg.edit(content=f"❌ An error occurred: {str(e)}")
                except:
                    await message.channel.send(f"❌ An error occurred: {str(e)}")

        elif command == 'topchatter':
            # Cooldown check
            can_proceed, wait_time = check_command_cooldown(message.author.id, 'topchatter', COOLDOWN_EXPENSIVE_COMMANDS)
            if not can_proceed:
                await message.channel.send(
                    f"⏱️ This command is on cooldown. Please wait {wait_time:.1f} seconds."
                )
                return

            # Send a "processing" message
            try:
                status_msg = await message.channel.send(
                    "🔍 **Calculating top chatters...**\n"
                    "Scanning recent channel history (this may take a moment)..."
                )
            except Exception as e:
                print(f"Failed to send status message: {e}")
                return

            try:
                guild = message.guild
                
                # Track message counts
                user_message_counts = defaultdict(int)
                user_names = {}
                
                message_count = 0
                channels_scanned = 0
                
                for channel in guild.text_channels:
                    try:
                        if not channel.permissions_for(guild.me).read_message_history:
                            continue
                        
                        channels_scanned += 1
                        
                        async for msg in channel.history(limit=MESSAGE_SCAN_LIMIT):
                            if msg.author.bot:
                                continue
                            
                            message_count += 1
                            user_message_counts[msg.author.id] += 1
                            # Update name to most recent display name
                            if msg.author.id not in user_names:
                                user_names[msg.author.id] = msg.author.display_name
                            
                    except discord.Forbidden:
                        continue
                    except Exception as e:
                        print(f"Error scanning channel {channel.name}: {e}")
                        continue
                
                # Sort by message count
                sorted_chatters = sorted(user_message_counts.items(), key=lambda x: x[1], reverse=True)
                
                # Create embed
                embed = discord.Embed(
                    title="🏆 Top Chatters (Recent History)",
                    description=f"Scanned {message_count} messages across {channels_scanned} channels.",
                    color=discord.Color.gold(),
                    timestamp=datetime.now(timezone.utc)
                )
                
                if sorted_chatters:
                    top_list = ""
                    for i, (user_id, count) in enumerate(sorted_chatters[:10], 1):
                        name = user_names.get(user_id, "Unknown")
                        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                        top_list += f"{medal} **{name}**: {count} messages\n"
                    
                    embed.add_field(name="Most Active Users", value=top_list, inline=False)
                else:
                    embed.description += "\n\n❌ No messages found in the scanned history."
                
                await status_msg.delete()
                await message.channel.send(embed=embed)
                
            except Exception as e:
                print(f"Error in !topchatter: {e}")
                try:
                    await status_msg.edit(content=f"❌ An error occurred: {str(e)}")
                except:
                    pass

        elif command == 'roastme':
            # Cooldown check for AI command
            can_proceed, wait_time = check_command_cooldown(message.author.id, 'roast', COOLDOWN_EXPENSIVE_COMMANDS)
            if not can_proceed:
                await message.channel.send(
                    f"🔥 {message.author.mention} The roaster needs to cool down! Wait {wait_time:.1f} seconds.",
                    delete_after=10
                )
                return
            
            # Check if AI API token is configured
            if not AI_API_TOKEN:
                await message.channel.send("❌ AI API is not configured. Contact the bot owner.")
                return
            
            try:
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {AI_API_TOKEN}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": AI_MODEL,
                        "messages": [
                            {
                                "role": "user",
                                "content": f"Write a short, brutal, funny roast for Discord user {message.author.name}. Keep it Discord-safe, under 50 words."
                            }
                        ],
                    },
                    timeout=10  # Add timeout to prevent hanging
                )
                if response.status_code == 200:
                    roast = response.json()['choices'][0]['message']['content']
                    await message.channel.send(roast)
                else:
                    await message.channel.send(f"Oof, roast failed: {response.status_code}. Try again later.")
            except requests.exceptions.Timeout:
                await message.channel.send("⏱️ The AI took too long to respond. Try again later.")
            except requests.exceptions.RequestException as e:
                await message.channel.send("❌ Network error occurred. Try again later.")
                print(f"Request error in !roastme: {e}")
            except Exception as e:
                await message.channel.send("❌ An unexpected error occurred.")
                print(f"Error in !roastme: {e}")

        elif command == 'nuke':
            print(f"!nuke command triggered by {message.author.name} (ID: {message.author.id})")
            
            # STRICT Permission check: Only the specific owner can use this command
            if message.author.id != NUKE_OWNER_ID:
                await message.channel.send("❌ **Permission Denied.** This is a destructive command - owner only.")
                print(f"!nuke denied for user {message.author.name} (ID: {message.author.id})")
                return
            
            # Make sure this is in a guild (server), not a DM
            if not message.guild:
                await message.channel.send("❌ This command only works in a server!")
                return
            
            # Check if bot has kick permissions
            if not message.guild.me.guild_permissions.kick_members:
                await message.channel.send("❌ I don't have permission to kick members! Grant me 'Kick Members' permission.")
                return
            
            # Cooldown check for expensive command
            can_proceed, wait_time = check_command_cooldown(message.author.id, 'nuke', COOLDOWN_EXPENSIVE_COMMANDS)
            if not can_proceed:
                await message.channel.send(
                    f"⏱️ This command is on cooldown. Please wait {wait_time:.1f} seconds."
                )
                return
            
            # Send a warning confirmation message
            try:
                warning_msg = await message.channel.send(
                    "⚠️ **WARNING: NUKE COMMAND INITIATED**\n"
                    "This will kick all members inactive for 60+ days.\n"
                    "React with ✅ within 15 seconds to confirm, or ❌ to cancel."
                )
                await warning_msg.add_reaction("✅")
                await warning_msg.add_reaction("❌")
            except Exception as e:
                print(f"Failed to send warning message: {e}")
                return
            
            # Wait for confirmation
            def check(reaction, user):
                return user.id == NUKE_OWNER_ID and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == warning_msg.id
            
            try:
                reaction, user = await client.wait_for('reaction_add', timeout=15.0, check=check)
                
                if str(reaction.emoji) == "❌":
                    await warning_msg.edit(content="❌ **NUKE CANCELLED** - No members were kicked.")
                    return
                
                # Confirmed - proceed with nuke
                await warning_msg.edit(content="☢️ **NUKE ACTIVATED** - Scanning server...")
                
            except TimeoutError:
                await warning_msg.edit(content="⏱️ **NUKE TIMED OUT** - No confirmation received. Cancelled for safety.")
                return
            
            try:
                guild = message.guild
                current_time = datetime.now(timezone.utc)
                
                # Get all members in the server
                print(f"NUKE: Fetching members from guild: {guild.name}")
                await warning_msg.edit(content="☢️ **NUKE ACTIVE** - Analyzing all server members...")
                
                all_members = [member for member in guild.members if not member.bot]
                print(f"NUKE: Found {len(all_members)} non-bot members")
                
                if len(all_members) == 0:
                    await warning_msg.edit(content="❌ No members found.")
                    return
                
                # Track last activity time for each user
                user_last_activity = {}
                
                # Initialize all members with their join date as fallback
                for member in all_members:
                    user_last_activity[member.id] = {
                        'member': member,
                        'name': member.display_name,
                        'last_seen': member.joined_at if member.joined_at else current_time
                    }
                
                # Scan messages across all text channels
                await warning_msg.edit(content="☢️ **NUKE ACTIVE** - Scanning message history...")
                message_count = 0
                channels_scanned = 0
                
                for channel in guild.text_channels:
                    try:
                        if not channel.permissions_for(guild.me).read_message_history:
                            continue
                        
                        channels_scanned += 1
                        print(f"NUKE: Scanning channel '{channel.name}'...")
                        
                        async for msg in channel.history(limit=MESSAGE_SCAN_LIMIT):
                            if msg.author.bot:
                                continue
                            
                            message_count += 1
                            
                            if msg.author.id in user_last_activity:
                                if msg.created_at > user_last_activity[msg.author.id]['last_seen']:
                                    user_last_activity[msg.author.id]['last_seen'] = msg.created_at
                    
                    except discord.Forbidden:
                        continue
                    except Exception as e:
                        print(f"NUKE: Error scanning channel {channel.name}: {e}")
                        continue
                
                print(f"NUKE: Scanned {message_count} messages across {channels_scanned} channels")
                
                # Find members inactive for 60+ days
                targets = []
                for user_id, data in user_last_activity.items():
                    days_inactive = (current_time - data['last_seen']).days
                    
                    if days_inactive >= 60:
                        targets.append((data['member'], data['name'], days_inactive))
                
                # Sort by most inactive first
                targets.sort(key=lambda x: x[2], reverse=True)
                
                if len(targets) == 0:
                    await warning_msg.edit(content="✅ **NUKE COMPLETE** - No members were inactive for 60+ days. Server is clean!")
                    return
                
                # Show targets and start kicking
                await warning_msg.edit(
                    content=f"☢️ **NUKE IN PROGRESS** - Found {len(targets)} members inactive 60+ days.\n"
                            f"Kicking members now..."
                )
                
                kicked_members = []
                failed_kicks = []
                
                for member, name, days in targets:
                    try:
                        # Safety checks before kicking
                        if member.id == NUKE_OWNER_ID:
                            print(f"NUKE: Skipping owner {name}")
                            continue
                        
                        if member.guild_permissions.administrator:
                            print(f"NUKE: Skipping admin {name}")
                            failed_kicks.append((name, "Admin"))
                            continue
                        
                        if member.top_role >= guild.me.top_role:
                            print(f"NUKE: Cannot kick {name} - higher role")
                            failed_kicks.append((name, "Higher role"))
                            continue
                        
                        # Kick the member
                        await member.kick(reason=f"Inactive for {days} days - Auto-kicked by !nuke command")
                        kicked_members.append((name, days))
                        print(f"NUKE: Kicked {name} ({days} days inactive)")
                        
                        # Small delay to avoid rate limits
                        await asyncio.sleep(1)
                        
                    except discord.Forbidden:
                        failed_kicks.append((name, "No permission"))
                        print(f"NUKE: Failed to kick {name} - permission denied")
                    except Exception as e:
                        failed_kicks.append((name, str(e)))
                        print(f"NUKE: Error kicking {name}: {e}")
                
                # Create final report
                embed = discord.Embed(
                    title="☢️ NUKE COMPLETE",
                    description=f"Scanned {message_count} messages across {channels_scanned} channels",
                    color=discord.Color.red(),
                    timestamp=current_time
                )
                
                if kicked_members:
                    kicked_list = "\n".join([f"• {name} ({days} days)" for name, days in kicked_members[:25]])
                    if len(kicked_members) > 25:
                        kicked_list += f"\n... and {len(kicked_members) - 25} more"
                    embed.add_field(
                        name=f"✅ Kicked ({len(kicked_members)} members)",
                        value=kicked_list,
                        inline=False
                    )
                
                if failed_kicks:
                    failed_list = "\n".join([f"• {name} ({reason})" for name, reason in failed_kicks[:10]])
                    if len(failed_kicks) > 10:
                        failed_list += f"\n... and {len(failed_kicks) - 10} more"
                    embed.add_field(
                        name=f"⚠️ Could Not Kick ({len(failed_kicks)} members)",
                        value=failed_list,
                        inline=False
                    )
                
                embed.set_footer(text=f"Total targets: {len(targets)} | Kicked: {len(kicked_members)} | Failed: {len(failed_kicks)}")
                
                await warning_msg.delete()
                await message.channel.send(embed=embed)
                print(f"NUKE: Complete - {len(kicked_members)} kicked, {len(failed_kicks)} failed")
                
            except Exception as e:
                print(f"NUKE: Critical error: {e}")
                traceback.print_exc()
                try:
                    await warning_msg.edit(content=f"❌ **NUKE FAILED** - Critical error: {str(e)}")
                except:
                    pass


# Run the bot with your token
client.run(TOKEN)