#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""JV cog."""
import re
from urllib.parse import urljoin

import aiohttp

# import discord
import logging

from bs4 import BeautifulSoup, Tag
from discord import Embed
from discord.ext import commands

logger = logging.getLogger(__name__)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    }


def find_next_page(tag: Tag):
    """Find if there is a button "next page".

    Args:
        tag (Tag): Beautiful Soup Tag

    Returns:
        bool, str: if found, then give the url
    """
    found = False
    url = ""
    if nextpage := tag.find("a", class_=re.compile("page")):
        url = urljoin("https://www.jeuxvideo.com", nextpage.get("href"))
        found = True
    return found, url


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
        embed = Embed(title=f"Sorties du mois {month} {year}")
        pages = True
        while pages:
            async with aiohttp.ClientSession() as session:
                res = await session.get(url, headers=headers)
                soup = BeautifulSoup(await res.text(), "html.parser")
            list_of_new_games = soup.select("div[class*='gameMetadatas']")
            pagination = soup.select_one("div[class*='pagination']")
            pages, url = find_next_page(pagination)

            for sortie in list_of_new_games:
                title = sortie.select_one("a[class*='gameTitleLink']").text
                date = sortie.select_one("span[class*='releaseDate']").text
                try:
                    tmp = sortie.select_one("div[class*='platforms']").text
                    platform = f"Plateformes :\t {tmp}"
                except AttributeError:
                    platform = "no platform"
                try:
                    part = sortie.select_one("div > span > h2 > a").get("href")
                    gameurl = urljoin("https://www.jeuxvideo.com", part)
                except AttributeError:
                    gameurl = None
                embed.add_field(name=title, value=f"{date}\n{platform}\n{gameurl}", inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(JV(bot))
    logger.info("Cog JV added")
