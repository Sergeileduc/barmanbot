"""Lemonde -> PDF cog."""
from discord import app_commands, Interaction
from discord.ext import commands
from bs4 import BeautifulSoup, Tag
import pdfkit
import discord
import aiohttp
import asyncio
import logging
import os

import random
from dataclasses import dataclass
from typing import Optional

from utils.base_cog import BaseSlashCog
from utils.decorators import dev_command
from utils.tools import to_bool
from utils.discord_types import Literal

# from reretry import retry

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# logger.addHandler(logging.StreamHandler())

LOGIN_URL = "https://secure.lemonde.fr/sfuser/connexion"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
}

# Retry
TRIES = 3
DELAY = 2
MAX_DELAY = None
BACKOFF = 1.2
# JITTER = 0
JITTER = (0, 1)

# Bloats in HTML
CSS_BLOATS = [
    ".meta__social",
    "ul.breadcrumb",
    "section.article__reactions",
    "section.friend",
    "section.article__siblings",
    "aside.aside__iso.old__aside",
    "section.inread",
    ]


def build_pdf_html(fragment: str, mobile: bool = False, dark: bool = False) -> tuple[str, dict]:
    """
    Construit un HTML complet + options PDFkit selon le format et le thème.

    Args:
        fragment (str): Contenu HTML à insérer dans le <body>.
        format (str): "A4" ou "mobile"
        dark (bool): True pour thème sombre, False pour thème clair

    Returns:
        tuple: (html_str, pdfkit_options)
    """
    # Configs de base
    if mobile:
        page_size = "A6"
        margin_mm = 7 if not dark else 0
        padding_mm = 0 if not dark else 7
    else:
        page_size = "A4"
        margin_mm = 20 if not dark else 0
        padding_mm = 0 if not dark else 20

    # Options PDFkit
    options = {
        'page-size': page_size,
        'margin-top': f'{margin_mm}mm',
        'margin-right': f'{margin_mm}mm',
        'margin-bottom': f'{margin_mm}mm',
        'margin-left': f'{margin_mm}mm',
        'encoding': "UTF-8",
        'no-outline': None,
        'custom-header': [('Accept-Encoding', 'gzip')],
        'enable-local-file-access': "",
    }

    # CSS selon thème
    if dark:
        css = f"""
        <style>
        html {{
            background: #121212;
        }}
        body {{
            background: transparent;
            color: #e0e0e0;
            margin: 0;
            padding: {padding_mm}mm;
            font-family: sans-serif;
            font-size: 12pt;
            line-height: 1.6;
            box-sizing: border-box;
        }}
        a {{ color: #90caf9; }}
        img {{ filter: brightness(0.8) contrast(1.2); max-width: 100%; height: auto; }}
        </style>
        """
    else:
        css = """
            <style>
            body {
                font-family: sans-serif;
                font-size: 12pt;
                line-height: 1.6;
            }
            </style>
        """

    # HTML complet
    html = f"""
    <html>
    <head>
    <meta charset="UTF-8">
    {css}
    </head>
    <body>
    {fragment}
    </body>
    </html>
    """

    return html.strip(), options


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


def remove_bloasts(css_list: list[str], article: Tag):
    "Remove some bloats in the article soup."
    for c in css_list:
        try:
            list_elements = article.select(c)
            for elem in list_elements:
                elem.decompose()  # remove some bloats
                logger.debug("Element %s decomposed", c)
        except AttributeError:
            logger.info("FAILS to remove %s bloat in the article. Pass.", c)


def fix_images_urls(article: BeautifulSoup) -> None:
    """Fixes image URLs in the provided article by updating the 'src' attribute.

    This function scans the article for image tags and updates their 'src'
    attributes based on the 'data-srcset' attribute. It ensures that the images
    are correctly referenced for display.

    Args:
        article (BeautifulSoup): The BeautifulSoup object representing
        the article from which to fix image URLs.

    Returns:
        None
    """

    imgs = article.select("img")
    for im in imgs:
        if im.has_attr("data-srcset"):
            srcset = im["data-srcset"]
            tmpsrc = srcset.split(",")
            for tmp in tmpsrc:
                if "664w" in tmp or "1x" in tmp:
                    url_im = tmp.strip().split(" ")[0]
                    im["src"] = url_im


