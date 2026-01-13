#!/usr/bin/python3
"""Awesome Discord Bot."""

import argparse
import asyncio
import logging
import os
import platform

import discord
from discord.ext import commands
from dotenv import load_dotenv

# import utils.tools

PREFIX = "!"

# Parse a .env file and then load all the variables found as environment variables.
load_dotenv()
TOKEN: str = os.getenv("BARMAN_DISCORD_TOKEN")
DEV_MODE = os.getenv("DEV_MODE", "").strip().lower() in ("1", "true", "yes", "on")
DEV_GUILD_ID = int(os.getenv("DEV_GUILD_ID", "0"))

# Logging
logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.DEBUG)

# --debug option
parser = argparse.ArgumentParser(description="Lancement du bot Discord")
parser.add_argument(
    "-d",
    "--debug",
    action="store_true",
    help="change prefix to '?'",
)
parser.add_argument("--dev", action="store_true", help="Activer le mode développement")
args = parser.parse_args()

if args.debug:
    logging.info("You are in debug mode.")
    logging.info("Prefix is now '?'")
    PREFIX = "?"

if args.dev:
    DEV_MODE = True
    os.environ["DEV_MODE"] = "true"  # Pour que les autres modules le voient aussi
else:
    os.environ["DEV_MODE"] = "false"

# Log du mode
if DEV_MODE:
    print(f"🚧 Mode développement activé (guild={DEV_GUILD_ID})")
    logging.info("guild for dev : %s", str(DEV_GUILD_ID))
else:
    print("🚀 Mode production activé")


# parameters for the bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix=PREFIX,
    help_command=None,
    description=None,
    case_insensitive=True,
    intents=intents,
)

cogs_ext_list = [
    "cogs.misc",
    "cogs.lemonde",
    "cogs.code",
    #  "cogs.jv",
    "cogs.youtube",
]


@bot.event
async def on_ready():
    """Log in Discord."""
    logging.info("Logged in as")
    logging.info(bot.user.name)
    logging.info(bot.user.id)
    # await bot.tree.sync()


@bot.event
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


if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    logging.info("New bot with discord.py version %s", discord.__version__)
    bot.run(TOKEN)
