import asyncio
import logging

from bs4 import BeautifulSoup, Tag
from playwright.async_api import TimeoutError, async_playwright
from requests_html import AsyncHTMLSession

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",  # noqa: E501
}


def to_bool(value: str, strict: bool = True) -> bool:
    """
    Convertit une chaîne en booléen.

    Cette fonction reconnaît plusieurs variantes de valeurs "vraies" et "fausses",
    en français et en anglais. Elle peut lever une exception si la valeur est invalide,
    ou retourner False par défaut en mode non strict.

    Paramètres :
        value (str) : La chaîne à convertir (ex. "oui", "no", "true", "0", etc.).
        strict (bool) : Si True, lève une ValueError pour les valeurs inconnues.
                        Si False, retourne False pour toute valeur non reconnue.

    Retour :
        bool : True ou False selon la valeur fournie.

    Exceptions :
        ValueError : Si strict=True et que la valeur n'est pas reconnue.
    """
    true_values = {"1", "true", "yes", "on", "oui"}
    false_values = {"0", "false", "no", "off", "non"}

    value_clean = value.strip().lower()
    if value_clean in true_values:
        return True
    elif value_clean in false_values:
        return False
    elif strict:
        raise ValueError(f"Valeur booléenne invalide : '{value}'")
    return False


def text_or_none(tag: Tag | None) -> str | None:
    """Safely returns a stripped text from tag (Tag | None)."""
    return tag.get_text(strip=True) if tag else None


def setup_logger(name: str, level: int | str = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


async def get_soup(url: str) -> BeautifulSoup:
    asession = AsyncHTMLSession()
    r = await asession.get(url, headers=headers)
    # await r.html.arender()
    await r.html.arender(timeout=20, sleep=2)
    await asession.close()
    soup = BeautifulSoup(r.html.html, "html.parser")
    return soup


async def fetch(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True
        )  # headless=True si tu veux rester invisible
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",  # noqa: E501
            locale="fr-FR",
        )

        # Enlève le flag webdriver
        await context.add_init_script(
            """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """
        )

        # Ajoute des headers réalistes
        await context.set_extra_http_headers(
            {"Accept-Language": "fr-FR,fr;q=0.9", "Referer": "https://www.google.com"}
        )

        page = await context.new_page()
        await page.goto(url, timeout=50000)  # 50s timeout
        await page.wait_for_timeout(10000)  # sleep=10s pour laisser le JS s'exécuter

        # Tu peux aussi simuler un scroll ou un clic si nécessaire
        await page.mouse.move(100, 100)
        await page.keyboard.press("ArrowDown")
        await page.wait_for_timeout(1000)

        html = await page.content()
        await browser.close()
        return html  # type: ignore


async def get_soup_hack(url: str) -> BeautifulSoup | None:
    """Fetch the site URL using playwright and return bs4 soup.

    Args:
        url (str): site to fetch

    Returns:
        BeautifulSoup: bs4 Soup of the page.
    """
    try:
        html = await fetch(url)
        return BeautifulSoup(html, "html.parser")
    except TimeoutError:
        print("Timeout Error")
        return None


if __name__ == "__main__":

    async def main():
        url = "https://www.jeuxvideo.com/jeux/sorties/machine-10/annee-2025/mois-10/"
        # url = "https://bot.sannysoft.com/"
        soup = await get_soup_hack(url)
        if soup:
            print(soup.prettify())

    asyncio.run(main())
