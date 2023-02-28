"""Lemonde -> PDF cog."""
import asyncio
import os
import random

import aiohttp
import discord
import pdfkit
from bs4 import BeautifulSoup
from discord.ext import commands
# from reretry import retry

login_url = "https://secure.lemonde.fr/sfuser/connexion"
options = {
    'page-size': 'A4',
    'margin-top': '20mm',
    'margin-right': '20mm',
    'margin-bottom': '20mm',
    'margin-left': '20mm',
    'encoding': "UTF-8",
    'no-outline': None
}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    }


# Retry
tries = 10
delay = 2
max_delay = None
backoff = 1.2
# jitter = 0
jitter = (0, 1)


def _new_delay(max_delay, backoff, jitter, delay):
    delay *= backoff
    delay += random.uniform(*jitter) if isinstance(jitter, tuple) else jitter

    if max_delay is not None:
        delay = min(delay, max_delay)

    return delay


def select_tag(soup: BeautifulSoup, selector: str) -> dict:
    """Select tag in soup and return dict (name:value)."""
    items = soup.select(selector)
    return {i['name']: i['value'] for i in items if i.has_attr('name') if i.has_attr('value')}


def remove_bloasts(article: BeautifulSoup):
    "Remove some bloats in the article soup."
    css = [
        ".meta__social",
        "ul.breadcrumb",
        ".article__siblings",
        "#habillagepub > section > section.article__wrapper.article__wrapper--premium > article > section.article__reactions",
        "section.friend",
        "aside.aside__iso.old__aside",
        # "#habillagepub > section > section.article__wrapper.article__wrapper--premium > footer > section:nth-child(3)",
    ]
    for c in css:
        try:
            article.select_one(c).decompose()  # remove some bloats
        except AttributeError:
            print(f"Fails to remove {c} bloat in the article. Pass.")


# @retry(asyncio.exceptions.TimeoutError, tries=10, delay=2, backoff=1.2, jitter=(0, 1))
async def get_article(url: str) -> str:
    """Get the article from the URL

    Args:
        url (str): url of article to be fetched

    Returns:
        str: path to the PDF file
    """
    session = aiohttp.ClientSession()
    # Login
    r = await session.get(login_url)
    soup = BeautifulSoup(await r.text(), "html.parser")
    form = soup.select_one('form[method="post"]')
    post_url = form.get('action')
    payload = select_tag(form, "input")
    payload['email'] = os.getenv("LEMONDE_EMAIL")
    payload['password'] = os.getenv("LEMONDE_PASSWD")
    rp = await session.post(post_url, data=payload)
    if rp.status == 200:
        print("Login OK")
    await asyncio.sleep(random.uniform(2.0, 3.0))

    html = None
    # Fetch article and print in PDF
    try:
        r = await session.get(url, headers=headers, timeout=6)
        print(r.status)
        html = await r.text()
        print("Get was ok")
    except asyncio.exceptions.TimeoutError:
        print("Timeout !")
        raise
    finally:
        await session.close()

    if html:
        print("Ok, making the PDF now")
        soup = BeautifulSoup(html, 'html.parser')
        article = soup.select_one("main > .article--content")
        # article = soup.select_one("section.zone--article")
        # article = soup.select_one(".zone.zone--article")
        # print(soup.prettify())
        remove_bloasts(article)
        # print(article.prettify())
        full_name = url.rsplit('/', 1)[-1]
        out_file = f"{os.path.splitext(full_name)[0]}.pdf"
        pdfkit.from_string(str(article), out_file, options=options)
        print("Returning file")
        return out_file
    return None


class LeMonde(commands.Cog):
    """LeMonde commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command()
    # @commands.command()
    async def lemonde(self, ctx: commands.Context, url: str):
        "Download an article from Lemonde.fr"

        # Retry
        _tries, _delay = tries, delay

        await ctx.defer(ephemeral=False)

        # While loop to retry fetching article, in case of Timeout errors
        while _tries:
            try:
                out_file = await get_article(url)
                print("out file ok")
                break
            except asyncio.exceptions.TimeoutError as e:
                print("Timeout in retry code !!!", e)
                _tries -= 1
                print(f"Tries left = {_tries}")

                error_message = ("Erreur : Timeout. "
                                 f"Tentative {tries - _tries}/{tries} échec - "
                                 f"Nouvel essai dans {_delay:.2f} secondes...")
                delete_after = _delay + 1.9
                await ctx.channel.send(error_message, delete_after=delete_after)
                if not _tries:
                    raise

                await asyncio.sleep(_delay)

                _delay = _new_delay(max_delay, backoff, jitter, _delay)
        # End of retry While loop

        try:
            await ctx.send(file=discord.File(out_file))
            os.remove(out_file)
        except TypeError:
            await ctx.send("Echec de la commande. Réessayez, peut-être ?")
        finally:
            print("------------------")
