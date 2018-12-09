from discord.ext import commands
from discord import Color
import asyncio
import logging
import os
from time import time
from utils.config import Config
from utils.flipbooks import Flipbook
from utils.discoutils import permissionNode, sendMarkdown, promptInput, promptConfirm
from .utils.mcservutils import isUp

log = logging.getLogger('charfred')


class ServerBackups:
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.servercfg = bot.servercfg

    @commands.group()
    @commands.guild_only()
    @permissionNode('backup')
    async def backup(self, ctx):
        """Minecraft server backup operations."""
        if ctx.invoked_subcommand is None:
            pass

    @backup.command(aliases=['listAll'])
    async def list(self, ctx, server: str):
        """List available backups for a specified server."""

        if server not in self.servercfg['servers']:
            log.warning(f'{server} has been misspelled or not configured!')
            await sendMarkdown(ctx, f'< {server} has been misspelled or not configured! >')
            return
        bpath = self.servercfg['backupspath']
        availablebackups = [archive for archive in os.listdir(f'{bpath}/{server}')
                            if os.path.isfile(f'{bpath}/{server}/{archive}') and
                            archive.endswith('.tar.gz')]
        backupsbook = Flipbook(ctx, availablebackups.sort(), entries_per_page=8,
                               title=f'Backups for {server}', color=Color.blurple())
        await backupsbook.flip()


def setup(bot):
    if not hasattr(bot, 'servercfg'):
        bot.servercfg = Config(f'{bot.dir}/configs/serverCfgs.json',
                               default=f'{bot.dir}/configs/serverCfgs.json_default',
                               load=True, loop=bot.loop)
    bot.add_cog(ServerBackups(bot))


permissionNodes = ['backup']
