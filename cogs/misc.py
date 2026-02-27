"""Miscs cog."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord import Interaction  # noqa: F401
from discord.ext import commands

if TYPE_CHECKING:
    from discord.ext.commands import Context

logger = logging.getLogger(__name__)


class Misc(commands.Cog):
    """My first cog, for holding commands !"""

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.hybrid_command()
    async def ping(self, ctx: Context) -> None:
        """Ping the bot."""
        await ctx.send("Ping ! Pang ! Pong !")

    @commands.hybrid_command()
    @commands.has_any_role("modo", "Admin")
    async def sync(self, ctx: Context) -> None:
        """Sync the / commands on discord."""
        await ctx.defer()
        await ctx.send("Wait for it..")
        synced = await self.bot.tree.sync()
        await ctx.send("Sync OK")
        await ctx.send(f"✅ Sync OK ({len(synced)} commandes)")
        for cmd in self.bot.tree.get_commands():
            await ctx.send(f"Commande enregistrée: {cmd.name}")

    # @app_commands.command(name="sync_cleanup",
    #                       description="Purge et resynchronise toutes les commandes slash")
    @commands.hybrid_command(
        name="sync_cleanup",
        description="Purge et resynchronise toutes les commandes slash",
    )
    @commands.has_any_role("modo", "Admin")
    async def sync_cleanup(self, ctx: Context) -> None:
        await ctx.defer()
        try:
            # Supprime toutes les commandes locales
            # self.bot.tree.clear_commands(guild=ctx.guild)
            self.bot.tree.clear_commands(guild=None)
            synced = await self.bot.tree.sync()
            await ctx.send("✅ Commandes globales purgées et resynchronisées.", ephemeral=True)
            await ctx.send(f"✅ Sync OK ({len(synced)} commandes)")
            for cmd in self.bot.tree.get_commands():
                await ctx.send(f"Commande enregistrée: {cmd.name}")
        except Exception as e:
            await ctx.send(f"⚠️ Échec du nettoyage : {e}", ephemeral=True)

    @commands.command(name="sync_here")
    @commands.has_permissions(administrator=True)
    async def sync_here(self, ctx: Context) -> None:
        """Sync les commandes slash uniquement dans cette guild."""
        await ctx.defer()
        try:
            synced = await self.bot.tree.sync(guild=ctx.guild)
            await ctx.send(f"✅ Sync local OK — {len(synced)} commandes enregistrées ici.")
        except Exception as e:
            await ctx.send(f"❌ Échec du sync local : {e}")

    @commands.command(name="check_commands")
    @commands.has_permissions(administrator=True)
    async def check_commands(self, ctx: Context) -> None:
        """Affiche les commandes slash visibles dans cette guild."""
        await ctx.defer()

        guild_id = ctx.guild.id if ctx.guild else 0
        visible = await self.bot.tree.fetch_commands(guild=ctx.guild)
        global_cmds = await self.bot.tree.fetch_commands()

        def fmt(cmd):
            return f"- `{cmd.name}` ({cmd.description})"

        msg = f"📍 **Guild ID**: `{guild_id}`\n\n"
        msg += f"🔎 **Commandes visibles dans cette guild** ({len(visible)}):\n"
        msg += "\n".join(fmt(cmd) for cmd in visible) or "*(aucune)*"
        msg += f"\n\n🌍 **Commandes globales enregistrées** ({len(global_cmds)}):\n"
        msg += "\n".join(fmt(cmd) for cmd in global_cmds) or "*(aucune)*"

        await ctx.send(msg)

    @commands.hybrid_command()
    @commands.has_any_role("modo", "Admin")
    async def sing(self, ctx: Context) -> None:
        """Just sing."""
        await ctx.send("https://media.tenor.com/De6M1HsMZSEAAAAC/mariah-carey.gif")


async def setup(bot):
    await bot.add_cog(Misc(bot))
    logger.info("Misc cog added")
