import logging
import os

from discord import Object, app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)
DEV_MODE = os.getenv("DEV_MODE") == "1"
DEV_GUILD_ID = int(os.getenv("DEV_GUILD_ID", "0"))


class BaseSlashCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._dev_guilds = set()

    async def cog_load(self):
        """
        Enregistre et synchronise les commandes slash du cog.

        - En mode développement (DEV_MODE=1) :
            - Ajoute explicitement les commandes marquées avec un attribut `_dev_guild`
              à l'arbre de commandes pour la guild spécifiée.
            - Effectue un `sync(guild=...)` pour chaque guild concernée, avec propagation immédiate.

        - En mode production :
            - Ne fait aucun `add_command()` manuel.
            - Se contente de synchroniser globalement les commandes décorées avec `@app_commands.command`.

        Cette méthode est appelée automatiquement lors du chargement du cog.
        """  # noqa: E501
        for attr_name in dir(self):
            if attr_name.startswith("_"):
                continue

            attr = getattr(self, attr_name)

            if isinstance(attr, app_commands.Command):
                guild = getattr(attr, "_dev_guild", None)

                if DEV_MODE and guild:
                    self.bot.tree.add_command(attr, guild=guild, override=True)
                    self._dev_guilds.add(guild.id)
                    logger.info(f"📎 Dev-only command enregistrée : {attr.name} (guild={guild.id})")
                else:
                    logger.info(f"📎 Commande détectée pour enregistrement global : {attr.name}")

        await self.sync_commands()

    async def sync_commands(self):
        """
        Synchronise les commandes slash enregistrées dans l'arbre `bot.tree`.

        - En mode développement (DEV_MODE=1) :
            - Effectue un `sync(guild=...)` pour chaque guild enregistrée via `_dev_guilds`
            - Permet une propagation immédiate des commandes locales pour test

        - En mode production :
            - Effectue un `sync()` global
            - Les commandes décorées avec `@app_commands.command` sont propagées à toutes les guilds (avec délai Discord)

        Cette méthode est appelée explicitement dans `cog_load()` et n'est pas un hook Discord.py.
        """  # noqa: E501
        try:
            if DEV_MODE and self._dev_guilds:
                for guild_id in self._dev_guilds:
                    await self.bot.tree.sync(guild=Object(id=guild_id))
                    logger.info(f"🔄 Sync dev pour guild={guild_id}")
            else:
                await self.bot.tree.sync()
                logger.info("🌍 Sync global en prod")
        except Exception as e:
            logger.warning(f"⚠️ Échec du sync : {e}")
