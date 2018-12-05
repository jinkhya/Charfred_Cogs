from discord.ext import commands
import discord
import re
import logging
from utils.config import Config
from utils.discoutils import permissionNode, sendMarkdown, promptInput, promptConfirm
from utils.flipbooks import EmbedFlipbook

log = logging.getLogger('charfred')


class ServerConfig:
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.servercfg = bot.servercfg

    @commands.group(name='serverConfig')
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
        await ctx.send(f'```Beginning configuration for {server}!'
                       f'\nPlease enter the invocation for {server}:```')
        r1 = await self.bot.wait_for('message', check=check, timeout=120)
        self.servercfg['servers'][server]['invocation'] = r1.content
        await ctx.send(f'```Do you want to run backups on {server}? [y/n]```')
        r2 = await self.bot.wait_for('message', check=check, timeout=120)
        if re.match('(y|yes)', r2.content, flags=re.I):
            self.servercfg['servers'][server]['backup'] = True
        else:
            self.servercfg['servers'][server]['backup'] = False
        await ctx.send(f'```Please enter the name of the main world folder for {server}:```')
        r3 = await self.bot.wait_for('message', check=check, timeout=120)
        self.servercfg['servers'][server]['worldname'] = r3.content
        await sendMarkdown(ctx, f'You have entered the following for {server}:\n' +
                           f'Invocation: {r1.content}\n' +
                           f'Backup: {r2.content}\n' +
                           f'Worldname: {r3.content}\n' +
                           '# Please confirm! [y/n]')
        r4 = await self.bot.wait_for('message', check=check, timeout=120)
        if re.match('(y|yes)', r4.content, flags=re.I):
            await self.servercfg.save()
            await sendMarkdown(ctx, f'# Serverconfigurations for {server} have been saved!')
        else:
            del self.servercfg['servers'][server]
            await sendMarkdown(ctx, f'< Serverconfigurations for {server} have been discarded. >')

    @config.command(name='list')
    async def _list(self, ctx, server: str):
        """Lists all configurations for a given server."""

        if server not in self.servercfg['servers']:
            await sendMarkdown(ctx, f'< No configurations for {server} listed! >')
            return
        await sendMarkdown(ctx, f'# Configuration entries for {server}:\n')
        for k, v in self.servercfg['servers'][server].items():
            await sendMarkdown(ctx, f'{k}: {v}\n')

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
    async def listAll(self, ctx):
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
            await sendMarkdown(ctx, f'< No configurations for {server} listed! >')
            return

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        await sendMarkdown(ctx, f'Available options for {server}: ' +
                           ' '.join(self.servercfg['servers'][server].keys()))
        await sendMarkdown(ctx, f'# Please enter the configuration option for {server}, that you want to edit:')
        r = await self.bot.wait_for('message', check=check, timeout=120)
        r = r.content.lower()
        if r not in self.servercfg['servers'][server]:
            await sendMarkdown(ctx, f'< {r.content.lower()} is not a valid entry! >')
            return
        await sendMarkdown(ctx, f'Please enter the new value for {r}:')
        r2 = await self.bot.wait_for('message', check=check, timeout=120)
        await sendMarkdown(ctx, f'You have entered the following for {server}:\n' +
                           f'{r}: {r2.content}\n' +
                           '# Please confirm! [y/n]')
        r3 = await self.bot.wait_for('message', check=check, timeout=120)
        if re.match('(y|yes)', r3.content, flags=re.I):
            self.servercfg['servers'][server][r] = r2.content
            await self.servercfg.save()
            await sendMarkdown(ctx, f'# Edit to {server} has been saved!')
        else:
            await sendMarkdown(ctx, f'< Edit to {server} has been discarded! >')

    @config.command()
    async def delete(self, ctx, server: str):
        """Delete the configuration of a given server."""

        if server not in self.servercfg['servers']:
            await sendMarkdown(ctx, f'< Nothing to delete for {server}! >')
            return

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        await sendMarkdown(ctx, '< You are about to delete all configuration options ' +
                           f'for {server}. >\n' +
                           '# Please confirm! [y/n]')
        r = await self.bot.wait_for('message', check=check, timeout=120)
        if re.match('(y|yes)', r.content, flags=re.I):
            del self.servercfg['servers'][server]
            await self.servercfg.save()
            await sendMarkdown(ctx, f'# Configurations for {server} have been deleted!')
        else:
            await sendMarkdown(ctx, f'< Deletion of configurations aborted! >')

    @config.command()
    async def editPaths(self, ctx):
        """Give the option of editing the various server path configurations!"""

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        await sendMarkdown(ctx, 'Current path for directory, where all minecraft servers'
                           'are located is:\n' + self.servercfg['serverspath'])
        r, _, _ = await promptConfirm(ctx, 'Would you like to change this path?')
        if r:
            newpath, _, _ = await promptInput(ctx, 'Please enter the new path now!\n'
                                              '(it needs to be the full path)')
            if newpath:
                self.servercfg['serverspath'] = newpath
                await self.servercfg.save()

        await sendMarkdown(ctx, 'Current path for directory, where backups are saved is:\n'
                           + self.servercfg['backupspath'])
        r, _, _ = await promptConfirm(ctx, 'Would you like to change this path?')
        if r:
            newpath, _, _ = await promptInput(ctx, 'Please enter the new path now!\n'
                                              '(it needs to be the full path)')
            if newpath:
                self.servercfg['backupspath'] = newpath
                await self.servercfg.save()


def setup(bot):
    if not hasattr(bot, 'servercfg'):
        bot.servercfg = Config(f'{bot.dir}/configs/serverCfgs.json',
                               default=f'{bot.dir}/configs/serverCfgs.json_default',
                               load=True, loop=bot.loop)
    bot.add_cog(ServerConfig(bot))


permissionNodes = ['management']