@dataclass
class MyArticle:
    path_to_file: str
    error: Optional[str] = None

# @retry(asyncio.exceptions.TimeoutError, tries=10, delay=2, backoff=1.2, jitter=(0, 1))


async def get_article(url: str, mobile: bool = False, dark_mode: bool = False) -> MyArticle | None:
    """Get the article from the URL

    Args:
        url (str): url of article to be fetched
        mobile (bool): is the PDF is for mobile ? default is False.
        dark_mode (bool): is the PDF in dark mode ? default is False

    Returns:
        MyArticle | None
    Raises:
        IOError: if wkhtmltopdf fails, it raises IOError
    """
    session = aiohttp.ClientSession(headers=headers)
    # Login
    r = await session.get(LOGIN_URL)
    soup: BeautifulSoup = BeautifulSoup(await r.text(), "html.parser")
    form = soup.select_one('form[method="post"]')
    payload = select_tag(form, "input")
    email = os.getenv("LEMONDE_EMAIL")
    payload['email'] = email
    payload['password'] = os.getenv("LEMONDE_PASSWD")
    rp = await session.post(LOGIN_URL, data=payload)
    if rp.status != 200 or email not in await rp.text():
        raise ValueError("Wrong login")
    else:
        logger.info("Login was ok")
    await asyncio.sleep(random.uniform(2.0, 3.0))

    html = None
    # Fetch article and print in PDF
    try:
        r = await session.get(url, headers=headers, timeout=6)
        logger.info("status : %s", r.status)
        html = await r.text()
        logger.info("Get was ok")
    except asyncio.exceptions.TimeoutError:
        logger.warning("Timeout !")
        raise
    finally:
        await session.close()

    if html:
        logger.info("Ok, doing some magic on HTML")
        soup = BeautifulSoup(html, 'html.parser')
        article = soup.select_one("main > .article--content")
        # article = soup.select_one("section.zone--article")
        # article = soup.select_one(".zone.zone--article")
        remove_bloasts(CSS_BLOATS, article)
        fix_images_urls(article)
        # ------------
        article, options = build_pdf_html(article, mobile=mobile, dark=dark_mode)

        # --------------------
        full_name = url.rsplit('/', 1)[-1]
        out_file: str = f"{os.path.splitext(full_name)[0]}.pdf"
        logger.info("Ok, making the pdf now.")

        try:
            pdfkit.from_string(str(article), out_file, options=options)
            logger.info("Returning file")
            return MyArticle(out_file)
        except IOError as e:
            logger.error("wkhtml a eu un problème")
            logger.error(e)
            logger.error("on va essayer d'enlever les media-embed")
            remove_bloasts(["div.multimedia-embed",], article)
            pdfkit.from_string(str(article), out_file, options=options)
            logger.info("Returning file")
            return MyArticle(out_file, error="Article contenant du multimédia que le bot a supprimé, article probablement incomplet.")
    return None


# class LeMonde(commands.Cog):
#     """LeMonde commands"""

#     def __init__(self, bot: commands.Bot):
#         self.bot = bot


