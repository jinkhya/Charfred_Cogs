from discord.ext import commands
from discord.utils import find
import asyncio
import logging
import re
from time import strftime, localtime
from threading import Event
from utils.config import Config
from utils.discoutils import permission_node, sendMarkdown, send
from .utils.mcservutils import isUp, getProc, serverStart

log = logging.getLogger('charfred')

cronpat = re.compile('^(?P<disabled>#)*((?P<reboot>@reboot)|(?P<min>(\*/\d+|\*|(\d+,?)+))\s(?P<hour>(\*/\d+|\*|(\d+,?)+))\s(?P<day>(\*/\d+|\*|(\d+,?)+)))\s.*spiffy\s(?P<cmd>\w+)\s(?P<server>\w+)\s(?P<args>.*)>>')
every = '*/'
always = '*'


class Watchdog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.servercfg = bot.servercfg
        self.watchdogs = {}
        self.watchcfg = Config(f'{bot.dir}/configs/watchcfg.json',
                               load=True, loop=self.loop)
        if 'crontab' not in self.watchcfg:
            self.watchcfg['crontab'] = {}
        if 'notify' not in self.watchcfg:
            self.watchcfg['notify'] = [True, 'default', '@here']

    def cog_unload(self):
        if self.watchdogs:
            for fut, event in self.watchdogs.values():
                event.set()

    @commands.group(invoke_without_command=True)
    @permission_node(f'{__name__}.watchdog')
    async def watchdog(self, ctx):
        """Server process watchdog commands.

        This returns a list of all active watchdogs,
        if no subcommand was given.
        """

        for server, wd in self.watchdogs.items():
            if wd[0].done():
                await sendMarkdown(ctx, f'< {server} watchdog inactive! >')
            else:
                await sendMarkdown(ctx, f'# {server} watchdog active!')

    def _parseCron(self, crontab):
        self.watchcfg['crontab'] = {}
        for l in crontab:
            if 'spiffy' not in l:
                continue
            if 'restart' not in l:
                continue
            if l.startswith('@') or l.startswith('#'):
                continue
            match = cronpat.match(l)
            if not match:
                continue
            _, _, min, hour, _, _, server, args = match.group('disabled',
                                                              'reboot',
                                                              'min', 'hour',
                                                              'day', 'cmd',
                                                              'server', 'args')
            if server not in self.watchcfg['crontab']:
                self.watchcfg['crontab'][server] = []
            self.watchcfg['crontab'][server].append((hour, min, args[:-2]))

    @watchdog.command(aliases=['readcron'])
    async def parsecron(self, ctx):
        """Parses current crontab for comparison with the watchdog."""

        log.info('Fetching current crontab...')
        proc = await asyncio.create_subprocess_exec(
            'crontab',
            '-l',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            log.info('Crontab retrieved successfully.')
        else:
            log.warning('Failed to retrieve crontab!')
            return
        crontab = stdout.decode().strip().split('\n')
        log.info('Parsing crontab...')
        self._parseCron(crontab)
        await sendMarkdown(ctx, '# Current crontab parsed!')
        await self.watchcfg.save()
        log.info('Watchdog cfg saved!')

    @watchdog.command(aliases=['shutup'])
    async def togglemention(self, ctx):
        """Toggles mention on crash notifications on and off."""

        log.info('Toggling crash mention.')
        if self.watchcfg['notify'][0]:
            self.watchcfg['notify'][0] = False
            self.watchcfg['notify'][1] = ctx.author.name
            await sendMarkdown(ctx, '< Crash mentioning has been disabled! >')
        else:
            self.watchcfg['notify'][0] = True
            self.watchcfg['notify'][1] = 'default'
            await sendMarkdown(ctx, '# Crash mentioning has been enabled!')
        await self.watchcfg.save()
        log.info('Watchdog cfg saved!')

    @watchdog.command(aliases=['blame'])
    async def setroletomention(self, ctx, mentionee: str):
        """Set who to mention for crash notification."""

        log.info(f'Setting role to mention to: {mentionee}.')

        role = find(lambda r: r.name == mentionee, ctx.guild.roles)
        if role:
            self.watchcfg['notify'][2] = role.mention
            await sendMarkdown(ctx, f'# Set role to mention to: {mentionee}!\n'
                               '> They will be notified if a crash is suspected,\n'
                               '> given that mentioning is enabled.')
            await self.watchcfg.save()
            log.info('Watchdog cfg saved!')
        else:
            await sendMarkdown(ctx, f'< {mentionee} is not a valid role! >')
            log.warning('Role could not be found, role to mention unchanged.')

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
                await sendMarkdown(ctx, f'# {server} is up and running.', deletable=False)
            else:
                log.info(f'Starting watchdog on offline server.')
                await sendMarkdown(ctx, f'< {server} is not running. >', deletable=False)

            if hasattr(self.bot, 'serverstopspending'):
                checkintent = True
            else:
                checkintent = False

            async def serverGone():
                now = localtime()
                await sendMarkdown(ctx, f'< {strftime("%H:%M", now)} : {server} is gone! >\n'
                                   '> Watching for it to return...', deletable=False)
                if checkintent and server in self.bot.serverstopspending:
                    await sendMarkdown(ctx, f'# A \'{self.bot.serverstopspending[server]}\''
                                       ' command was issued for {server} and is still pending!\n'
                                       '> No action required!')
                    return
                if server in self.watchcfg['crontab']:
                    # This whole checking thing really only works if your cron is sensible...
                    # Stuff it doesn't consider atm:
                    # - every n hours/min configurations
                    # - days/months
                    for hour, min, delay in self.watchcfg['crontab'][server]:
                        delay = int(delay)
                        min = int(min)
                        if (min + delay) > 60:
                            starthour = now.tm_hour - 1
                        else:
                            starthour = now.tm_hour
                        if f'{starthour}' in hour or hour == always:
                            if now.tm_min == ((min + delay) % 60):
                                await sendMarkdown(ctx, '> This looks like a scheduled restart.\n'
                                                   '> No action required!')
                                return
                    else:
                        if self.watchcfg['notify'][0]:
                            await send(ctx, f'{self.watchcfg["notify"][2]}\n```markdown\n<'
                                       ' This looks like an unscheduled crash. >'
                                       '\n< Someone might wanna investigate! >\n```')
                        else:
                            await sendMarkdown(ctx, '< This looks like an unscheduled crash! >\n'
                                               '< Role notification was'
                                               f' disabled by {self.watchcfg["notify"][1]}. >')

            async def serverBack():
                await sendMarkdown(ctx, '# ' + strftime("%H:%M") + f' {server} is back online!\n'
                                   '> Continuing watch!', deletable=False)

            async def watchGone():
                await sendMarkdown(ctx, f'> Ended watch on {server}!', deletable=False)

            async def startServer():
                startPrompt = await sendMarkdown(ctx, f'> If you wish to attempt starting {server},\n'
                                                 '> back up again, please react with ✅ to this message!',
                                                 deletable=False)
                await startPrompt.add_reaction('✅')

                def startcheck(reaction, user):
                    if reaction.message.id != startPrompt.id:
                        return False

                    return str(reaction.emoji) == '✅' and not user.bot

                log.info(f'Prompting {server} start... 120 seconds.')
                try:
                    await self.bot.wait_for('reaction_add', timeout=120, check=startcheck)
                except asyncio.TimeoutError:
                    log.info('Prompt timed out.')
                    await startPrompt.clear_reactions()
                    await startPrompt.edit(content=f'```markdown\n> Prompt to start {server}'
                                           ' timed out!\n```')
                    await asyncio.sleep(5, loop=self.loop)
                    await startPrompt.delete()
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
                            event.wait(timeout=40)
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
            await sendMarkdown(ctx, '# Watchdog activated!', deletable=False)

    @watchdog.command(name='deactivate', aliases=['stop', 'unwatch'])
    async def wdstop(self, ctx, server: str):
        """Stop the process watchdog for a server."""

        if server in self.watchdogs and not self.watchdogs[server][0].done():
            watcher = self.watchdogs[server]
            watcher[1].set()
            await sendMarkdown(ctx, f'> Terminating {server} watchdog...', deletable=False)
        else:
            if server not in self.servercfg['servers']:
                log.warning(f'{server} has been misspelled or not configured!')
                await sendMarkdown(ctx, f'< {server} has been misspelled or not configured! >')
            else:
                await sendMarkdown(ctx, '# Watchdog already inactive!', deletable=False)


def setup(bot):
    if not hasattr(bot, 'servercfg'):
        bot.servercfg = Config(f'{bot.dir}/configs/serverCfgs.json',
                               default=f'{bot.dir}/configs/serverCfgs.json_default',
                               load=True, loop=bot.loop)
    bot.register_nodes([f'{__name__}.watchdog'])
    bot.add_cog(Watchdog(bot))
