"""Youtube cog."""


# Sample Python code for youtube.search.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/guides/code_samples#python

import html
import logging
import os
from typing import NamedTuple

import discord
import googleapiclient.discovery
from discord.ext import commands

logger = logging.getLogger(__name__)

TOKEN_YOUTUBE = os.getenv("TOKEN_YOUTUBE")


class TitleURL(NamedTuple):
    title: str
    url: str


class Result(NamedTuple):  # pylint: disable=missing-class-docstring
    title: str
    type_: str
    id_: str


class YoutubeError(Exception):
    """Base class for YouTube-related errors."""


class NoYoutubeResults(YoutubeError):
    """Raised when a YouTube search returns no results."""


def string_is_int(string: str) -> bool:  # pragma: no cover
    """Return if 'string' is an int or not (bool)."""
    try:
        int(string)
        return True
    except ValueError:
        return False


def search_youtube(user_input: str, number: int) -> list[Result]:
    """Search on Youtube.

    Args:
        user_input (str): search string
        number (int): number of search results

    Returns:
        list: list of results

    """
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    # os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = TOKEN_YOUTUBE

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=DEVELOPER_KEY, cache_discovery=False
    )

    request = youtube.search().list(
        part="snippet",  # pylint: disable=no-member
        maxResults=number,
        q=user_input,
    )
    response = request.execute()

    items = response["items"]

    out = []

    for item in items:
        title = html.unescape(item["snippet"]["title"])
        try:
            if item["id"]["kind"] == "youtube#channel":
                type_ = "channel"
                id_ = item["id"]["channelId"]
            elif item["id"]["kind"] == "youtube#playlist":
                type_ = "playlist"
                id_ = item["id"]["playlistId"]
            elif item["id"]["kind"] == "youtube#video":
                type_ = "video"
                id_ = item["id"]["videoId"]
            else:
                type_ = "unknown"
                id_ = "NoID"
        except KeyError:  # pragma: no cover
            type_ = "unknown"
            id_ = "NoID"

        out.append(Result(title=title, type_=type_, id_=id_))

    return out


def youtube_top_link(user_input: str) -> TitleURL:
    """Return title and url of 1st Youtube search.

    Args:
        user_input (str): user search on Youtube

    Returns:
        TitleURL: title, url

    """
    results = search_youtube(user_input, number=1)
    if not results:
        raise NoYoutubeResults(user_input)

    result = results[0]
    url = get_youtube_url(result)
    return TitleURL(title=result.title, url=url)


def get_youtube_url(result: Result) -> str:
    """Make youtube url of 'result' (video, playlist, or channel).

    Args:
        result (Result): result tuple

    Raises:
        YoutubeError: type of result is messy

    Returns:
        str: url
    """
    if result.type_ == "channel":
        return f"https://www.youtube.com/channel/{result.id_}"
    if result.type_ == "playlist":
        return f"https://www.youtube.com/playlist?list={result.id_}"
    if result.type_ == "video":
        return f"https://www.youtube.com/watch?v={result.id_}"

    raise YoutubeError(f"Unknown YouTube result type: {result.type_}")


class Youtube(commands.Cog):
    """Youtube cog.
    Commands are youtube and youtubelist
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def youtube(self, ctx, *, query: str) -> None:
        """Send first Youtube search result.

        Args:
            query (str): Search on youtube
        """
        try:
            title, url = youtube_top_link(query.lower())
        except NoYoutubeResults:
            await ctx.send("Aucun résultat YouTube trouvé.")
            return

        link = await ctx.send(f"{title}\n{url}")

        def check(message):
            return message == ctx.message

        await self.bot.wait_for("message_delete", check=check, timeout=1200)
        await link.delete()

    @commands.hybrid_command()
    async def youtubelist(self, ctx, num: int, *, query: str) -> None:
        """Send <n> Youtube search results.

        Args:
            num (int): amount of desired results.
            query (str): search on youtube.
        """
        num = num if num <= 10 else 10
        results = search_youtube(user_input=query, number=num)
        embed = discord.Embed(color=0xFF0000)
        embed.set_footer(
            text="Tapez un nombre pour faire votre choix " 'ou dites "cancel" pour annuler'
        )
        for i, res in enumerate(results, start=1):
            url = get_youtube_url(res)
            embed.add_field(
                name=f"{i}.{res.type_}",
                value=f"[{res.title}]({url})",
                inline=False,
            )

        self_message = await ctx.send(embed=embed)

        def check(message):
            return message.author == ctx.author and (
                message.content == "cancel" or string_is_int(message.content)
            )

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=15)
            if msg.content == "cancel":
                await ctx.send("Annulé !", delete_after=5)
                await self_message.delete(delay=None)
                await ctx.message.delete(delay=2)
                await msg.delete(delay=1)
            else:
                num = int(msg.content)
                if 0 < num <= len(results):
                    url = get_youtube_url(results[num - 1])
                    await ctx.send(content=f"{url}")
                    await ctx.message.delete(delay=2)
                    await self_message.delete(delay=None)
                    await msg.delete(delay=1)

        except TimeoutError:
            await ctx.send("Tu as pris trop de temps pour répondre !", delete_after=5)
            await self_message.delete(delay=None)
            await ctx.message.delete(delay=2)


async def setup(bot):
    await bot.add_cog(Youtube(bot))
    logger.info("⚙️ Youtube cog added")
