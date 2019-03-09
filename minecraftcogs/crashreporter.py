from discord.ext import commands
import os
import logging
from utils.discoutils import permission_node, sendMarkdown
from .utils.mcservutils import getcrashreport, parsereport

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
            await sendMarkdown(ctx, f'< I have no knowledge of {server}! >')
            return

        log.info(f'Getting report for {server}.')
        serverspath = self.servercfg['serverspath']
        rpath, _ = await self.loop.run_in_executor(None, getcrashreport, server, serverspath, nthlast)
        if rpath:
            log.info(f'Report found.')
        else:
            log.warning('No crashreports found!')
            return

        log.info('Parsing report...')
        sections = await self.loop.run_in_executor(None, parsereport, rpath)

        report = []
        report.append('> ' + os.path.basename(rpath) + '\n')
        report.append('# ' + sections['flavor'] + '\n')
        report.append('# ' + sections['time'])
        report.append('# ' + sections['desc'] + '\n')
        report.append('# Shortened Stacktrace:')
        report.extend(sections['trace'][:4])
        if 'level' in sections:
            report.append('\n# Affected level:')
            report.extend(sections['level'][1:])

        msg = '\n'.join(report)
        await sendMarkdown(ctx, msg)
        log.info('Report sent!')


def setup(bot):
    bot.register_nodes([f'{__name__}.report'])
    bot.add_cog(CrashReporter(bot))
