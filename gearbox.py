import logging
import traceback
from discord.ext import commands
from .utils.config import Config

log = logging.getLogger('charfred')


class gearbox:
    def __init__(self, bot):
        self.bot = bot
        self.dir = bot.dir
        self.loop = bot.loop
        self.cogfig = Config(f'{self.dir}/cogs/configs/cogCfg.json',
                             load=True, loop=self.loop)
        try:
            for cog in self.cogfig['cogs']:
                self._load(cog)
        except KeyError:
            log.info('No cog configurations exist. Initializing empty config.')
            self.cogfig['cogs'] = []

    def _load(self, cog):
        try:
            self.bot.load_extension(cog)
        except Exception as e:
            log.error(f'Could not load \"{cog}\"!')
            traceback.print_exc()
            return False
        else:
            log.info(f'\"{cog}\" loaded!')
            return True

    def _unload(self, cog):
        try:
            self.bot.unload_extension(cog)
        except Exception as e:
            log.error(f'Could not unload \"{cog}\"!')
            traceback.print_exc()
            return False
        else:
            log.info(f'\"{cog}\" unloaded!')
            return True

    def _reload(self, cog):
        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except Exception as e:
            log.error(f'Could not reload \"{cog}\"!')
            traceback.print_exc()
            return False
        else:
            log.info(f'\"{cog}\" reloaded!')
            return True

    @commands.group(hidden=True, aliases=['gear', 'extension', 'cogs'])
    @commands.is_owner()
    async def cog(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @cog.command(name='load')
    @commands.is_owner()
    async def loadcog(self, ctx, cogname: str):
        """Load a cog."""

        if self._load(cogname):
            await ctx.send(f'\"{cogname}\" loaded!')
        else:
            await ctx.send(f'Could not load \"{cogname}\"!\nMaybe you got the name wrong?')

    @cog.command(name='unload')
    @commands.is_owner()
    async def unloadcog(self, ctx, cogname: str):
        """Unload a cog."""

        if self._unload(cogname):
            await ctx.send(f'\"{cogname}\" unloaded!')
        else:
            await ctx.send(f'Could not unload \"{cogname}\"!')

    @cog.command(name='reload')
    @commands.is_owner()
    async def reloadcog(self, ctx, cogname: str):
        """Reload a cog."""

        if self._reload(cogname):
            await ctx.send(f'\"{cogname}\" reloaded!')
        else:
            await ctx.send(f'Could not reload \"{cogname}\"!')

    # NOTE: reinitiate is a one-off use, it'll unload gearbox,
    #       but won't be able to reload it, as at time of
    #       execution, all of gearbox's commands are still registered.
    @cog.command(name='reinitiate')
    @commands.is_owner()
    async def reinitiatecogs(self, ctx):
        """One-off reload of all cogs.

        Won\'t reload the gearbox, so this is a
        one-time per bot-uptime use! (workin on it)
        """

        for cog in list(self.bot.extensions):
            self._unload(cog)
        for cog in self.cogfig['cogs']:
            self._load(cog)

    @cog.command(name='add')
    @commands.is_owner()
    async def addcog(self, ctx, cogname: str):
        """Adds a cog to be loaded automatically in the future."""

        self.cogfig['cogs'].append(cogname)
        await self.cogfig.save()
        await ctx.send(f'\"{cogname}\" will now be loaded automatically.')

    @cog.command(name='remove')
    @commands.is_owner()
    async def removecog(self, ctx, cogname: str):
        """Removes a cog from being loaded automatically in the future."""

        self.cogfig['cogs'].remove(cogname)
        await self.cogfig.save()
        await ctx.send(f'\"{cogname}\" will no longer be loaded automatically.')

    @cog.command(name='list')
    @commands.is_owner()
    async def listcogs(self, ctx):
        """Lists all cogs to be loaded automatically."""

        cogList = ', '.join(self.cogfig['cogs'])
        await ctx.send(f'Cogs being loaded on startup: `{cogList}`')


def setup(bot):
    bot.add_cog(gearbox(bot))
