from discord.ext import commands
import discord
import re
import logging
from utils.config import Config
from utils.discoutils import permission_node, sendmarkdown, promptinput, promptconfirm, send
from utils.flipbooks import EmbedFlipbook

log = logging.getLogger('charfred')


class ServerConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.servercfg = bot.servercfg

    @commands.group(name='serverconfig', invoke_without_command=True)
    @permission_node(f'{__name__}.manage')
    async def config(self, ctx):
        """Minecraft server configuration commands."""

        pass

    @config.command()
    async def add(self, ctx, server: str):
        """Interactively add a server configuration."""

        if server in self.servercfg['servers']:
            await send(ctx, f'{server} is already listed!')
            return

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        self.servercfg['servers'][server] = {}
        await send(ctx, f'```Beginning configuration for {server}!'
                   f'\nPlease enter the invocation for {server}:```')
        r1 = await self.bot.wait_for('message', check=check, timeout=120)
        self.servercfg['servers'][server]['invocation'] = r1.content
        await send(ctx, f'```Do you want to run backups on {server}? [y/n]```')
        r2 = await self.bot.wait_for('message', check=check, timeout=120)
        if re.match('(y|yes)', r2.content, flags=re.I):
            self.servercfg['servers'][server]['backup'] = True
        else:
            self.servercfg['servers'][server]['backup'] = False
        await send(ctx, f'```Please enter the name of the main world folder for {server}:```')
        r3 = await self.bot.wait_for('message', check=check, timeout=120)
        self.servercfg['servers'][server]['worldname'] = r3.content
        await sendmarkdown(ctx, f'You have entered the following for {server}:\n' +
                           f'Invocation: {r1.content}\n' +
                           f'Backup: {r2.content}\n' +
                           f'Worldname: {r3.content}\n' +
                           '# Please confirm! [y/n]')
        r4 = await self.bot.wait_for('message', check=check, timeout=120)
        if re.match('(y|yes)', r4.content, flags=re.I):
            await self.servercfg.save()
            await sendmarkdown(ctx, f'# Serverconfigurations for {server} have been saved!')
        else:
            del self.servercfg['servers'][server]
            await sendmarkdown(ctx, f'< Serverconfigurations for {server} have been discarded. >')

    @config.command(name='list')
    async def _list(self, ctx, server: str):
        """Lists all configurations for a given server."""

        if server not in self.servercfg['servers']:
            await sendmarkdown(ctx, f'< No configurations for {server} listed! >')
            return
        await sendmarkdown(ctx, f'# Configuration entries for {server}:\n')
        for k, v in self.servercfg['servers'][server].items():
            await sendmarkdown(ctx, f'{k}: {v}\n')

    def buildEmbeds(self):
        embeds = []
        for name, cfgs in self.servercfg['servers'].items():
            embed = discord.Embed(color=discord.Color.dark_gold())
            embed.description = f'Configurations for {name}:'
            for k, v in cfgs.items():
                embed.add_field(name=k, value=f'``` {v}```', inline=False)
            embeds.append(embed)
        return embeds

    @config.command()
    async def flip(self, ctx):
        """Lists all known server configurations,
        via Flipbook."""

        embeds = await self.loop.run_in_executor(None, self.buildEmbeds)
        cfgFlip = EmbedFlipbook(ctx, embeds, entries_per_page=1,
                                title='Server Configurations')
        await cfgFlip.flip()

    @config.command()
    async def edit(self, ctx, server: str):
        """Interactively edit the configurations for a given server."""

        if server not in self.servercfg['servers']:
            await sendmarkdown(ctx, f'< No configurations for {server} listed! >')
            return

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        await sendmarkdown(ctx, f'Available options for {server}: ' +
                           ' '.join(self.servercfg['servers'][server].keys()))
        await sendmarkdown(ctx, f'# Please enter the configuration option for {server}, that you want to edit:')
        r = await self.bot.wait_for('message', check=check, timeout=120)
        r = r.content.lower()
        if r not in self.servercfg['servers'][server]:
            await sendmarkdown(ctx, f'< {r.content.lower()} is not a valid entry! >')
            return
        await sendmarkdown(ctx, f'Please enter the new value for {r}:')
        r2 = await self.bot.wait_for('message', check=check, timeout=120)
        await sendmarkdown(ctx, f'You have entered the following for {server}:\n' +
                           f'{r}: {r2.content}\n' +
                           '# Please confirm! [y/n]')
        r3 = await self.bot.wait_for('message', check=check, timeout=120)
        if re.match('(y|yes)', r3.content, flags=re.I):
            self.servercfg['servers'][server][r] = r2.content
            await self.servercfg.save()
            await sendmarkdown(ctx, f'# Edit to {server} has been saved!')
        else:
            await sendmarkdown(ctx, f'< Edit to {server} has been discarded! >')

    @config.command()
    async def delete(self, ctx, server: str):
        """Delete the configuration of a given server."""

        if server not in self.servercfg['servers']:
            await sendmarkdown(ctx, f'< Nothing to delete for {server}! >')
            return

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        await sendmarkdown(ctx, '< You are about to delete all configuration options ' +
                           f'for {server}. >\n' +
                           '# Please confirm! [y/n]')
        r = await self.bot.wait_for('message', check=check, timeout=120)
        if re.match('(y|yes)', r.content, flags=re.I):
            del self.servercfg['servers'][server]
            await self.servercfg.save()
            await sendmarkdown(ctx, f'# Configurations for {server} have been deleted!')
        else:
            await sendmarkdown(ctx, f'< Deletion of configurations aborted! >')

    @config.command()
    async def editpaths(self, ctx):
        """Give the option of editing the various server path configurations!"""

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        if 'serverspath' not in self.servercfg:
            self.servercfg['serverspath'] = 'NONE'
            await self.servercfg.save()
        await sendmarkdown(ctx, 'Current path for directory, where all minecraft servers'
                           'are located is:\n' + self.servercfg['serverspath'])
        r, _, timedout = await promptconfirm(ctx, 'Would you like to change this path?')
        if timedout:
            return
        if r:
            newpath, _, timedout = await promptinput(ctx, 'Please enter the new path now!\n'
                                                     '(it needs to be the full path)')
            if timedout:
                return
            if newpath:
                self.servercfg['serverspath'] = newpath
                await self.servercfg.save()
                await sendmarkdown(ctx, 'Saved new path for minecraft servers directory!')

        if 'backupspath' not in self.servercfg:
            self.servercfg['backupspath'] = 'NONE'
        await sendmarkdown(ctx, 'Current path for directory, where backups are saved is:\n' +
                           self.servercfg['backupspath'])
        r, _, timedout = await promptconfirm(ctx, 'Would you like to change this path?')
        if timedout:
            return
        if r:
            newpath, _, timedout = await promptinput(ctx, 'Please enter the new path now!\n'
                                                     '(it needs to be the full path)')
            if timedout:
                return
            if newpath:
                self.servercfg['backupspath'] = newpath
                await self.servercfg.save()
                await sendmarkdown(ctx, 'Saved new path for minecraft backups directory!')

    @config.command(aliases=['editbackuptimer'])
    async def editmaxbackupage(self, ctx):
        """Give the option of changing the maximum age for backups!

        Maximum age is defined in minutes.
        """

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        if 'oldTimer' not in self.servercfg:
            self.servercfg['oldTimer'] = 1440
            await self.servercfg.save()
        await sendmarkdown(ctx, 'Current maximum age for backups is:\n' +
                           self.servercfg['oldTimer'])
        r, _, timedout = await promptconfirm(ctx, 'Would you like to change it?')
        if timedout:
            return
        if r:
            newage, _, timedout = await promptinput(ctx, 'Please enter the new maximum backup age now!'
                                                    '\n(Age needs to be in minutes)')
            if timedout:
                return
            if newage:
                self.servercfg['oldTimer'] = newage
                await self.servercfg.save()
                await sendmarkdown(ctx, 'Saved new maximum backup age!')


def setup(bot):
    if not hasattr(bot, 'servercfg'):
        default = {
            "servers": {}, "serverspath": "NONE", "backupspath": "NONE", "oldTimer": 1440
        }
        bot.servercfg = Config(f'{bot.dir}/configs/serverCfgs.json',
                               default=default,
                               load=True, loop=bot.loop)
    bot.register_nodes([f'{__name__}.manage'])
    bot.add_cog(ServerConfig(bot))
