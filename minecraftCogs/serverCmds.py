from discord.ext import commands
import discord
import asyncio
import os
import re
import logging
import functools
from utils.config import Config
from utils.discoutils import permissionNode
from utils.flipbooks import EmbedFlipbook
from .utils.mcservutils import isUp, termProc, sendCmd, sendCmds

log = logging.getLogger('charfred')


class ServerCmds:
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.servercfg = bot.servercfg
        self.countpat = re.compile(
            '(?P<time>\d+)((?P<minutes>[m].*)|(?P<seconds>[s].*))', flags=re.I
        )

    @commands.group()
    @commands.guild_only()
    @permissionNode('status')
    async def server(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @server.command(aliases=['failsafe'])
    @permissionNode('start')
    async def start(self, ctx, server: str):
        """Start a server."""

        if server not in self.servercfg['servers']:
            log.warning(f'{server} has been misspelled or not configured!')
            await ctx.send(f'{server} has been misspelled or not configured!')
            return
        if isUp(server):
            log.info(f'{server} appears to be running already!')
            await ctx.send(f'{server} appears to be running already!')
        else:
            cwd = os.getcwd()
            log.info(f'Starting {server}')
            await ctx.send(f'Starting {server}.')
            os.chdir(self.servercfg['serverspath'] + f'/{server}')
            proc = await asyncio.create_subprocess_exec(
                'screen', '-h', '5000', '-dmS', server,
                *(self.servercfg['servers'][server]['invocation']).split(), 'nogui',
                loop=self.loop
            )
            await proc.wait()
            os.chdir(cwd)
            await asyncio.sleep(5, loop=self.loop)
            if isUp(server):
                log.info(f'{server} is now running!')
                await ctx.send(f'{server} is now running!')
            else:
                log.warning(f'{server} does not appear to have started!')
                await ctx.send(f'{server} does not appear to have started!')

    @server.command()
    @permissionNode('stop')
    async def stop(self, ctx, server: str):
        """Stop a server."""

        if server not in self.servercfg['servers']:
            log.warning(f'{server} has been misspelled or not configured!')
            await ctx.send(f'{server} has been misspelled or not configured!')
            return
        if isUp(server):
            log.info(f'Stopping {server}...')
            await ctx.send(f'Stopping {server}')
            await sendCmds(
                self.loop,
                server,
                'title @a times 20 40 20',
                'title @a title {\"text\":\"STOPPING SERVER NOW\", \"bold\":true, \"italic\":true}',
                'broadcast Stopping now!',
                'save-all',
            )
            await asyncio.sleep(5, loop=self.loop)
            await sendCmd(
                self.loop,
                server,
                'stop'
            )
            await asyncio.sleep(20, loop=self.loop)
            if isUp(server):
                log.warning(f'{server} does not appear to have stopped!')
                await ctx.send(f'{server} does not appear to have stopped!')
            else:
                log.info(f'{server} was stopped.')
                await ctx.send(f'{server} was stopped.')
        else:
            log.info(f'{server} already is not running.')
            await ctx.send(f'{server} already is not running.')

    @server.command()
    @permissionNode('restart')
    async def restart(self, ctx, server: str, countdown: str=None):
        """Restart a server with a countdown.

        Takes a servername and optionally the
        starting point for the countdown.
        Possible starting points are: 20m, 15m,
        10m, 5m, 3m, 2m, 1m, 30s, 10s, 5s.

        Additionally the issuer of this command
        may abort the countdown at any step.
        """

        if server not in self.servercfg['servers']:
            log.warning(f'{server} has been misspelled or not configured!')
            await ctx.send(f'{server} has been misspelled or not configured!')
            return
        if isUp(server):
            countdownSteps = ["20m", "15m", "10m", "5m", "3m",
                              "2m", "1m", "30s", "10s", "5s"]
            if countdown:
                if countdown not in countdownSteps:
                    log.error(f'{countdown} is an undefined step, aborting!')
                    await ctx.send(f'{countdown} is an undefined step, aborting!')
                    return
                log.info(f'Restarting {server} with {countdown}-countdown.')
                announcement = await ctx.send(f'Restarting {server} with {countdown}-countdown.')
                indx = countdownSteps.index(countdown)
                cntd = countdownSteps[indx:]
            else:
                log.info(f'Restarting {server} with default 10min countdown.')
                announcement = await ctx.send(f'Restarting {server} with default 10min countdown.')
                cntd = countdownSteps[2:]
            await asyncio.sleep(1, loop=self.loop)  # Tiny delay to allow message to be edited!
            steps = []
            for i, step in enumerate(cntd):
                s = self.countpat.search(step)
                if s.group('minutes'):
                    time = int(s.group('time'))
                    secs = time * 60
                    unit = 'minutes'
                else:
                    time = int(s.group('time'))
                    secs = time
                    unit = 'seconds'
                if i + 1 > len(cntd) - 1:
                    steps.append((time, secs, unit))
                else:
                    st = self.countpat.search(cntd[i + 1])
                    if st.group('minutes'):
                        t = int(st.group('time')) * 60
                    else:
                        t = int(st.group('time'))
                    steps.append((time, secs - t, unit))
            for step in steps:
                await sendCmds(
                    self.loop,
                    server,
                    'title @a times 20 40 20',
                    f'title @a subtitle {{\"text\":\"in {step[0]} {step[2]}!\",\"italic\":true}}',
                    'title @a title {\"text\":\"Restarting\", \"bold\":true}',
                    f'broadcast Restarting in {step[0]} {step[2]}!'
                )
                msg = f'Restarting {server} in {step[0]} {step[2]}!\nReact with ✋ to abort!'
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
                    await ctx.send(f'Restart of {server} aborted!')
                    return
                # await asyncio.sleep(step[1], loop=self.loop)
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
            await ctx.send(f'Stopping {server}.')
            await asyncio.sleep(30, loop=self.loop)
            if isUp(server):
                log.warning(f'Restart failed, {server} appears not to have stopped!')
                await ctx.send(f'Restart failed, {server} appears not to have stooped!')
            else:
                log.info(f'Restart in progress, {server} was stopped.')
                await ctx.send(f'Restart in progress, {server} was stopped.')
                cwd = os.getcwd()
                log.info(f'Starting {server}')
                await ctx.send(f'Starting {server}.')
                os.chdir(self.servercfg['serverspath'] + f'/{server}')
                proc = await asyncio.create_subprocess_exec(
                    'screen', '-h', '5000', '-dmS', server,
                    *(self.servercfg['servers'][server]['invocation']).split(), 'nogui',
                    loop=self.loop
                )
                await proc.wait()
                os.chdir(cwd)
                await asyncio.sleep(5, loop=self.loop)
                if isUp(server):
                    log.info(f'Restart successful, {server} is now running!')
                    await ctx.send(f'Restart successful, {server} is now running!')
                else:
                    log.warning(f'Restart failed, {server} does not appear to have started!')
                    await ctx.send(f'Restart failed, {server} does not appear to have started!')
        else:
            log.warning(f'Restart cancelled, {server} is offline!')
            await ctx.send(f'Restart cancelled, {server} is offline!')

    @server.command()
    @permissionNode('status')
    async def status(self, ctx, server: str):
        """Queries the status of a server."""

        if server not in self.servercfg['servers']:
            log.warning(f'{server} has been misspelled or not configured!')
            await ctx.send(f'{server} has been misspelled or not configured!')
            return
        if isUp(server):
            log.info(f'{server} is running.')
            await ctx.send(f'{server} is running.')
        else:
            log.info(f'{server} is not running.')
            await ctx.send(f'{server} is not running.')

    @server.command()
    @permissionNode('terminate')
    async def terminate(self, ctx, server: str):
        """Terminates a serverprocess forcefully."""

        if server not in self.servercfg['servers']:
            log.warning(f'{server} has been misspelled or not configured!')
            await ctx.send(f'{server} has been misspelled or not configured!')
            return
        log.info(f'Attempting termination of {server}...')
        if not isUp(server):
            log.info(f'{server} is not running!')
            await ctx.send(f'{server} is not running!')
            return
        await ctx.send(f'Attempting termination of {server}\n'
                       'Please hold, this may take a couple of seconds.')
        _termProc = functools.partial(termProc, server)
        killed = await self.loop.run_in_executor(None, _termProc)
        if killed:
            log.info(f'{server} terminated.')
            await ctx.send(f'{server} terminated.')
        else:
            log.info(f'Could not terminate {server}!')
            await ctx.send(f'Well this is awkward... {server} is still up!')

    @server.group()
    @permissionNode('management')
    async def config(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @config.command()
    async def add(self, ctx, server: str):
        """Interactively add a server configuration."""

        if server in self.servercfg['servers']:
            await ctx.send(f'{server} is already listed!')
            return

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        self.servercfg['servers'][server] = {}
        await ctx.send(f'Beginning configuration for {server}!'
                       '\nPlease enter the invocation for {server}:')
        r1 = await self.bot.wait_for('message', check=check, timeout=120)
        self.servercfg['servers'][server]['invocation'] = r1.content
        await ctx.send(f'Do you want to run backups on {server}? [y/n]')
        r2 = await self.bot.wait_for('message', check=check, timeout=120)
        if re.match('(y|yes)', r2.content, flags=re.I):
            self.servercfg['servers'][server]['backup'] = True
        else:
            self.servercfg['servers'][server]['backup'] = False
        await ctx.send(f'Please enter the name of the main world folder for {server}:')
        r3 = await self.bot.wait_for('message', check=check, timeout=120)
        self.servercfg['servers'][server]['worldname'] = r3.content
        await ctx.send(f'You have entered the following for {server}:\n' +
                       f'Invocation: {r1.content}\n' +
                       f'Backup: {r2.content}\n' +
                       f'Worldname: {r3.content}\n' +
                       'Please confirm! [y/n]')
        r4 = await self.bot.wait_for('message', check=check, timeout=120)
        if re.match('(y|yes)', r4.content, flags=re.I):
            await self.servercfg.save()
            await ctx.send(f'Serverconfigurations for {server} have been saved!')
        else:
            del self.servercfg['servers'][server]
            await ctx.send(f'Serverconfigurations for {server} have been discarded.')

    @config.command(name='list')
    async def _list(self, ctx, server: str):
        """Lists all configurations for a given server."""

        if server not in self.servercfg['servers']:
            await ctx.send(f'No configurations for {server} listed!')
            return
        await ctx.send(f'Configuration entries for {server}:\n')
        for k, v in self.servercfg['servers'][server].items():
            await ctx.send(f'{k}: {v}\n')

    def buildEmbeds(self):
        embeds = []
        for name, cfgs in self.servercfgs['servers'].items():
            embed = discord.Embed(color=discord.Color.dark_gold())
            embed.description = f'Configurations for {name}:'
            for k, v in cfgs.items():
                embed.add_field(name=k, value=f'``` {v}```', inline=False)
            embeds.append(embed)
        return embeds

    @config.command()
    async def listAll(self, ctx):
        """Lists all known server configurations,
        via Flipbook."""

        embeds = self.buildEmbeds()
        cfgFlip = EmbedFlipbook(ctx, embeds, entries_per_page=1,
                                title='Server Configurations')
        await cfgFlip.flip()

    @config.command()
    async def edit(self, ctx, server: str):
        """Interactively edit the configurations for a given server."""

        if server not in self.servercfg['servers']:
            await ctx.send(f'No configurations for {server} listed!')
            return

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        await ctx.send(f'Available options for {server}: ' +
                       ' '.join(self.servercfg['servers'][server].keys()))
        await ctx.send(f'Please enter the configuration option for {server}, that you want to edit:')
        r = await self.bot.wait_for('message', check=check, timeout=120)
        r = r.content.lower()
        if r not in self.servercfg['servers'][server]:
            await ctx.send(f'{r.content.lower()} is not a valid entry!')
            return
        await ctx.send(f'Please enter the new value for {r}:')
        r2 = await self.bot.wait_for('message', check=check, timeout=120)
        await ctx.send(f'You have entered the following for {server}:\n' +
                       f'{r}: {r2.content}\n' +
                       'Please confirm! [y/n]')
        r3 = await self.bot.wait_for('message', check=check, timeout=120)
        if re.match('(y|yes)', r3.content, flags=re.I):
            self.servercfg['servers'][server][r] = r2.content
            await self.servercfg.save()
            await ctx.send(f'Edit to {server} has been saved!')
        else:
            await ctx.send(f'Edit to {server} has been discarded!')

    @config.command()
    async def delete(self, ctx, server: str):
        """Delete the configuration of a given server."""

        if server not in self.servercfg['servers']:
            await ctx.send(f'Nothing to delete for {server}!')
            return

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        await ctx.send('You are about to delete all configuration options ' +
                       f'for {server}.\n' +
                       'Please confirm! [y/n]')
        r = await self.bot.wait_for('message', check=check, timeout=120)
        if re.match('(y|yes)', r.content, flags=re.I):
            del self.servercfg['servers'][server]
            await self.servercfg.save()
            await ctx.send(f'Configurations for {server} have been deleted!')
        else:
            await ctx.send(f'Deletion of configurations aborted!')

# TODO: Ability to change other settings in serverCfg.json, either here or charwizard


def setup(bot):
    if not hasattr(bot, 'servercfg'):
        bot.servercfg = Config(f'{bot.dir}/configs/serverCfgs.json',
                               default=f'{bot.dir}/configs/serverCfgs.json_default',
                               load=True, loop=bot.loop)
    bot.add_cog(ServerCmds(bot))


permissionNodes = ['start', 'stop', 'status', 'restart', 'terminate', 'management']
