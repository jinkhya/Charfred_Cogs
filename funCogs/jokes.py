import logging
import asyncio
from discord.ext import commands
from utils.discoutils import permissionNode

log = logging.getLogger('charfred')


class Jokes:
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session

    @commands.command(aliases=['tellmeajoke', 'makemelaugh'])
    @commands.cooldown(60, 60)
    @permissionNode('joke')
    async def joke(self, ctx):
        """Get a random joke.

        Uses the official joke api!
        """

        log.info('Retrieving joke.')
        async with self.session.get('https://08ad1pao69.execute-api.us-east-1.amazonaws.com/dev/random_joke') as r:
            joke = await r.json()
            await ctx.send(f"`{joke['setup']}`")
            await asyncio.sleep(5)
            await ctx.send(f"`{joke['punchline']}`")


def setup(bot):
    bot.add_cog(Jokes(bot))


permissionNodes = ['joke']
