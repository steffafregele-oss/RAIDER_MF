import os
import time
import asyncio
import random
import logging
import discord
from discord import User, Embed, Interaction, ButtonStyle, app_commands
from discord.ext import commands
from discord.ui import View, Button
import json
from colorama import Fore, Style, init
from aiohttp import web

init(autoreset=True)

# -------------------------------
# HTTP server dummy pentru Render
# -------------------------------
async def handle(request):
    return web.Response(text="Bot is running ✅")

async def start_http_server():
    port = int(os.environ.get("PORT", 5000))
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"✅ HTTP server running on port {port}")

# Configuration
PREMIUM_FILE = "premium.json"
OWNER_ID = 1386627461197987841

# Premium user management
def load_premium_users():
    if not os.path.exists(PREMIUM_FILE):
        return []
    with open(PREMIUM_FILE, "r") as f:
        return json.load(f)

def save_premium_users(user_ids):
    with open(PREMIUM_FILE, "w") as f:
        json.dump(user_ids, f, indent=2)

def add_premium_user(user_id: int):
    premium_users = load_premium_users()
    if user_id not in premium_users:
        premium_users.append(user_id)
        save_premium_users(premium_users)

def is_premium_user(user_id: int):
    premium_users = load_premium_users()
    return user_id in premium_users

def remove_premium_user(user_id: int) -> bool:
    premium_users = load_premium_users()
    if user_id in premium_users:
        premium_users.remove(user_id)
        save_premium_users(premium_users)
        return True
    return False

# Command logging functions
async def log_command_use(user, command_name, channel=None, message=None):
    """Log command usage"""
    print(f"{Fore.CYAN}[COMMAND]{Fore.WHITE} {user} used /{command_name}")

def update_leaderboard(user_id, command_name):
    """Update leaderboard (placeholder for future implementation)"""
    pass

# Logo
logo = f"""{Fore.MAGENTA}

  ___ _  _ ___  ___  __  __ _  _ ___   _   
 |_ _| \| / __|/ _ \|  \/  | \| |_ _| /_\  
  | || .` \__ \ (_) | |\/| | .` || | / _ \ 
 |___|_|\_|___/\___/|_|  |_|_|\_|___/_/ \_\
{Fore.WHITE}     raiding made easy                        
 
"""

# Bot setup - Enhanced with proper permissions for ghost ping
intents = discord.Intents.default()
intents.messages = True  # Enable message content for ghost ping
intents.message_content = True  # Enable message content for ghost ping
intents.members = False  
intents.guilds = True  # Enable guilds for better server management
intents.typing = False 
intents.presences = False  

bot = commands.Bot(command_prefix="!", intents=intents)

class FloodButton(discord.ui.View):
    def __init__(self, message, delay):
        super().__init__()
        self.message = message
        self.delay = delay

    @discord.ui.button(label="⚡ Execute Command", style=discord.ButtonStyle.blurple)
    async def flood_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        max_retries = 2

        for _ in range(5):
            retries = 0
            while retries <= max_retries:
                try:
                    await interaction.followup.send(self.message, allowed_mentions=discord.AllowedMentions(everyone=True))
                    await asyncio.sleep(self.delay + random.uniform(0.1, 0.5))
                    break
                except discord.errors.HTTPException as e:
                    if e.status == 429:
                        retry_after = getattr(e, "retry_after", 1.5)
                        retry_after = min(retry_after, 5)
                        print(f"{Fore.YELLOW}>{Fore.WHITE} Rate limit hit, retrying after {Fore.YELLOW}{retry_after:.2f}s{Fore.WHITE} (retry {Fore.YELLOW}{retries + 1}{Fore.WHITE}/{Fore.YELLOW}{max_retries}{Fore.WHITE})")
                        await asyncio.sleep(retry_after)
                        retries += 1
                    else:
                        raise e
            else:
                print(f"{Fore.RED}>{Fore.WHITE} Failed to send message after max retries, skipping{Fore.RED}.{Fore.WHITE}")

