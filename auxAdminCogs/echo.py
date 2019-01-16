from discord.ext import commands
import logging
from utils.config import Config
from utils.discoutils import sendMarkdown, send

log = logging.getLogger('charfred')


class Echo:
    def __init__(self, bot):
        self.bot = bot
        self.botCfg = bot.cfg

    @commands.group(invoke_without_command=True, hidden=True)
    @commands.is_owner()
    async def echo(self, ctx):
        """Echo commands.

        This shows which channels are registered to be echoed to,
        if no subcommand was given.
        """

        pass

    @echo.commands(aliases=['add'])
    async def register(self, ctx):
        """Registers a channel to the echoable list of channels.

        Takes
        """

        pass
