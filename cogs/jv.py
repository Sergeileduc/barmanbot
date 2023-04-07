#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""JV cog."""
import logging
import re
from datetime import date
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup, Tag
from dateparser.date import DateDataParser
from discord import Embed
from discord.ext import commands

logger = logging.getLogger(__name__)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    }
ddp = DateDataParser(languages=["fr"])


class NewGame:
    """Class for keeping informations on a game, such as name, release date, etc..."""

    def __init__(self, name: str, release: str, platforms: str, part_url: str) -> None:
        self.name = name
        self.release = release
        self.platforms = platforms
        self.url = urljoin("https://www.jeuxvideo.com", part_url)
        try:
            date_str = re.sub('Sortie: ', '', self.release)
            self.date = ddp.get_date_data(date_str).date_obj.date()
        except AttributeError:
            self.date = date(year=3000, month=1, day=1)

    def __str__(self) -> str:
        return f"{self.name}\n{self.release}\n{self.platforms}\n{self.url}\n{self.date}\n----------"


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


async def fetch_page(url: str):
    """Fetch a page on JV, for month releases. If pagination, return the next url.

    Args:
        url (str): url of the release page
    """
    async with aiohttp.ClientSession() as session:
        res = await session.get(url, headers=headers)
        soup = BeautifulSoup(await res.text(), "html.parser")
    list_of_new_games = soup.select("div[class*='gameMetadatas']")
    pagination = soup.select_one("div[class*='pagination']")
    pages, url = find_next_page(pagination)

    releases = []
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
        except AttributeError:
            part = None
        releases.append(NewGame(name=title, release=date, platforms=platform, part_url=part))
    return releases, pages, url


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
            games, pages, url = await fetch_page(url)
            for game in games:
                embed.add_field(name=game.name,
                                value=f"{game.release}\n{game.platforms}\n{game.url}",
                                inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(JV(bot))
    logger.info("Cog JV added")
