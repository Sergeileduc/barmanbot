#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Miscs cog."""

from discord.ext import commands


class Misc(commands.Cog):
    """My first cog, for holding commands !"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command()
    async def ping(self, ctx: commands.Context):
        "Ping the bot."
        await ctx.send("Ping ! Pang ! Pong !")
