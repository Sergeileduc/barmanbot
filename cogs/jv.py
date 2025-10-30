#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""JV cog."""

import asyncio
import contextlib
import logging
import re
from datetime import date, timedelta
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup, Tag
from dateparser.date import DateDataParser
from discord import Embed, Interaction, ButtonStyle
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
    """Represents a video game with metadata such as name, release date, platforms, and URL.

    This class encapsulates basic information about a game and provides a formatted
    string representation. The release date is parsed from a raw string and converted
    to a `datetime.date` object. If parsing fails, a default placeholder date is used.
    """

    def __init__(self, name: str, release: str, platforms: str, part_url: str) -> None:
        """Initializes a new game instance.

        Args:
            name (str): The name of the game.
            release (str): The raw release string, typically like 'Sortie: 12 décembre 2023'.
            platforms (str): The platforms the game is available on.
            part_url (str): The partial URL path to be joined with the base site.
        """

        self.name = name
        self.release = release
        self.platforms = platforms
        self.url = urljoin("https://www.jeuxvideo.com", part_url)
        self.date = self._parse_release_date(release)

    @staticmethod
    def _parse_release_date(release: str) -> date:
        """Parses a release string into a date object.

        Removes the 'Sortie: ' prefix from the release string and attempts to
        convert the remaining text into a `datetime.date` object using `ddp.get_date_data`.

        If parsing fails due to missing attributes, returns a fallback date far
        in the future (January 1st, 3000).

        Args:
            release (str): A release string, typically formatted like
                'Sortie: 12 décembre 2023'.

        Returns:
            date: The parsed release date, or a default placeholder date.
        """

        try:
            date_str = re.sub('Sortie: ', '', release)
            return ddp.get_date_data(date_str).date_obj.date()
        except AttributeError:
            return date(3000, 1, 1)

    def __str__(self) -> str:
        return f"{self.name}\n{self.release}\n{self.platforms}\n{self.url}\n{self.date}\n----------"


class TimeButton(Button):
    """Class for the buttons 'Jour', 'Semaine', 'Mois'
    """

    def __init__(self, label: str, row: int,
                 delta: timedelta, embedtitle: str) -> None:
        """Each button has his own label, row, timedelta and embed title"""
        super().__init__(label=label, row=row)
        self.delta = delta
        self.title = embedtitle

    async def callback(self, interaction: Interaction):
        platform = self.view.platform
        one_platform = platform != "Toutes"

        # change style to green when clicked
        self.style = ButtonStyle.green
        await interaction.response.edit_message(view=self.view)

        full_title = f"{self.title} sur {platform}" if one_platform else self.title
        embed = Embed(title=full_title)
        games = await fetch_time_delta(self.delta, platform=platform)
        for game in games:
            if game.platforms != "no platform":
                value = f"{game.release}\n{game.platforms}\n{game.url}"
            else:
                value = f"{game.release}\n{game.url}"
            embed.add_field(name=game.name,
                            value=value,
                            inline=False)
        await interaction.followup.send(embed=embed)


class PlatformButton(Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: Interaction):
        # await interraction.response.defer()
        self.view.platform = self.label
        # change style to green when clicked
        self.style = ButtonStyle.green
        await interaction.response.edit_message(view=self.view)


def _unbloat_title(title: Tag):
    with contextlib.suppress(AttributeError):
        em = title.find("em")
        em.decompose()  # remove some bloats


def find_next_page(tag: Tag):
    """Find if there is a button "next page".

    Args:
        tag (Tag): Beautiful Soup Tag

    Returns:
        bool, str: if found, then give the url for next page
    """
    found = False
    url = ""
    if nextpage := tag.find("a", class_=re.compile("page")):
        url = urljoin("https://www.jeuxvideo.com", nextpage.get("href"))
        found = True
    return found, url


def generate_url(month: int, year: int, platform=None) -> str:
    """Generates a jeuxvideo.com release calendar URL for a given month, year, and platform.

    Converts the numeric month into its French name and builds the appropriate URL
    based on the selected platform. If the platform is not recognized, returns None.

    Supported platforms:
        - "PC"
        - "PS5"
        - "Switch"
        - "Xbox"
        - "Toutes" (all platforms)

    Args:
        month (int): Month number (1–12).
        year (int): Year of the release calendar.
        platform (str, optional): Target platform. Defaults to None.

    Returns:
        str: A formatted URL string for the release calendar, or None if the platform is unsupported.
    """

    french_months = ['janvier', 'fevrier', 'mars', 'avril', 'mai', 'juin',
                     'juillet', 'aout',
                     'septembre', 'octobre', 'novembre', 'decembre']
    french_m = french_months[month - 1]
    logger.debug("generate_url - platform: %s", platform)
    if platform == "PC":
        return f"https://www.jeuxvideo.com/sorties/dates-de-sortie-pc-{french_m}-{year}-date.htm"
    elif platform == "PS5":
        return f"https://www.jeuxvideo.com/sorties/dates-de-sortie-ps5-playstation-5-{french_m}-{year}-date.htm"
    elif platform == "Switch":
        return f"https://www.jeuxvideo.com/sorties/dates-de-sortie-switch-nintendo-switch-{french_m}-{year}-date.htm"
    elif platform == "Xbox":
        return f"https://www.jeuxvideo.com/sorties/dates-de-sortie-xbox-series-{french_m}-{year}-date.htm"
    elif platform == "Toutes":
        return f"https://www.jeuxvideo.com/sorties/dates-de-sortie-{french_m}-{year}-date.htm"
    else:
        return None


