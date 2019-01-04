import logging
from discord.ext import commands

log = logging.getLogger('charfred')


class Herald:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def heraldry(self, ctx):
        pass
