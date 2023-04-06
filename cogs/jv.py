#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""JV cog."""

import aiohttp

# import discord
import logging

from bs4 import BeautifulSoup
from discord import Embed
from discord.ext import commands

logger = logging.getLogger(__name__)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    }


def generate_url(month: int, year: int):
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
    french_m = french_months[month - 1]
    url = f"https://www.jeuxvideo.com/sorties/dates-de-sortie-{french_m}-{year}-date.htm"
    return url, french_m, year


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
        url, month, year = generate_url(month, year)
        async with aiohttp.ClientSession() as session:
            res = await session.get(url, headers=headers)
            soup = BeautifulSoup(await res.text(), "html.parser")
        list_of_new_games = soup.select("div[class*='gameMetadatas']")

        embed = Embed(title=f"Sorties du mois {month} {year}")
        for sortie in list_of_new_games:
            title = sortie.select_one("a[class*='gameTitleLink']").text
            date = sortie.select_one("span[class*='releaseDate']").text
            try:
                tmp = sortie.select_one("div[class*='platforms']").text
                platform = f"Plateformes :\t {tmp}"
            except AttributeError:
                platform = "no platform"
            embed.add_field(name=title, value=f"{date} \n {platform}", inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(JV(bot))
    logger.info("Cog JV added")
