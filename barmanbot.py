#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Awesome Discord Bot."""
import argparse
import asyncio
import logging
import os
import platform

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Logging
# logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)

# Parse a .env file and then load all the variables found as environment variables.
load_dotenv()
TOKEN = os.getenv("BARMAN_DISCORD_TOKEN")
# Done

logging.basicConfig(level=logging.DEBUG)

PREFIX = '!'

# --debug option
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug",
                    help="change prefix to '?'", action="store_true")
args = parser.parse_args()
if args.debug:
    logging.info("You are in debug mode.")
    logging.info("Prefix is now '?'")
    PREFIX = '?'


# parameters for the bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, help_command=None,
                   description=None, case_insensitive=True, intents=intents)

cogs_ext_list = ["cogs.misc",
                 "cogs.lemonde",
                 "cogs.code",
                 "cogs.jv",
                 "cogs.youtube",
                 ]


@bot.event
async def on_ready():
    """Log in Discord."""
    logging.info('Logged in as')
    logging.info(bot.user.name)
    logging.info(bot.user.id)
    logging.info('------')
    # await bot.tree.sync()


async def setup_hook():
    """A coroutine to be called to setup the bot.

    To perform asynchronous setup after the bot is logged in but before
    it has connected to the Websocket, overwrite this coroutine.

    This is only called once, in `login`, and will be called before
    any events are dispatched, making it a better solution than doing such
    setup in the `~discord.on_ready` event.

    Warning :
    Since this is called *before* the websocket connection is made therefore
    anything that waits for the websocket will deadlock, this includes things
    like :meth:`wait_for` and :meth:`wait_until_ready`.
    """
    logging.info("Setup_hook !!!")
    for ext in cogs_ext_list:
        await bot.load_extension(ext)


# Overwrite the empty setup_hook of commands.Bot :
bot.setup_hook = setup_hook


if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    logging.info("New bot with discord.py version %s", discord.__version__)
    bot.run(TOKEN)
