"""News cog."""

import logging
import os

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

ACTU_BOT_CHANNEL: str = "news-jv"
ACTU_JV: str = "talk-jv"


class ActuRelay(commands.Cog):
    def __init__(self, bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        self.guild = None
        self.channel_bot = None  # define later in on_ready
        self.channel_human = None  # define later in on_ready

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = self.bot.get_guild(self.guild_id)
        if self.guild is None:
            logger.error("Guild introuvable: %s", self.guild_id)
            return

        self.channel_bot = discord.utils.find(
            lambda c: c.name.endswith("news-jv"), self.guild.text_channels
        )

        self.channel_human = discord.utils.find(
            lambda c: c.name.endswith("talk-jv"), self.guild.text_channels
        )

        logger.info("ActuRelay prêt: %s -> %s", self.channel_bot, self.channel_human)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Relay news to another channel, on any reaction."""
        # On filtre le bon salon
        if payload.channel_id != self.channel_bot.id:
            return

        # On ignore les réactions du bot
        if payload.user_id == self.bot.user.id:
            return

        # Récupérer le message original
        message = await self.channel_bot.fetch_message(payload.message_id)

        # Auteur de la réaction
        author = payload.member.display_name if payload.member else "Quelqu'un"

        # Envoyer l’annonce
        await self.channel_human.send(f"{author} vous a partagé ceci :")

        # Envoyer le contenu du message
        if message.content:
            await self.channel_human.send(message.content)


async def setup(bot):
    GUILD_ID = int(os.getenv("GUILD_ID"))
    await bot.add_cog(ActuRelay(bot, guild_id=GUILD_ID))
    logger.info("News cog added")
