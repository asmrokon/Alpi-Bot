import asyncio
import logging
import sys
from os import getenv

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

token = getenv("DISCORD_TOKEN")
if not token:
    print("Error: DISCORD_TOKEN not found in .env file.")
    sys.exit(1)


# DISCORD LOGGING
logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)  
file_handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
logger.addHandler(file_handler)

# INTENTS
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=".",intents=intents)


async def main():
    await load_cogs()
    await bot.start(token)
    
async def load_cogs():
    await bot.load_extension("cogs.manga")
    await bot.load_extension("cogs.news")
    await bot.load_extension("cogs.admin")
    await bot.load_extension("cogs.event")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot Tree synced")


try:
    asyncio.run(main())
except discord.errors.LoginFailure:
    print("Error: Improper token")
    sys.exit(1)
except discord.errors.HTTPException:
    print("Error: 401 Unauthorized (error code: 0): 401: Unauthorized")
    sys.exit(1)