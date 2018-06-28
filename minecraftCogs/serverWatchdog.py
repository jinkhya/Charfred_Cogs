from discord.ext import commands
import asyncio
import logging
from time import strftime
from threading import Event
from utils.config import Config
from utils.discoutils import permissionNode, sendMarkdown
from .utils.mcservutils import isUp, getProc, serverStart

log = logging.getLogger('charfred')


class Watchdog:
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.servercfg = bot.servercfg
        self.watchdogs = {}

    def __unload(self):
        if self.watchdogs:
            for fut, event in self.watchdogs.values():
                event.set()

    @commands.group(invoke_without_command=True)
    @permissionNode('watchdog')
    async def watchdog(self, ctx):
        """Server process watchdog operations.

        Without a subcommand this returns a list of all
        active watchdogs.
        """

        for server, wd in self.watchdogs.items():
            if wd[0].done():
                await sendMarkdown(ctx, f'< {server} watchdog inactive! >')
            else:
                await sendMarkdown(ctx, f'# {server} watchdog active!')

    @watchdog.command(name='activate', aliases=['start', 'watch'])
    async def wdstart(self, ctx, server: str):
        """Start the process watchdog for a server."""

        if server in self.watchdogs and not self.watchdogs[server][0].done():
            log.info(f'{server} watchdog active.')
            await sendMarkdown(ctx, '# Watchdog already active!')
        else:
            if server not in self.servercfg['servers']:
                log.warning(f'{server} has been misspelled or not configured!')
                await sendMarkdown(ctx, f'< {server} has been misspelled or not configured! >')
                return

            if isUp(server):
                log.info(f'Starting watchdog on online server.')
                await sendMarkdown(ctx, f'# {server} is up and running.')
            else:
                log.info(f'Starting watchdog on offline server.')
                await sendMarkdown(ctx, f'< {server} is not running. >')

            async def serverGone():
                await sendMarkdown(ctx, '< ' + strftime("%H:%M") + f' {server} is gone! >\n'
                                   '> Watching for it to return...')

            async def serverBack():
                await sendMarkdown(ctx, '# ' + strftime("%H:%M") + f' {server} is back online!\n'
                                   '> Continuing watch!')

            async def watchGone():
                await sendMarkdown(ctx, f'> Ended watch on {server}!')

            async def startServer():
                startPrompt = await sendMarkdown(ctx, f'> If you wish to attempt starting {server},\n'
                                                 '> back up again, please react with ✅ to this message!')
                await startPrompt.add_reaction('✅')

                def startcheck(reaction, user):
                    if reaction.message.id != startPrompt.id:
                        return False

                    return str(reaction.emoji) == '✅' and not user.bot

                log.info(f'Prompting {server} start... 60 seconds.')
                try:
                    await self.bot.wait_for('reaction_add', timeout=60, check=startcheck)
                except asyncio.TimeoutError:
                    log.info('Prompt timed out.')
                    await startPrompt.clear_reactions()
                    await startPrompt.edit(content=f'```markdown\n> Prompt to start {server}'
                                           ' timed out!\n```')
                else:
                    await startPrompt.clear_reactions()
                    if isUp(server):
                        log.info(f'{server} is already back!')
                        await startPrompt.edit(content=f'```markdown\n> {server} is already back!\n```')
                    else:
                        log.info(f'Starting {server}')
                        await startPrompt.edit(content=f'```markdown\n> Starting {server}...\n```')
                        await serverStart(server, self.servercfg, self.loop)

            def watchDone(future):
                log.info(f'WD: Ending watch on {server}.')
                if future.exception():
                    log.warning(f'WD: Exception in watchdog for {server}!')
                asyncio.run_coroutine_threadsafe(watchGone(), self.loop)

            def watch(event):
                log.info(f'WD: Starting watch on {server}.')
                serverProc = getProc(server)
                if serverProc and serverProc.is_running():
                    lastState = True
                else:
                    lastState = False
                while not event.is_set():
                    if lastState:
                        if not serverProc.is_running():
                            log.info(f'WD: {server} is gone!')
                            lastState = False
                            asyncio.run_coroutine_threadsafe(serverGone(), self.loop)
                            asyncio.run_coroutine_threadsafe(startServer(), self.loop)
                        event.wait(timeout=20)
                    else:
                        serverProc = getProc(server)
                        if serverProc and serverProc.is_running():
                            log.info(f'WD: {server} is back online!')
                            lastState = True
                            asyncio.run_coroutine_threadsafe(serverBack(), self.loop)
                            event.wait(timeout=20)
                        else:
                            event.wait(timeout=60)
                else:
                    return

            event = Event()
            watchFuture = self.loop.run_in_executor(None, watch, event)
            watchFuture.add_done_callback(watchDone)
            self.watchdogs[server] = (watchFuture, event)
            await sendMarkdown(ctx, '# Watchdog activated!')

    @watchdog.command(name='deactivate', aliases=['stop', 'unwatch'])
    async def wdstop(self, ctx, server: str):
        """Stop the process watchdog for a server."""

        if server in self.watchdogs and not self.watchdogs[server][0].done():
            watcher = self.watchdogs[server]
            watcher[1].set()
            await sendMarkdown(ctx, f'> Terminating {server} watchdog...')
        else:
            if server not in self.servercfg['servers']:
                log.warning(f'{server} has been misspelled or not configured!')
                await sendMarkdown(ctx, f'< {server} has been misspelled or not configured! >')
            else:
                await sendMarkdown(ctx, '# Watchdog already inactive!')


def setup(bot):
    if not hasattr(bot, 'servercfg'):
        bot.servercfg = Config(f'{bot.dir}/configs/serverCfgs.json',
                               default=f'{bot.dir}/configs/serverCfgs.json_default',
                               load=True, loop=bot.loop)
    bot.add_cog(Watchdog(bot))


permissionNodes = ['watchdog']