def next_month(month: int, year: int):
    """Return a tuple of month and year for next month.

    Args:
        month(int): current month
        year(int): current year

    Returns:
        (int, int): next month tuple of month and year
    """
    return (month + 1, year) if month != 12 else (1, year + 1)


async def fetch_page(url: str):
    """Fetch a page on JV, for month releases. If pagination, return the next url.

    Args:
        url(str): url of the release page
    """
    async with aiohttp.ClientSession() as session:
        res = await session.get(url, headers=headers)
        soup = BeautifulSoup(await res.text(), "html.parser")
        print(soup.prettify())
    list_of_new_games = soup.select("div[class*='gameMetadatas']")
    pagination = soup.select_one("div[class*='pagination']")
    pages, url = find_next_page(pagination)

    releases = []
    for sortie in list_of_new_games:
        title_tag = sortie.select_one("a[class*='gameTitleLink']")
        _unbloat_title(title_tag)
        title = title_tag.text
        _date = sortie.select_one("span[class*='releaseDate']").text
        try:
            tmp = sortie.select_one("div[class*='platforms']").text
            platform = f"Plateformes :\t {tmp}"
        except AttributeError:
            platform = "no platform"
        try:
            part = sortie.select_one("div > span > h2 > a").get("href")
        except AttributeError:
            part = None
        releases.append(NewGame(name=title, release=_date, platforms=platform, part_url=part))
    return releases, pages, url


async def fetch_month(url):
    """Fetch all games in a month, even if there are several pages."""
    logger.debug("fetch_month url : %s", url)
    pages = True
    games = []
    while pages:
        games_page, pages, url = await fetch_page(url)
        games += games_page
    return games


async def fetch_time_delta(delta: timedelta, platform: str = None):
    """Fetch games in a time delta relative to today(one week, one month, etc...)"""
    today = date.today()
    int_month = today.month
    int_year = today.year

    url = generate_url(today.month, today.year, platform=platform)
    logger.debug("fetch_time_delta url : %s", url)
    games = await fetch_month(url)
    # next month
    new_month, new_year = next_month(int_month, int_year)
    url = generate_url(new_month, new_year, platform=platform)
    games += await fetch_month(url)
    return [game for game in games
            if (diff := game.date - today) <= delta and diff.days >= 0]


class JV(commands.Cog):
    """Fetch Video games release date."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command()
    async def sorties(self, ctx: commands.Context):
        """Permet de voir les prochaines sorties."""
        await ctx.defer(ephemeral=False)

        view = View()
        view.platform = None

        platbutton1 = PlatformButton(label="Toutes", row=0)
        platbutton2 = PlatformButton(label="PS5", row=0)
        platbutton3 = PlatformButton(label="Xbox", row=0)
        platbutton4 = PlatformButton(label="Switch", row=0)
        platbutton5 = PlatformButton(label="PC", row=0)

        button1 = TimeButton(label="Jour", row=1, delta=DAY, embedtitle="Sorties du jour")
        button2 = TimeButton(label="Semaine", row=1, delta=WEEK, embedtitle="Sorties de la semaine")
        button3 = TimeButton(label="Mois", row=1, delta=MONTH, embedtitle="Sorties du mois")

        view.add_item(platbutton1)
        view.add_item(platbutton2)
        view.add_item(platbutton3)
        view.add_item(platbutton4)
        view.add_item(platbutton5)
        view.add_item(button1)
        view.add_item(button2)
        view.add_item(button3)

        await ctx.send(view=view)


async def setup(bot):
    "Add the cog to the bot."
    await bot.add_cog(JV(bot))
    logger.info("Cog JV added")


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)

    async def main():
        # url = generate_url(10, 2025, "PC")
        url = "https://www.jeuxvideo.com/jeux/sorties/machine-22/annee-2025/mois-10/"
        print(url)
        r, p, u = await fetch_page(url)
        print(r)
        print(p)
        print(u)

    asyncio.run(main())
