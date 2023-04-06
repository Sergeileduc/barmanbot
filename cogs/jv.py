#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""JV cog."""

import aiohttp

# import discord
import logging

from bs4 import BeautifulSoup
from discord.ext import commands

logger = logging.getLogger(__name__)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    }


def generate_url(month: int, year: int) -> str:
    """generate JV url

    Args:
        month (int):
        year (int):

    Returns:
        str: url
    """
    french_months = ['janvier', 'fevrier', 'mars', 'avril', 'mai', 'juin',
                     'juillet', 'aout',
                     'septembre', 'octobre', 'novembre', 'decembre']
    return f"https://www.jeuxvideo.com/sorties/dates-de-sortie-{french_months[month - 1]}-{year}-date.htm"


class JV(commands.Cog):
    """Fetch Video games release date."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command()
    async def sorties(self, ctx: commands.Context, month: int, year: int):
        """Sorties JV

        Args:
            month (int): mois
            year (int): année
        """
        url = generate_url(month, year)
        async with aiohttp.ClientSession() as session:
            res = await session.get(url, headers=headers)
            soup = BeautifulSoup(await res.text(), "html.parser")
        list_of_new_games = soup.select("div[class*='gameMetadatas']")

        content = ""
        for sortie in list_of_new_games:
            title = sortie.select_one("a[class*='gameTitleLink']").text
            date = sortie.select_one("span[class*='releaseDate']").text
            try:
                tmp = sortie.select_one("div[class*='platforms']").text
                platform = f"Plateformes :\t {tmp}"
            except AttributeError:
                platform = "no platform"
            content += title + "\n"
            content += date + "\n"
            content += platform + "\n"
            content += "_____________\n"
        await ctx.send(content=content)


async def setup(bot):
    await bot.add_cog(JV(bot))
    logger.info("Cog JV added")
