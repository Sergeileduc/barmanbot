#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Miscs cog."""

import discord
import logging

from discord import app_commands, ui
from discord.ext import commands

logger = logging.getLogger(__name__)


class CodeModal(ui.Modal, title="My code modal"):
    answer = ui.TextInput(label="Entrez votre code", required=True)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        # return await super().on_submit(interaction)
        embed = discord.Embed(title=self.title,
                              description=f"**{self.answer.label}\n**{self.answer}")
        embed.set_author(name=interaction.user, icon=interaction.user.avatar)
        await interaction.response.send_message(embed=embed)


class Code(commands.Cog):
    """Mardown some code."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="code")
    @app_commands.choices(choices=[
        app_commands.Choice(name="Python", value="python"),
        app_commands.Choice(name="html", value="html"),
        app_commands.Choice(name="json", value="json"),
        ])
    async def code(self,
                   i: discord.Interaction,
                   choices: app_commands.Choice[str],
                   ):
        print(choices.value)
        await i.response.send_modal(CodeModal())


async def setup(bot):
    await bot.add_cog(Code(bot))
    logger.info("Cog code added")
