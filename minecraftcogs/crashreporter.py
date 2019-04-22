from discord.ext import commands
import logging
import asyncio
from discord import File
from utils.discoutils import permission_node, sendmarkdown, promptconfirm
from .utils.mcservutils import getcrashreport, parsereport, formatreport

log = logging.getLogger('charfred')


class CrashReporter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.servercfg = bot.servercfg

    @commands.command(aliases=['report', 'crashreports'])
    @permission_node(f'{__name__}.report')
    async def crashreport(self, ctx, server: str, nthlast: int=0):
        """Retrieves the last crashreport for the given server.

        Takes a servername and an optional relative age parameter,
        0 for the newest report, 1 for the one before, etc.
        """
        if server not in self.servercfg['servers']:
            await sendmarkdown(ctx, f'< I have no knowledge of {server}! >')
            return

        log.info(f'Getting report for {server}.')
        serverspath = self.servercfg['serverspath']
        rpath, _ = await self.loop.run_in_executor(None, getcrashreport, server, serverspath, nthlast)

        b, _, timedout = await promptconfirm(ctx, 'Do you wish to download the full report?')
        if timedout:
            log.info('Crasreport prompt timed out!')
            return
        if b:
            log.info('Uploading crashreport to discord...')
            reportfile = File(rpath, filename=f'{server}-report.txt')
            await ctx.send(f'Crashreport for {server}: ', file=reportfile)
            return

        log.info('Parsing report...')
        ctime, desc, strace, flavor, level, block, phase = await self.loop.run_in_executor(
            None, parsereport, rpath
        )

        log.info('Formatting report...')
        chunks = await self.loop.run_in_executor(
            None, formatreport, rpath, ctime, desc, flavor, strace, level, block, phase
        )

        for c in chunks:
            await sendmarkdown(ctx, c)
            await asyncio.sleep(1, loop=self.loop)
        log.info('Report sent!')


def setup(bot):
    bot.register_nodes([f'{__name__}.report'])
    bot.add_cog(CrashReporter(bot))
