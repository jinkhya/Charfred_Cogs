import logging
import asyncio
from discord.ext import commands
from utils.discoutils import permissionNode, send

log = logging.getLogger('charfred')


class Jokes(commands.Cog):
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
            await send(ctx, f"{joke['setup']}")
            await asyncio.sleep(5)
            await send(ctx, f"{joke['punchline']}")

    @commands.command()
    @commands.cooldown(20, 60)
    @permissionNode('joke')
    async def dadjoke(self, ctx):
        """Get a random dad-style joke.

        Uses the icanhazdadjoke.com api, go check it out!
        """
        log.info('Retrieving dadjoke.')
        ua = self.bot.cfg['nodes']['spec:joke'][0]
        log.info(f'User-Agent header: {ua}')
        headers = {'Accept': 'application/json',
                   'User-Agent': ua}
        async with self.session.get('https://icanhazdadjoke.com/', headers=headers) as r:
            dadjoke = await r.json()
            await send(ctx, f"{dadjoke['joke']}")


def setup(bot):
    bot.add_cog(Jokes(bot))


permissionNodes = {
    'joke': '',
    'spec:joke': ['Please enter an email or url, that can be used for the User-Agent'
                  ' header for the icanhazdadjoke api\n', 'Charfred']
}
