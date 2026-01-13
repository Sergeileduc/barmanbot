#!/usr/bin/python3
"""JV cog."""

import asyncio
import contextlib
import logging
import re
from collections.abc import Awaitable, Callable
from datetime import date, timedelta
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from dateparser.date import DateDataParser
from discord import ButtonStyle, Embed, Interaction
from discord.ext import commands
from discord.ui import Button, View

from utils.tools import get_soup_hack

logger = logging.getLogger(__name__)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",  # noqa: E501
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
            date_str = re.sub("Sortie: ", "", release)
            return ddp.get_date_data(date_str).date_obj.date()
        except AttributeError:
            return date(3000, 1, 1)

    def __str__(self) -> str:
        return f"{self.name}\n{self.release}\n{self.platforms}\n{self.url}\n{self.date}\n----------"


class TimeButton(Button):
    """Class for the buttons 'Jour', 'Semaine', 'Mois'"""

    def __init__(self, label: str, row: int, delta: timedelta, embedtitle: str) -> None:
        """Each button has his own label, row, timedelta and embed title"""
        super().__init__(label=label, row=row)
        self.delta = delta
        self.title = embedtitle

    async def callback(self, interaction: Interaction):
        # await interaction.response.defer(ephemeral=False)

        platform = self.view.platform
        one_platform = platform != "Toutes"

        # change style to green when clicked
        self.style = ButtonStyle.green
        await interaction.response.edit_message(view=self.view)

        full_title = f"{self.title} sur {platform}" if one_platform else self.title
        embeds = []
        current_embed = Embed(title=full_title)

        # this command takes TIME, so warn the user !
        await interaction.followup.send(content="ça va prendre du temps ! c'est normal !")

        games = await fetch_time_delta(self.delta, platform=platform)

        for game in games:
            if len(current_embed.fields) >= 25:
                embeds.append(current_embed)
                current_embed = Embed(title="Suite de la liste")

            if game.platforms != "no platform":
                value = f"{game.release}\n{game.platforms}\n{game.url}"
            else:
                value = f"{game.release}\n{game.url}"

            current_embed.add_field(name=game.name, value=value, inline=False)

        embeds.append(current_embed)  # Ajoute le dernier embed

        for embed in embeds:
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


# def find_next_page(soup: BeautifulSoup):
#     """Find if there is a button "next page".

#     Args:
#         soup (BeautifulSoup): Beautiful Soup

#     Returns:
#         bool, str: if found, then give the url for next page
#     """
#     found = False
#     url = ""
#     pagination = soup.select_one("div.pagination")
#     if not pagination:
#         return False, None
#     if nextpage := pagination.find("a", class_=re.compile("page")):
#         print("NEXT")
#         url = urljoin("https://www.jeuxvideo.com", nextpage.get("href"))
#         found = True
#     return found, url


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
    """  # noqa: E501

    # french_months = ['janvier', 'fevrier', 'mars', 'avril', 'mai', 'juin',
    #                  'juillet', 'aout',
    #                  'septembre', 'octobre', 'novembre', 'decembre']
    # french_m = french_months[month - 1]
    # logger.debug("generate_url - platform: %s", platform)
    # if platform == "PC":
    #     return f"https://www.jeuxvideo.com/sorties/dates-de-sortie-pc-{french_m}-{year}-date.htm"
    # elif platform == "PS5":
    #     return f"https://www.jeuxvideo.com/sorties/dates-de-sortie-ps5-playstation-5-{french_m}-{year}-date.htm"
    # elif platform == "Switch":
    #     return f"https://www.jeuxvideo.com/sorties/dates-de-sortie-switch-nintendo-switch-{french_m}-{year}-date.htm"
    # elif platform == "Xbox":
    #     return f"https://www.jeuxvideo.com/sorties/dates-de-sortie-xbox-series-{french_m}-{year}-date.htm"
    # elif platform == "Toutes":
    #     return f"https://www.jeuxvideo.com/sorties/dates-de-sortie-{french_m}-{year}-date.htm"
    # else:
    #     return None

    if platform == "PC":
        return f"https://www.jeuxvideo.com/jeux/sorties/machine-10/annee-{year}/mois-{month}/"
    elif platform == "PS5":
        return f"https://www.jeuxvideo.com/jeux/sorties/machine-22/annee-{year}/mois-{month}/"
    elif platform == "Switch":
        # TODO : ça ne fait que la switch 2, pas la 1, faudrait améliorer ça
        return f"https://www.jeuxvideo.com/jeux/sorties/machine-42/annee-{year}/mois-{month}/"
    elif platform == "Xbox":
        return f"https://www.jeuxvideo.com/jeux/sorties/machine-32/annee-{year}/mois-{month}/"
    elif platform == "Toutes":
        return f"https://www.jeuxvideo.com/jeux/sorties/annee-{year}/mois-{month}/"


def next_month(month: int, year: int):
    """Return a tuple of month and year for next month.

    Args:
        month(int): current month
        year(int): current year

    Returns:
        (int, int): next month tuple of month and year
    """
    return (month + 1, year) if month != 12 else (1, year + 1)


def _get_platform(tag: Tag) -> str:
    """Get platform from the website

    Args:
        tag (Tag): div for one video game

    Returns:
        str: the platform the game will be available
    """
    try:
        tmp = tag.select_one("div.cardGameList__gamePlatforms").get_text(strip=True)
        platform = f"Plateformes :\t {tmp}"
    except AttributeError:
        platform = "no platform"
    return platform


# def _extract_release_date(html: Tag) -> str:
#     """get the date from the HTML

