#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Awesome Discord Bot."""
import asyncio
import logging
import os
import platform

import discord
from discord.ext import commands
from dotenv import load_dotenv

import cogs

# Logging
logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.DEBUG)

# Parse a .env file and then load all the variables found as environment variables.
load_dotenv()
token = os.getenv("DISCORD_TOKEN")
# Done


# parameters for the bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", help_command=None,
                   description=None, case_insensitive=True, intents=intents)

cogs_list = [
    cogs.Misc,
    cogs.LeMonde,
    ]


@bot.event
async def on_ready():
    """Log in Discord."""
    logging.info('Logged in as')
    logging.info(bot.user.name)
    logging.info(bot.user.id)
    logging.info('------')
    for cog in cogs_list:
        await bot.add_cog(cog(bot))
    # await bot.tree.sync()


if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    bot.run(token)
