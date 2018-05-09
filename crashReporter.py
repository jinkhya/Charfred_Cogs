from discord.ext import commands
import os
import glob
import asyncio
import logging
from .utils.discoutils import has_permission, sendReply
# cfg no longer has serverspath, rebuild to use Config

log = logging.getLogger('charfred')


class crashReporter:
    def __init__(self, bot):
        self.bot = bot
        self.servercfg = bot.servercfg

    @commands.command(aliases=['report', 'crashreports'])
    @commands.guild_only()
    @has_permission('crashreport')
    async def crashreport(self, ctx, server: str, age: int=None):
        """Retrieves the last crashreport for the given server;
        Takes a relative age parameter, 0 for the newest report,
        1 for the one before, etc.
        """
        if server not in self.servercfg['servers']:
            await sendReply(ctx, f'I have no knowledge of {server}!')
            return
        if age is None:
            reportFile = sorted(
                glob.iglob(self.servercfg['serverspath'] + f'/{server}/crash-reports/*'),
                key=os.path.getmtime,
                reverse=True
            )[0]
        else:
            reportFile = sorted(
                glob.iglob(self.servercfg['serverspath'] + f'/{server}/crash-reports/*'),
                key=os.path.getmtime,
                reverse=True
            )[age]
        proc = await asyncio.create_subprocess_exec(
            'awk',
            '/^Time: /{e=1}/^-- Head/{e=1}/^-- Block/{e=1}/^-- Affected/{e=1}/^-- System/{e=0}/^A detailed/{e=0}{if(e==1){print}}',
            reportFile,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        log.info(f'Getting report for {server}.')
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            log.info(f'Report retrieved successfully.')
        else:
            log.warning('Failed to retrieve report!')
            return
        report = stdout.decode().strip()
        report = report.split('\n\n')
        for paragraph in report:
            await ctx.send(f'```{paragraph}```')
            await asyncio.sleep(1, loop=self.bot.loop)


def setup(bot):
    bot.add_cog(crashReporter(bot))


permissionNodes = ['crashreport']