#     Args:
#         tag (Tag): div for one video game

#     Returns:
#         str: date formated in french string
#     """
#     date_span = html.select_one("span.cardGameList__releaseDate span")
#     if date_span:
#         return date_span.get_text(strip=True)
#     return None


def _extract_game_href(html: Tag) -> str | None:
    """get the partial URL of a video game (in the div)

    Args:
        html (Tag): div for one video game

    Returns:
        str | None: partial URL
    """
    link_tag = html.select_one("a.cardGameList__gameTitleLink")
    if link_tag and link_tag.has_attr("href"):
        return link_tag["href"]
    return None


async def scrape_page(soup: BeautifulSoup) -> list[NewGame]:
    """Scrape a page on JV, for month releases.

    Args:
        soup (BeautifulSoup): soup for the page

    Returns:
        list[NewGame]: list of games for the page
    """

    releases = []
    try:
        list_of_new_games = soup.select("div[class*='gameMetadata']")
    except AttributeError:
        return releases

    for sortie in list_of_new_games:
        title_tag = sortie.select_one("a[class*='gameTitleLink']")
        _unbloat_title(title_tag)
        title = title_tag.text
        _date = sortie.select_one("span[class*='releaseDate']").text
        platform = _get_platform(sortie)
        try:
            part = _extract_game_href(sortie)
        except AttributeError:
            part = None
        releases.append(NewGame(name=title, release=_date, platforms=platform, part_url=part))
    return releases


async def scrape_all_pages(
    start_url: str, process_page_callback: Callable[[BeautifulSoup], Awaitable[list]]
) -> list:
    """Parcourt toutes les pages d'une pagination à partir d'une URL complète (version async).

    Args:
        start_url (str): L'URL complète de la première page (ex. "https://www.jeuxvideo.com/jeux/sorties/annee-2026/?p=1").
        process_page_callback (Callable[[BeautifulSoup], Awaitable[List]]):
            Une fonction async qui prend un objet BeautifulSoup et retourne une liste d'éléments extraits.

    Returns:
        List: Une liste contenant tous les éléments extraits de toutes les pages.
    """  # noqa: E501
    current_url = start_url
    visited = set()
    all_results = []

    while current_url and current_url not in visited:
        visited.add(current_url)
        logger.info(f"Scraping {current_url}")
        soup = await get_soup_hack(current_url)

        page_results = await process_page_callback(soup)
        if isinstance(page_results, list):
            all_results.extend(page_results)
        else:
            logger.info("⚠️ La fonction de traitement n'a pas retourné une liste.")

        next_link = soup.select_one(".pagination__button--next")
        if next_link and "href" in next_link.attrs:
            current_url = urljoin(current_url, next_link["href"])
        else:
            current_url = None

    return all_results


async def fetch_month(url) -> list[NewGame]:
    """Fetch all games in a month, even if there are several pages."""
    logger.debug("fetch_month url : %s", url)
    return await scrape_all_pages(start_url=url, process_page_callback=scrape_page)


async def fetch_time_delta(delta: timedelta, platform: str = None):
    """Fetch games in a time delta relative to today(one week, one month, etc...)"""
    today = date.today()
    int_month: int = today.month
    int_year: int = today.year

    url: str = generate_url(today.month, today.year, platform=platform)
    logger.debug("fetch_time_delta url : %s", url)
    games = await fetch_month(url)
    # next month
    new_month, new_year = next_month(int_month, int_year)
    url = generate_url(new_month, new_year, platform=platform)
    games += await fetch_month(url)
    return [game for game in games if (diff := game.date - today) <= delta and diff.days >= 0]


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

    def print_page_title(soup):
        try:
            title = soup.title.string.strip() if soup.title else "Sans titre"
            print("Titre de la page :", title)
            return [title]
        except AttributeError:
            return []

    async def main():
        # url = generate_url(10, 2025, "PC")
        # url = "https://www.jeuxvideo.com/jeux/sorties/machine-22/annee-2025/mois-10/"
        # url = "https://www.jeuxvideo.com/jeux/sorties/machine-32/annee-2025/mois-10/"
        # url = "https://www.jeuxvideo.com/jeux/sorties/annee-2025/mois-10/"
        url = "https://www.jeuxvideo.com/jeux/sorties/annee-2026/"
        print(url)

        # results = await fetch_month(url)
        results = await fetch_time_delta(delta=MONTH, platform="PC")
        for r in results:
            print(r)

    asyncio.run(main())