# Premium message management
def load_presets():
    if not os.path.exists("presets.json"):
        return {}
    try:
        with open("presets.json", "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        return {}

def save_preset(user_id, message):
    data = load_presets()
    data[str(user_id)] = message
    with open("presets.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def get_preset(user_id):
    data = load_presets()
    return data.get(str(user_id))

class PresetModal(discord.ui.Modal, title="Set Your Custom Raid Message"):
    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id
        self.message_input = discord.ui.TextInput(
            label="Enter your spam message", 
            style=discord.TextStyle.long, 
            max_length=2000
        )
        self.add_item(self.message_input)

    async def on_submit(self, interaction: discord.Interaction):
        save_preset(self.user_id, self.message_input.value)
        await interaction.response.send_message("✅ Preset message saved successfully!", ephemeral=True)

class PresetView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id

    @discord.ui.button(label="Set Message", style=ButtonStyle.green)
    async def set_message(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(PresetModal(user_id=self.user_id))

    @discord.ui.button(label="Preview Message", style=ButtonStyle.primary)
    async def preview_message(self, interaction: discord.Interaction, button: Button):
        message = get_preset(self.user_id)
        if message:
            await interaction.response.send_message(f"📄 **Your preset message:**\n```{message}```", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ No preset message found. Please set one first.", ephemeral=True)

class SpamButton(discord.ui.View):
    def __init__(self, message):
        super().__init__()
        self.message = message

    @discord.ui.button(label="Spam", style=discord.ButtonStyle.red)
    async def spam_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        allowed = discord.AllowedMentions(everyone=True, users=True, roles=True)
        for _ in range(5):  
            await interaction.followup.send(self.message, allowed_mentions=allowed)  

# Storage for custom raid messages
raid_messages = {}

# Commands
@bot.tree.command(name="a-raid", description="RAID Any Server.")
@app_commands.describe(delay="Delay between messages in seconds (0.01 to 5.00).")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def araid(interaction: discord.Interaction, delay: float = 0.01):
    if delay < 0.01 or delay > 5.00:
        await interaction.response.send_message("**Error: Delay must be between 0.01 and 5.00 seconds.**", ephemeral=True)
        return

    # Check if custom raid message is set
    raid_message = raid_messages.get("custom", '''> **- 🦴 3 OP GENERATORS,
> - 🌐 HAVE OWN SITE,
> - 🧠 OP METHODS,
> - 👀 !STATS BOT
> - 🪆 MANAGE UR OWN SITE/DASHBOARD,
> - 🗒️ USERNAME & PASSWORD,
> - 🔒 ACCOUNT STATUS,
> - 🚀 FAST LOGIN SPEED
> - 📷 FULL TUTORIALS ON HOW TO BEAM**
━━━━━━━━━━━━┓
 https://discord.gg/GTFN2Dy96
━━━━━━━━━━━━┛
@everyone''')
    
    try:
        view = FloodButton(raid_message, delay)
        await interaction.response.send_message("Press the button to start raiding.", view=view, ephemeral=True)
    except discord.HTTPException as e:
        if e.code == 40094:  # follow-up message limit reached
            print(f"[A-RAID ERROR] Max follow-up messages reached for interaction {interaction.id}")
        else:
            print(f"[A-RAID ERROR] Unexpected HTTPException: {e}")
            raise

@bot.tree.command(name="edit-raid", description="Edit the a-raid message (owner only)")
@app_commands.describe(message="The new raid message to use")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def edit_raid(interaction: discord.Interaction, message: str):
    # Only allow owner to use this command
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Only the owner can use this command.", ephemeral=True)
        return
    
    raid_messages["custom"] = message
    await interaction.response.send_message("✅ Raid message updated successfully!", ephemeral=True)

@bot.tree.command(name="custom-message", description="[💎]Send one custom message (premium only)")
@app_commands.describe(message="The message to send")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def custom_message(interaction: discord.Interaction, message: str):
    # Premium only
    if not is_premium_user(interaction.user.id):
        await interaction.response.send_message("💎 This command is only available for premium users.", ephemeral=True)
        return
    
    try:
        await interaction.response.send_message(message, allowed_mentions=discord.AllowedMentions(everyone=True, users=True, roles=True))
    except discord.HTTPException as e:
        print(f"[CUSTOM-MESSAGE ERROR] {e}")
        await interaction.followup.send("❌ Failed to send message.", ephemeral=True)

@bot.tree.command(
    name="ghostping",
    description="GhostPing Somebody multiple times! The best delay is 0.3 seconds"
)
@app_commands.describe(
    user="📔 The user you want to ghost ping",
    seconds="🕰️ The delay (in seconds) before each message is deleted. Best is 0.3 🕰️",
    times="🔁 How many times to ghost ping them 🔁"
)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def ghostping(
    interaction: discord.Interaction,
    user: discord.User,
    seconds: float = 0.3,
    times: int = 3
):
    await interaction.response.send_message("Ghost pinging...", ephemeral=True)
    await log_command_use(interaction.user, "ghostping")
    update_leaderboard(interaction.user.id, "ghostping")

    for i in range(times):
        try:
            message = await interaction.followup.send(f"{user.mention}")
            await asyncio.sleep(seconds)
            await message.delete()
        except discord.HTTPException as e:
            if e.code == 40094:  
                print(f"[ghostping] follow up messages reached – stopped after {i} pings.")
                break
            else:
                raise

@bot.tree.command(name="blame", description="Blame somebody else for raiding, and get them banned!")
@app_commands.describe(user="📰 The user you want to blame..")
async def blame(interaction: discord.Interaction, user: discord.User):
    await interaction.response.send_message("Blaming... ✏️", ephemeral=True)
    await interaction.followup.send(f"{user.mention}, Your Raid Command has been Successfully Completed! ✅")
    await log_command_use(interaction.user, "blame")

@bot.tree.command(name="flooduser", description="[💎] Flood a user's DMs with messages. (premium only!)")
@app_commands.describe(user="The user to DM spam", message="Message to spam", times="How many times to send", delay="Delay between messages (in sec)")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def flooduser(interaction: discord.Interaction, user: discord.User, message: str, times: int = 5, delay: float = 0.3):
    if not is_premium_user(interaction.user.id):
        await interaction.response.send_message("💎 This command is only available for premium users.", ephemeral=True)
        return
    await interaction.response.send_message("Flooding user... 💣", ephemeral=True)
    await log_command_use(
        user=interaction.user,
        command_name="💎 flooduser",
        channel=interaction.channel,
        message=message
    )
    for _ in range(times):
        try:
            await user.send(message)
            await asyncio.sleep(delay)
        except discord.Forbidden:
            await interaction.followup.send("❌ Could not DM user (they may have DMs closed).", ephemeral=True)
            break

@bot.tree.command(name="custom-raid", description="[💎] Premium Raid with your own message. (premium only!)")
@app_commands.describe(message="Optional: your custom message to spam (use /preset-message if you want to save it)")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def custom_raid(interaction: discord.Interaction, message: str = None):
    if not is_premium_user(interaction.user.id):
        await interaction.response.send_message("💎 This command is only available for premium users.", ephemeral=True)
        return

    if not message:
        message = get_preset(interaction.user.id)
        if not message:
            await interaction.response.send_message("❌ You have not set a preset message. Use `/preset-message` to set one.", ephemeral=True)
            return

    view = SpamButton(message)
    await interaction.response.send_message(f"💎 SPAM TEXT:\n```{message}```", view=view, ephemeral=True)

@bot.tree.command(name="preset-message", description="Manage your custom raid message preset.")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def preset_message(interaction: discord.Interaction):
    if not is_premium_user(interaction.user.id):
        await interaction.response.send_message("💎 This command is only available for premium users.", ephemeral=True)
        return
    view = PresetView(user_id=interaction.user.id)
    embed = discord.Embed(
        title="⚡ Preset Message",
        description="Use the buttons below to set or preview your raid message.",
        color=0xa874d1
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="add-premium", description="Grant premium access to a user. (owner only)")
@app_commands.describe(user="The user to grant premium access to")
async def add_premium(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return
    
    add_premium_user(user.id)
    await interaction.response.send_message(f"✅ {user.mention} has been granted premium access!", ephemeral=False)

@bot.tree.command(name="remove-premium", description="Remove premium access from a user. (owner only)")
@app_commands.describe(user="The user to remove premium access from")
async def remove_premium(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return

    removed = remove_premium_user(user.id)
    if removed:
        await interaction.response.send_message(f"✅ User {user.mention} has been removed from premium access!", ephemeral=False)
    else:
        await interaction.response.send_message(f"⚠️ User {user.mention} does not have premium access.", ephemeral=True)

@bot.event
async def on_ready():
    print(logo)
    print(f"{Fore.MAGENTA}>{Fore.WHITE} Logged in as {Fore.MAGENTA}{bot.user}{Fore.WHITE}.")
    try:
        synced = await bot.tree.sync()
        print(f"{Fore.MAGENTA}>{Fore.WHITE} Synced {Fore.GREEN}{len(synced)}{Fore.WHITE} commands{Fore.MAGENTA}.{Fore.WHITE}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# -------------------------------
# Pornire simultană bot + HTTP server
# -------------------------------
async def main():
    # pornește HTTP server
    await start_http_server()
    # pornește botul
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        raise RuntimeError("Environment variable TOKEN not set.")
    
    try:
        await bot.start(TOKEN)
    except discord.errors.LoginFailure:
        print(Fore.RED + "Can't connect to token. Please check your token.")
    except Exception as e:
        print(Fore.RED + f"An unexpected error occurred: {e}")

# rulează totul în asyncio
if __name__ == "__main__":
    asyncio.run(main())
