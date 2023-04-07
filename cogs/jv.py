#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""JV cog."""
import logging
import re
from datetime import date, timedelta
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup, Tag
from dateparser.date import DateDataParser
from discord import Embed, Interaction
from discord.ext import commands
from discord.ui import Button, View

logger = logging.getLogger(__name__)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    }
ddp = DateDataParser(languages=["fr"])

DAY = timedelta(days=1)
WEEK = timedelta(days=7)
MONTH = timedelta(days=31)
QUARTER = timedelta(days=91)


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


def next_month(month: int, year: int):
    return (month + 1, year) if month != 12 else (1, year + 1)


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


async def fetch_month(url):
    """Fetch all games in a month, even if there are several pages."""
    pages = True
    games = []
    while pages:
        games_page, pages, url = await fetch_page(url)
        games += games_page
    return games


async def fetch_time_delta(delta: timedelta):
    """Fetch games in a time delta relative to today (one week, one month, etc...)"""
    today = date.today()
    int_month = today.month
    int_year = today.year

    url, _, _ = generate_url(today.month, today.year)
    games = await fetch_month(url)
    # next month
    new_month, new_year = next_month(int_month, int_year)
    url, _, _ = generate_url(new_month, new_year)
    games += await fetch_month(url)
    return [game for game in games
            if (diff := game.date - today) <= delta and diff.days >= 0]


class JV(commands.Cog):
    """Fetch Video games release date."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @ commands.hybrid_command()
    async def sorties(self, ctx: commands.Context):
        button1 = Button(label="Jour")
        button2 = Button(label="Semaine")
        button3 = Button(label="Mois")

        async def day_callback(interraction: Interaction):
            embed = Embed(title="Sorties du jour")
            games = await fetch_time_delta(DAY)
            for game in games:
                embed.add_field(name=game.name,
                                value=f"{game.release}\n{game.platforms}\n{game.url}",
                                inline=False)
            await interraction.response.send_message(embed=embed)

        async def week_callback(interraction: Interaction):
            embed = Embed(title="Sorties de la semaine")
            games = await fetch_time_delta(WEEK)
            for game in games:
                embed.add_field(name=game.name,
                                value=f"{game.release}\n{game.platforms}\n{game.url}",
                                inline=False)
            await interraction.response.send_message(embed=embed)

        async def month_callback(interraction: Interaction):
            embed = Embed(title="Sorties du mois")
            games = await fetch_time_delta(MONTH)
            for game in games:
                embed.add_field(name=game.name,
                                value=f"{game.release}\n{game.platforms}\n{game.url}",
                                inline=False)
            await interraction.response.send_message(embed=embed)

        button1.callback = day_callback
        button2.callback = week_callback
        button3.callback = month_callback

        view = View()
        view.add_item(button1)
        view.add_item(button2)
        view.add_item(button3)
        await ctx.send(view=view)

    @ commands.hybrid_command()
    async def sorties2(self, ctx: commands.Context, month: int, year: int):
        """Sorties JV

        Args:
            month (int): mois
            year (int): année
        """
        url, month, year = generate_url(month, year)
        embed = Embed(title=f"Sorties du mois {month} {year}")
        games = await fetch_month(url)
        for game in games:
            embed.add_field(name=game.name,
                            value=f"{game.release}\n{game.platforms}\n{game.url}",
                            inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(JV(bot))
    logger.info("Cog JV added")