class LeMonde(BaseSlashCog):
    """LeMonde commands"""

    def __init__(self, bot):
        super().__init__(bot)

    @dev_command(name="lemonde", description="Télécharge un article du Monde")
    @app_commands.describe(url="URL de l'article à télécharger",
                           mode="Choisir mobile et/ou dark theme",
                           )
    async def lemonde(self,
                      interaction: discord.Interaction,
                      url: str,
                      mode: Literal["Normal Clair", "Normal Dark", "Mobile Clair", "Mobile Dark"] = "Normal Clair",
                      ):
        """
        Télécharge un article depuis Lemonde.fr et l'affiche dans Discord.

        Args:
            interaction(discord.Interaction): L'interaction Discord.
            url (str): Lien vers l'article.
            mobile (Literal["Oui", "Non"]): Mode mobile.
            dark_mode (Literal["Oui", "Non"]): Mode sombre.

        Comportement :
            - Affiche les paramètres reçus dans un message de suivi.
            - Tente de récupérer l'article avec plusieurs essais en cas de timeout.
            - Utilise `to_bool()` pour convertir les paramètres en booléens.
        """

        mobile: bool = "Mobile" in mode
        dark_mode: bool = "Dark" in mode

        await interaction.response.defer(ephemeral=False)

        # Log pour debug
        logger.info(f"Commande /lemonde appelée avec url={url}, mobile={mobile}, dark_mode={dark_mode}")
        await interaction.followup.send(f"📄 Article: {url}\n📱 Mobile: {mobile}\n🌙 Mode sombre: {dark_mode}")

        # Retry
        _tries, _delay = TRIES, DELAY

        msg_wait = await interaction.followup.send("⏳ Traitement en cours…",
                                                   ephemeral=False)
        # While loop to retry fetching article, in case of Timeout errors
        while _tries:
            try:
                my_article: MyArticle = await get_article(url=url,
                                                          mobile=mobile,
                                                          dark_mode=dark_mode)
                logger.info("out file ok")
                break
            except asyncio.exceptions.TimeoutError:
                logger.warning("Timeout in retry code !!!")
                _tries -= 1
                logger.warning("Tries left = %d", _tries)

                error_message = ("Erreur : Timeout. "
                                 f"Tentative {TRIES - _tries}/{TRIES} échec - "
                                 f"Nouvel essai dans {_delay:.2f} secondes...")
                delete_after = _delay + 1.9
                await interaction.followup.send(error_message, delete_after=delete_after)
                if not _tries:
                    raise

                await asyncio.sleep(_delay)

                _delay = _new_delay(MAX_DELAY, BACKOFF, JITTER, _delay)
        # End of retry While loop

        try:
            # await interaction.followup.send(content=url)
            await interaction.followup.send(file=discord.File(my_article.path_to_file))
            if my_article.error:
                await interaction.followup.send(my_article.error)
            os.remove(my_article.path_to_file)
        except (TypeError, FileNotFoundError):
            await interaction.followup.send("Echec de la commande. Réessayez, peut-être ?")
        finally:
            msg_wait.delete()
            logger.info("------------------")


async def setup(bot):
    """
    Sets up the LeMonde cog for the provided Discord bot instance.

    This asynchronous function adds the LeMonde cog to the bot and logs a message
    indicating the successful addition of the cog.

    Args:
        bot: The Discord bot instance to which the cog will be added.

    Returns:
        None
    """
    await bot.add_cog(LeMonde(bot))
    logger.info("lemonde cog added")


# TESTING
if __name__ == "__main__":
    # Testing lemonde pdf
    import platform
    from dotenv import load_dotenv
    # Parse a .env file and then load all the variables found as environment variables.
    load_dotenv()

    logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)

    # URL = "https://www.lemonde.fr/international/article/2024/10/03/face-a-l-iran-la-france-se-range-derriere-israel_6342763_3210.html"
    URL = "https://www.lemonde.fr/societe/article/2024/10/05/proces-des-viols-de-mazan-le-huis-clos-leve-les-accuses-maintiennent-leur-version-apres-le-visionnage-des-videos_6344040_3224.html"
    # URL = "https://www.lemonde.fr/les-decodeurs/article/2025/09/25/condamnation-de-nicolas-sarkozy-la-chronologie-complete-de-l-affaire-du-financement-libyen_6482596_4355771.html"
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(get_article(URL, mobile=True, dark_mode=True))
    except IOError as e:
        logger.error("Erreur IOError")
        logger.error(e)
