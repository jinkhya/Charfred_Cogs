import logging
import os
import asyncio
from time import sleep, time
from threading import Event
from discord.ext import commands
from utils.config import Config
from utils.discoutils import permission_node, sendmarkdown

log = logging.getLogger('charfred')


class LogReader(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.servercfg = bot.servercfg
        self.logfutures = {}

    @commands.group()
    @permission_node(f'{__name__}.read')
    async def log(self, ctx):
        """Minecraft log commands."""
        pass

    @log.command(aliases=['observe'])
    async def watch(self, ctx, server: str, timeout: int=180):
        """Continously reads from the log file of a given server for a little while.

        Takes a servername and an optional timeout argument,
        if no timeout is specified, it will default to 3 minutes,
        if timeout is set to either 0 or higher than 1800 seconds,
        it will default to 1800 seconds (30 minutes).
        """

        if server in self.logfutures and not self.logfutures[server][0].done():
            log.info(f'There\'s already a reader open for {server}\'s log!')
            await sendmarkdown(ctx, '# Reader already active!')
            return
        if server not in self.servercfg['servers']:
            log.warning(f'{server} has been misspelled or not configured!')
            await sendmarkdown(ctx, f'< {server} has been misspelled or not configured! >')
            return
        if not os.path.isfile(self.servercfg['serverspath'] + f'/{server}/logs/latest.log'):
            log.warning(f'Log for {server} not found!')
            await sendmarkdown(ctx, f'< Log file for {server} not found! >')
            return

        def _watchlog(event):
            timestamp = time()
            if timeout and timeout < 1800:
                stopwhen = timestamp + timeout
                coro = sendmarkdown(ctx, f'# Reading log for {server} for {timeout} seconds...\n'
                                    f'< Please run \'log endwatch {server}\' if you\'re\n'
                                    'not actively following the log! >')
            else:
                stopwhen = timestamp + 1800
                coro = sendmarkdown(ctx, f'# Reading log for {server} for 1800 seconds...\n'
                                    f'< Please run \'log endwatch {server}\' if you\'re\n'
                                    'not actively following the log! >')
            asyncio.run_coroutine_threadsafe(coro, self.loop)
            with open(self.servercfg['serverspath'] + f'/{server}/logs/latest.log', 'r') as mclog:
                log.info(f'LW: Reading log for {server} for {timeout} seconds...')
                mclog.seek(0, 2)
                outlines = []
                while not event.is_set() and time() < stopwhen:
                    line = mclog.readline()
                    if line and line.startswith('['):
                        outlines.append('# ' + line if len(line) < 225 else (line[:225] + ' [...]'))
                        if len(outlines) == 8 or (time() - timestamp) > 5:
                            out = '\n'.join(outlines)
                            coro = sendmarkdown(ctx, out)
                            asyncio.run_coroutine_threadsafe(coro, self.loop)
                            outlines = []
                            timestamp = time()
                            sleep(1)
                    else:
                        sleep(0.2)
                return

        def _watchDone(future):
            log.info(f'LW: Done reading log for {server}!')
            if future.exception():
                log.warning(f'LW: Exception in log reader for {server}!')
                log.warning(future.exception())
                coro = sendmarkdown(ctx, f'< An exception caused the log reader for {server}\n'
                                    'to terminate immaturely! >')
            else:
                coro = sendmarkdown(ctx, f'> Stopped reading log for {server}.')
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
            await sendmarkdown(ctx, f'> Stopped reading {server}\'s log!')
        else:
            if server not in self.servercfg['servers']:
                log.warning(f'{server} has been misspelled or not configured!')
                await sendmarkdown(ctx, f'< {server} has been misspelled or not configured! >')
            else:
                await sendmarkdown(ctx, f'# No currently active reader for {server}\'s log found.')


def setup(bot):
    if not hasattr(bot, 'servercfg'):
        default = {
            "servers": {}, "serverspath": "NONE", "backupspath": "NONE", "oldTimer": 1440
        }
        bot.servercfg = Config(f'{bot.dir}/configs/serverCfgs.json',
                               default=default,
                               load=True, loop=bot.loop)
    bot.register_nodes([f'{__name__}.read'])
    bot.add_cog(LogReader(bot))
