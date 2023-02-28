"""Lemonde -> PDF cog."""
import asyncio
import os
import random

import aiohttp
import discord
import pdfkit
from bs4 import BeautifulSoup
from discord.ext import commands
from reretry import retry

login_url = "https://secure.lemonde.fr/sfuser/connexion"
options = {
    'page-size': 'A4',
    'margin-top': '20mm',
    'margin-right': '20mm',
    'margin-bottom': '20mm',
    'margin-left': '20mm',
    'encoding': "UTF-8",
    # 'custom-header': [
    #     ('Accept-Encoding', 'gzip')
    # ],
    # 'cookie': [
    #     ('cookie-empty-value', '""')
    #     ('cookie-name1', 'cookie-value1'),
    #     ('cookie-name2', 'cookie-value2'),
    # ],
    'no-outline': None
}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    }


def select_tag(soup: BeautifulSoup, tag) -> dict:
    """Select tag in soup and return dict (name:value)."""
    items = soup.select(tag)
    return {i['name']: i['value'] for i in items if i.has_attr('name') if i.has_attr('value')}


def remove_bloasts(article: BeautifulSoup) -> BeautifulSoup:
    "Remove some bloats in the article soup."
    css = [
        ".meta__social",
        "ul.breadcrumb",
        "#habillagepub > section > section.article__wrapper.article__wrapper--premium > article > section.article__reactions",
        "section.friend",
        "aside.aside__iso.old__aside",
        "section.article__siblings",
    ]
    for c in css:
        try:
            article.select_one(c).decompose()  # remove some bloats
        except AttributeError:
            print(f"Fails to remove {c} bloat in the article. Pass.")


@retry(asyncio.exceptions.TimeoutError, tries=10, delay=2, backoff=1.2, jitter=(0, 1))
async def get_article(url: str):
    "Get the article from the URL"
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
        r = await session.get(url, headers=headers, timeout=5)
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
        await ctx.defer(ephemeral=False)
        # async with ctx.channel.typing():
        try:
            out_file = await get_article(url)
            await ctx.send(file=discord.File(out_file))
            os.remove(out_file)
        except TypeError:
            await ctx.send("no file to send, sorry, try again maybe ?")
