# Discord Raid Bot in Python

## Requirement Summary
This document outlines the implementation of a Discord bot that allows users to initiate raid commands. The bot includes commands for both regular and premium users, with specific functionalities for each. The bot is designed to be deployed securely using environment variables for sensitive information.

## Code Generated

### 1. `main.py`
```python
import discord
from discord.ext import commands
import os
import json
import asyncio
from typing import List, Dict, Any, Optional
import logging

# --- Configuration ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_WHITELIST = [1386627461197987841]  # Your user ID for premium access

# --- Setup Logging ---
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

# --- File Management Functions ---
FILE_PATHS = {
    "config": "config.json",
    "premium": "premium.json",
    "presets": "presets.json",
    "leaderboard": "leaderboard.json",
}

def load_json(filepath: str) -> Any:
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {filepath}. Creating a default empty structure.")
        return {}

def save_json(filepath: str, data: Any):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

# --- Load All Data ---
premium_users = load_json(FILE_PATHS["premium"])
presets = load_json(FILE_PATHS["presets"])
leaderboard = load_json(FILE_PATHS["leaderboard"])

# --- Bot Initialization ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# --- Commands ---
@bot.tree.command(name="a-raid", description="Initiate a raid.")
async def a_raid(interaction: discord.Interaction):
    embed = discord.Embed(title="Raid Alert!", description="Click the button to send the message 5 times.")
    button = discord.ui.Button(label="Send Message", style=discord.ButtonStyle.primary)

    async def button_callback(interaction: discord.Interaction):
        for _ in range(5):
            await interaction.channel.send("🚨 Raid Alert! 🚨")
        await interaction.response.send_message("Message sent 5 times!", ephemeral=True)

    button.callback = button_callback
    view = discord.ui.View()
    view.add_item(button)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="custom-raid", description="Custom raid message for premium users.")
async def custom_raid(interaction: discord.Interaction, message: str):
    if interaction.user.id not in ADMIN_WHITELIST:
        await interaction.response.send_message("You don’t have premium access and you cannot use this command😧", ephemeral=True)
        return

    embed = discord.Embed(title="Custom Raid Alert!", description=message)
    button = discord.ui.Button(label="Send Message", style=discord.ButtonStyle.primary)

    async def button_callback(interaction: discord.Interaction):
        for _ in range(5):
            await interaction.channel.send(message)
        await interaction.response.send_message("Custom message sent 5 times!", ephemeral=True)

    button.callback = button_callback
    view = discord.ui.View()
    view.add_item(button)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="add-premium", description="Add premium access to a user.")
async def add_premium(interaction: discord.Interaction, user_id: int):
    if interaction.user.id != ADMIN_WHITELIST[0]:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    premium_users.append(user_id)
    save_json(FILE_PATHS["premium"], premium_users)
    await interaction.response.send_message(f"User {user_id} has been granted premium access.")

@bot.tree.command(name="remove-premium", description="Remove premium access from a user.")
async def remove_premium(interaction: discord.Interaction, user_id: int):
    if interaction.user.id != ADMIN_WHITELIST[0]:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    if user_id in premium_users:
        premium_users.remove(user_id)
        save_json(FILE_PATHS["premium"], premium_users)
        await interaction.response.send_message(f"User {user_id} has been removed from premium access.")
    else:
        await interaction.response.send_message(f"User {user_id} does not have premium access.")

# --- Run Bot ---
if __name__ == "__main__":
    bot.run(BOT_TOKEN)
