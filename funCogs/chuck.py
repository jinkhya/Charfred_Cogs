import logging
from discord.ext import commands
from utils.discoutils import permissionNode

log = logging.getLogger('charfred')


class chuck:
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session

    @commands.group(invoke_without_command=True, aliases=['chuck', 'roundhouse'])
    @commands.cooldown(60, 60)
    @permissionNode('chuck')
    async def norris(self, ctx):
        """Interactions with ChuckNorrisJokes API.

        Without a subcommand, this gets a random joke.
        """

        if ctx.invoked_subcommand is None:
            log.info('Getting random chuck joke.')
            async with self.session.get('https://api.chucknorris.io/jokes/random') as r:
                joke = await r.json()['value']
                await ctx.send(f'`{joke}`')

    @norris.command()
    async def category(self, ctx, category: str=None):
        """Get a random joke from a category!

        If no category is given, this will return
        the list of all categories.
        """

        if category is None:
            log.info('Retrieving categories.')
            async with self.session.get('https://api.chucknorris.io/jokes/categories') as r:
                cats = await r.json()
                cats = ', '.join(cats)
                await ctx.send(f'Available categories: `{cats}`')
        else:
            log.info(f'Trying for a random joke from {category}.')
            async with self.session.get(f'https://api.chucknorris.io/jokes/random?category={category}') as r:
                joke = await r.json()['value']
                await ctx.send(f'`{joke}`')


def setup(bot):
    bot.add_cog(chuck(bot))


permissionNodes = ['chuck']
