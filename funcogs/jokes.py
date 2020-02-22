import logging
from discord.ext import commands

log = logging.getLogger('charfred')


class Jokes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session

    @commands.command()
    @commands.cooldown(20, 60)
    async def dadjoke(self, ctx):
        """Get a random dad-style joke.

        Uses the icanhazdadjoke.com api, go check it out!
        """
        log.info('Retrieving dadjoke.')
        ua = self.bot.cfg['cogcfgs'][f'{__name__}.jokeuser'][0]
        log.info(f'User-Agent header: {ua}')
        headers = {'Accept': 'application/json',
                   'User-Agent': ua}
        async with self.session.get('https://icanhazdadjoke.com/', headers=headers) as r:
            dadjoke = await r.json()
            await ctx.send(f"{dadjoke['joke']}")


def setup(bot):
    bot.register_cfg(f'{__name__}.jokeuser',
                     'Please enter an email or url, that can be used for the User-Agent'
                     ' header for the icanhazdadjoke api:\n',
                     'CharfredBot')
    bot.add_cog(Jokes(bot))
