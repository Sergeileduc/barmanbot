from functools import wraps
import os
from discord import app_commands, Object

DEV_MODE = os.getenv("DEV_MODE", "").strip().lower() in ("1", "true", "yes", "on")
DEV_GUILD_ID = int(os.getenv("DEV_GUILD_ID", "0"))


def dev_command(**kwargs):
    """
    décorateur `@dev_command`, conçu pour faciliter l'enregistrement conditionnel
    des commandes slash (`@app_commands.command`) dans un environnement de développement ou de production.

    Fonctionnalités :
    - Permet d'enregistrer une commande slash dans une guild spécifique en mode développement.
    - En mode production, la commande est enregistrée globalement.
    - Ajoute dynamiquement un attribut `_dev_guild` à la commande, utilisé par `BaseSlashCog` pour l'enregistrement.

    Utilisation :
    - À utiliser à la place de `@app_commands.command` dans les cogs héritant de `BaseSlashCog`.
    - Le mode est contrôlé par la constante `DEV_MODE` (True pour dev, False pour prod).
    - L'ID de la guild de test est défini par `DEV_GUILD_ID`.

    Exemple :
        @dev_command(name="ping", description="Répond pong")
        async def ping(self, interaction: discord.Interaction):
            await interaction.response.send_message("Pong!")

    Auteur : Serge
    """
    def wrapper(func):
        # Crée la commande comme d’habitude
        cmd = app_commands.command()(func)

        # Injecte l’attribut _dev_guild utilisé par BaseSlashCog
        cmd._dev_guild = Object(id=DEV_GUILD_ID)
        return cmd
    return wrapper
