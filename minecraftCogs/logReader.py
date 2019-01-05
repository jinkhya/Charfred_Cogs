import logging
import os
import asyncio
from time import sleep, time
from threading import Event
from discord.ext import commands
from utils.config import Config
from utils.discoutils import permissionNode, sendMarkdown

log = logging.getLogger('charfred')


class LogReader:
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.servercfg = bot.servercfg
        self.logfutures = {}

    @commands.group()
    @commands.guild_only()
    @permissionNode('logread')
    async def log(self, ctx):
        """Minecraft log operations."""
        pass

    @log.command(aliases=['observe'])
    async def watch(self, ctx, server: str):
        """Continously reads from the log file of a given server.

        This will keep reading any new lines that are added to the
        log file of the given server for about a minute, unless
        cancelled.
        """

        if server in self.logfutures:
            log.info(f'There\'s already a reader open for {server}\'s log!')
            await sendMarkdown(ctx, '# Reader already active!')
            return
        if server not in self.servercfg['servers']:
            log.warning(f'{server} has been misspelled or not configured!')
            await sendMarkdown(ctx, f'< {server} has been misspelled or not configured! >')
            return
        if not os.path.isfile(self.servercfg['serverspath'] + f'/{server}/logs/latest.log'):
            log.warning(f'Log for {server} not found!')
            await sendMarkdown(ctx, f'< Log file for {server} not found! >')
            return

        def _watchlog(event):
            stopwhen = time() + 60
            with open(self.servercfg['serverspath'] + f'/{server}/logs/latest.log', 'r') as mclog:
                log.info(f'LW: Reading log for {server}...')
                mclog.seek(0, 2)
                while not event.is_set() and time() < stopwhen:
                    line = mclog.readline()
                    if line:
                        coro = sendMarkdown(ctx, '# ' + line, deletable=False)
                        asyncio.run_coroutine_threadsafe(coro, self.loop)
                    else:
                        sleep(0.5)
                else:
                    return

        def _watchDone(future):
            log.info(f'LW: Done reading log for {server}!')
            if future.exception():
                log.warning(f'LW: Exception in reader for {server}\'s log!')
                log.warning(future.exception())
            coro = sendMarkdown(ctx, f'> Stopped reading log for {server}.', deletable=False)
            asyncio.run_coroutine_threadsafe(coro, self.loop)

        event = Event()
        logfuture = self.loop.run_in_executor(None, _watchlog, event)
        logfuture.add_done_callback(_watchDone)
        self.logfutures[server] = (logfuture, event)

    @log.command(aliases=['unwatch', 'stopit', 'enough'])
    async def endwatch(self, ctx, server: str):
        """Stops the reader of a given server's log."""

        if server in self.logfutures and not self.logfutures[server][0].done():
            reader = self.logfutures[server]
            reader[1].set()
            await sendMarkdown(ctx, f'> Stopped reading {server}\'s log!', deletable=False)
        else:
            if server not in self.servercfg['servers']:
                log.warning(f'{server} has been misspelled or not configured!')
                await sendMarkdown(ctx, f'< {server} has been misspelled or not configured! >')
            else:
                await sendMarkdown(ctx, f'# No currently active reader for {server}\'s log found.',
                                   deletable=False)


def setup(bot):
    if not hasattr(bot, 'servercfg'):
        bot.servercfg = Config(f'{bot.dir}/configs/serverCfgs.json',
                               default=f'{bot.dir}/configs/serverCfgs.json_default',
                               load=True, loop=bot.loop)
    bot.add_cog(LogReader(bot))


permissionNodes = ['logread']
