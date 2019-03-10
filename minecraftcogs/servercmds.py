from discord.ext import commands
import asyncio
import logging
from utils.config import Config
from utils.discoutils import permission_node, sendMarkdown
from .utils.mcservutils import isUp, sendCmd, sendCmds, serverStart, \
    serverStop, serverTerminate, serverStatus, buildCountdownSteps

log = logging.getLogger('charfred')


class ServerCmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.servercfg = bot.servercfg

    @commands.group(invoke_without_command=True)
    @permission_node(f'{__name__}.status')
    async def server(self, ctx):
        """Minecraft server commands."""

        pass

    @server.command(aliases=['failsafe'])
    @permission_node(f'{__name__}.start')
    async def start(self, ctx, server: str):
        """Start a server."""

        if server not in self.servercfg['servers']:
            log.warning(f'{server} has been misspelled or not configured!')
            await sendMarkdown(ctx, f'< {server} has been misspelled or not configured! >')
            return
        if isUp(server):
            log.info(f'{server} appears to be running already!')
            await sendMarkdown(ctx, f'< {server} appears to be running already! >')
        else:
            log.info(f'Starting {server}')
            await sendMarkdown(ctx, f'> Starting {server}...')
            await serverStart(server, self.servercfg, self.loop)
            await asyncio.sleep(5, loop=self.loop)
            if isUp(server):
                log.info(f'{server} is now running!')
                await sendMarkdown(ctx, f'# {server} is now running!')
            else:
                log.warning(f'{server} does not appear to have started!')
                await sendMarkdown(ctx, f'< {server} does not appear to have started! >')

    @server.command()
    @permission_node(f'{__name__}.stop')
    async def stop(self, ctx, server: str):
        """Stop a server.

        If stop fails, prompts for forceful
        termination of server.
        """

        if server not in self.servercfg['servers']:
            log.warning(f'{server} has been misspelled or not configured!')
            await sendMarkdown(ctx, f'< {server} has been misspelled or not configured! >')
            return
        if isUp(server):
            log.info(f'Stopping {server}...')
            await sendMarkdown(ctx, f'> Stopping {server}...')
            await serverStop(server, self.loop)
            await asyncio.sleep(20, loop=self.loop)
            if isUp(server):
                log.warning(f'{server} does not appear to have stopped!')
                msg = await sendMarkdown(ctx, f'< {server} does not appear to have stopped! >'
                                         f'React with ❌ within 60 seconds to force stop {server}!',
                                         deletable=False)
                await msg.add_reaction('❌')

                def termcheck(reaction, user):
                    if reaction.message.id != msg.id:
                        return False

                    return str(reaction.emoji) == '❌' and user == ctx.author

                log.info(f'Awaiting confirm on {server} termination... 60 seconds.')
                try:
                    await self.bot.wait_for('reaction_add', timeout=60, check=termcheck)
                except asyncio.TimeoutError:
                    log.info('Termination cancelled!')
                    await msg.clear_reactions()
                    await msg.edit(content='```markdown\n< Stop incomplete,'
                                   'termination cancelled! >\n```')
                else:
                    log.info('Attempting termination...')
                    await msg.clear_reactions()
                    await msg.edit(content='```markdown\n> Attempting termination!\n'
                                   '> Please hold, this may take a couple of seconds.```')
                    killed = await serverTerminate(server, self.loop)
                    if killed:
                        log.info(f'{server} terminated.')
                        await msg.edit(content=f'```markdown\n# {server} terminated.\n'
                                       '< Please investigate why termination was necessary! >```')
                    else:
                        log.info(f'{server} termination failed!')
                        await msg.edit(content=f'```markdown\n< {server} termination failed! >\n')
            else:
                log.info(f'{server} was stopped.')
                await sendMarkdown(ctx, f'# {server} was stopped.')
        else:
            log.info(f'{server} already is not running.')
            await sendMarkdown(ctx, f'< {server} already is not running. >')

    @server.command()
    @permission_node(f'{__name__}.restart')
    async def restart(self, ctx, server: str, countdown: str=None):
        """Restart a server with a countdown.

        Takes a servername and optionally the
        starting point for the countdown.
        Possible starting points are: 20m, 15m,
        10m, 5m, 3m, 2m, 1m, 30s, 10s, 5s.

        Additionally the issuer of this command
        may abort the countdown at any step,
        and issue termination, if stop fails.
        """

        if server not in self.servercfg['servers']:
            log.warning(f'{server} has been misspelled or not configured!')
            await sendMarkdown(ctx, f'< {server} has been misspelled or not configured! >')
            return
        if isUp(server):
            countdownSteps = ["20m", "15m", "10m", "5m", "3m",
                              "2m", "1m", "30s", "10s", "5s"]
            if countdown:
                if countdown not in countdownSteps:
                    log.error(f'{countdown} is an undefined step, aborting!')
                    availableSteps1 = ', '.join(countdownSteps[:5])
                    availableSteps2 = ', '.join(countdownSteps[5:])
                    await sendMarkdown(ctx, f'< {countdown} is an undefined step, aborting! >\n'
                                       '> Available countdown steps are:\n'
                                       f'> {availableSteps1},\n'
                                       f'> {availableSteps2}')
                    return
                log.info(f'Restarting {server} with {countdown}-countdown.')
                announcement = await sendMarkdown(ctx, f'> Restarting {server} with {countdown}-countdown.')
                indx = countdownSteps.index(countdown)
                cntd = countdownSteps[indx:]
            else:
                log.info(f'Restarting {server} with default 10min countdown.')
                announcement = await sendMarkdown(ctx, f'> Restarting {server} with default 10min countdown.', deletable=False)
                cntd = countdownSteps[2:]
            await asyncio.sleep(1, loop=self.loop)  # Tiny delay to allow message to be edited!
            steps = buildCountdownSteps(cntd)
            for step in steps:
                await sendCmds(
                    self.loop,
                    server,
                    'title @a times 20 40 20',
                    f'title @a subtitle {{\"text\":\"in {step[0]} {step[2]}!\",\"italic\":true}}',
                    'title @a title {\"text\":\"Restarting\", \"bold\":true}',
                    f'broadcast Restarting in {step[0]} {step[2]}!'
                )
                msg = f'```markdown\nRestarting {server} in {step[0]} {step[2]}!\nReact with ✋ to abort!\n```'
                await announcement.edit(content=msg)

                def check(reaction, user):
                    if reaction.message.id != announcement.id:
                        return False

                    return str(reaction.emoji) == '✋' and user == ctx.author

                try:
                    await self.bot.wait_for('reaction_add', timeout=step[1], check=check)
                except asyncio.TimeoutError:
                    pass
                else:
                    await sendCmds(
                        self.loop,
                        server,
                        'title @a times 20 40 20',
                        'title @a title {\"text\":\"Restart aborted!\", \"bold\":true}',
                        'broadcast Restart aborted!'
                    )
                    await sendMarkdown(ctx, f'# Restart of {server} aborted!')
                    return
            await sendCmd(
                self.loop,
                server,
                'save-all'
            )
            await asyncio.sleep(5, loop=self.loop)
            await sendCmd(
                self.loop,
                server,
                'stop'
            )
            await announcement.edit(content=f'```markdown\n> Stopping {server}\n```.')
            await asyncio.sleep(30, loop=self.loop)
            if isUp(server):  # TODO: Fix all this terminating stuff
                log.warning(f'Restart failed, {server} appears not to have stopped!')

                def termcheck(reaction, user):
                    if reaction.message.id != announcement.id:
                        return False

                    return str(reaction.emoji) == '❌' and user == ctx.author

                msg = (f'```markdown\n< Restart failed, {server} appears not to have stopped! >\n'
                       f'React with ❌ within 60 seconds to force stop {server}!\n```')
                await announcement.edit(content=msg)
                await announcement.add_reaction('❌')

                log.info(f'Awaiting confirm on {server} termination... 60 seconds')
                try:
                    await self.bot.wait_for('reaction_add', timeout=60, check=termcheck)
                except asyncio.TimeoutError:
                    log.info('Termination cancelled!')
                    await announcement.clear_reactions()
                    await announcement.edit(content='```markdown\n< Restart incomplete,'
                                            'termination cancelled! >\n```')
                else:
                    log.info('Attempting termination...')
                    await announcement.clear_reactions()
                    await announcement.edit(content='```markdown\n> Attempting termination!\n'
                                            '> Please hold, this may take a couple of seconds.```')
                    killed = await serverTerminate(server, self.loop)
                    if killed:
                        log.info(f'{server} terminated.')
                        await announcement.edit(content=f'```markdown\n# {server} terminated.\n'
                                                '< Please investigate why termination was necessary >\n'
                                                f'< and start {server} manually afterwards! >```')
                    else:
                        log.info(f'{server} termination failed!')
                        await announcement.edit(content=f'```markdown\n< {server} termination failed! >\n')
            else:
                log.info(f'Restart in progress, {server} was stopped.')
                await sendMarkdown(ctx, f'# Restart in progress, {server} was stopped.')
                log.info(f'Starting {server}')
                await sendMarkdown(ctx, f'> Starting {server}.')
                await serverStart(server, self.servercfg, self.loop)
                await asyncio.sleep(5, loop=self.loop)
                if isUp(server):
                    log.info(f'Restart successful, {server} is now running!')
                    await sendMarkdown(ctx, f'# Restart successful, {server} is now running!')
                else:
                    log.warning(f'Restart failed, {server} does not appear to have started!')
                    await sendMarkdown(ctx, f'< Restart failed, {server} does not appear to have started! >')
        else:
            log.warning(f'Restart cancelled, {server} is offline!')
            await sendMarkdown(ctx, f'< Restart cancelled, {server} is offline! >')

    @server.command()
    @permission_node(f'{__name__}.status')
    async def status(self, ctx, server: str=None):
        """Queries the status of servers.

        Without a servername specified, this returns
        a list with the status of all registered servers.
        """
        if server is None:
            servers = self.servercfg['servers'].keys()
        elif server not in self.servercfg['servers']:
            log.warning(f'{server} has been misspelled or not configured!')
            await sendMarkdown(ctx, f'< {server} has been misspelled or not configured! >')
            return
        else:
            servers = [server]
        statuses = await serverStatus(servers, self.loop)
        await sendMarkdown(ctx, f'{statuses}')

    @server.command()
    @permission_node(f'{__name__}.terminate')
    async def terminate(self, ctx, server: str):
        """Terminates a serverprocess forcefully."""

        if server not in self.servercfg['servers']:
            log.warning(f'{server} has been misspelled or not configured!')
            await sendMarkdown(ctx, f'< {server} has been misspelled or not configured! >')
            return
        if not isUp(server):
            log.info(f'{server} is not running!')
            await sendMarkdown(ctx, f'< {server} is not running! >')
            return
        log.info(f'Attempting termination of {server}...')
        await sendMarkdown(ctx, f'> Attempting termination of {server}\n'
                           '> Please hold, this may take a couple of seconds.')
        killed = await serverTerminate(server, self.loop)
        if killed:
            log.info(f'{server} terminated.')
            await sendMarkdown(ctx, f'# {server} terminated.')
        else:
            log.info(f'Could not terminate {server}!')
            await sendMarkdown(ctx, f'< Well this is awkward... {server} is still up! >')


def setup(bot):
    if not hasattr(bot, 'servercfg'):
        bot.servercfg = Config(f'{bot.dir}/configs/serverCfgs.json',
                               default=f'{bot.dir}/configs/serverCfgs.json_default',
                               load=True, loop=bot.loop)
    permission_nodes = ['start', 'stop', 'status', 'restart', 'terminate']
    bot.register_nodes([f'{__name__}.{node}' for node in permission_nodes])
    bot.add_cog(ServerCmds(bot))
