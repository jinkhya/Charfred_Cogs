import logging
import os
import asyncio
from time import sleep, time
from threading import Event
from queue import Queue
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
    async def watch(self, ctx, server: str, timeout: int=120):
        """Continously reads from the log file of a given server.

        This will keep reading any new lines that are added to the
        log file of the given server for about two minutes, unless
        cancelled.
        """

        if server in self.logfutures and not self.logfutures[server][0].done():
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

        outqueue = Queue(maxsize=20)

        def _readlog(event, timeout):
            if timeout:
                stopwhen = time() + 120
            with open(self.servercfg['serverspath'] + f'/{server}/logs/latest.log', 'r') as mclog:
                log.info(f'LW: Reading log for {server}...')
                mclog.seek(0, 2)
                while not event.is_set():
                    if timeout and time() > stopwhen:
                        coro = sendMarkdown(ctx, '< Timeout reached! >')
                        asyncio.run_coroutine_threadsafe(coro, self.loop)
                        return
                    line = mclog.readline()
                    if line:
                        try:
                            outqueue.put(line)
                        except:
                            pass
                    else:
                        sleep(0.5)

        def _relaylog(event):
            lines = []
            while not event.is_set():
                log.info(f'LW: Relaying log for {server}...')
                while len(lines) < 5:
                    line = '# ' + outqueue.get()
                    lines.append(line)
                else:
                    out = '\n'.join(lines)
                    coro = sendMarkdown(ctx, out)
                    asyncio.run_coroutine_threadsafe(coro, self.loop)
            return

        def _watchDone(future):
            log.info(f'LW: Done reading log for {server}!')
            if future.exception():
                log.warning(f'LW: Exception in log reader for {server}!')
                log.warning(future.exception())
                coro = sendMarkdown(ctx, f'< An exception caused the log reader for {server}\n'
                                    'to terminate immaturely! >')
            else:
                coro = sendMarkdown(ctx, f'> Stopped reading log for {server}.')
            asyncio.run_coroutine_threadsafe(coro, self.loop)

        event = Event()
        await sendMarkdown(ctx, f'# Starting log reader for {server}...')
        logreaderfuture = self.loop.run_in_executor(None, _readlog, event, timeout)
        logrelayfuture = self.loop.run_in_executor(None, _relaylog, event)
        logreaderfuture.add_done_callback(_watchDone)
        self.logfutures[server] = ((logreaderfuture, logrelayfuture), event)

    @log.command(aliases=['unwatch', 'stopit', 'enough'])
    async def endwatch(self, ctx, server: str):
        """Stops the reader of a given server's log."""

        if server in self.logfutures and not self.logfutures[server][0][1].done():
            reader = self.logfutures[server]
            reader[1].set()
        else:
            if server not in self.servercfg['servers']:
                log.warning(f'{server} has been misspelled or not configured!')
                await sendMarkdown(ctx, f'< {server} has been misspelled or not configured! >')
            else:
                await sendMarkdown(ctx, f'# No currently active reader for {server}\'s log found.')


def setup(bot):
    if not hasattr(bot, 'servercfg'):
        bot.servercfg = Config(f'{bot.dir}/configs/serverCfgs.json',
                               default=f'{bot.dir}/configs/serverCfgs.json_default',
                               load=True, loop=bot.loop)
    bot.add_cog(LogReader(bot))


permissionNodes = ['logread']
