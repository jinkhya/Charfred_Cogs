from discord.ext import commands
import logging
from .utils.discoutils import has_permission

log = logging.getLogger('charfred')


class nbteditor:
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @has_permission('nbt')
    async def nbt(self, ctx):
        True


def setup(bot):
    bot.add_cog(nbteditor(bot))
