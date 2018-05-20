import logging
from discord.ext import commands

log = logging.getLogger('charfred')


class adminis:
    def __init__(self, bot):
        self.bot = bot
        self.botCfg = bot.cfg

    @commands.group(invoke_without_command=True)
    async def prefix(self, ctx):
        """Bot Prefix operations.

        Without a subcommand, this returns the list
        of all current prefixes.
        """
        if ctx.invoked_subcommand is None:
            prefixes = ' '.join(self.botCfg['prefixes'])
            await ctx.send(f'Current prefixes: `{prefixes}`')

    @prefix.command(hidden=True)
    @commands.is_owner()
    async def add(self, ctx, prefix: str):
        """Add a new prefix."""

        log.info(f'Adding a new prefix: {prefix}')
        self.botCfg['prefixes'].append(prefix)
        await self.botCfg.save()
        await ctx.send(f'{prefix} has been registered!')

    @prefix.command(hidden=True)
    @commands.is_owner()
    async def remove(self, ctx, prefix: str):
        """Remove a prefix."""

        log.info(f'Removing prefix: {prefix}')
        self.botCfg['prefixes'].remove(prefix)
        await self.botCfg.save()
        await ctx.send(f'{prefix} has been unregistered!')


def setup(bot):
    bot.add_cog(adminis(bot))
