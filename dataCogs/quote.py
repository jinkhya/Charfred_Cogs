import logging
import random
from discord.ext import commands
from utils.config import Config

log = logging.getLogger('charfred')


class Quotator:
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.quotes = Config(f'{bot.dir}/configs/quotes.json',
                             load=True, loop=self.loop)

    async def on_reaction_add(self, reaction, user):
        if str(reaction.emoji) == '💾' and reaction.count == 1:
            if user.bot or reaction.message.author.bot:
                return

            log.info('Saving a quote!')
            quotee = reaction.message.author
            quote = reaction.message.content

            if quotee.name not in self.quotes:
                self.quotes[quotee.name] = {}
            elif quote in self.quotes[quotee.name]:
                await reaction.message.add_reaction('\N{CROSS MARK}')
                return

            self.quotes[quotee.name][quote] = {'quotee': quotee.id,
                                               'savedBy': user.id}
            await reaction.message.add_reaction('\N{HEAVY CHECK MARK}')
            await self.quotes.save()

    @commands.group(invoke_without_command=True)
    async def quote(self, ctx, user: str=None):
        """User Quote operations.

        Without a subcommand, this returns a list
        of all users that are registered in the
        quote repository.
        """

        if user and user in self.quotes:
            log.info('Random quote!')
            q = random.choice(list(self.quotes[user].keys()))
            await ctx.send(f'{user}: {q}')
        else:
            users = '\n '.join(self.quotes.keys())
            await ctx.send(f'I have quotes from these users:\n ```\n{users}\n```')

    @quote.command(aliases=['delete', 'unquote'])
    async def remove(self, ctx, user: str, *, _quote: str):
        """Remove a specific quote.

        Takes the user who was quoted, and
        the exact quote to be removed.

        Only the user who saved the quote,
        and the quoted user can do this.
        """

        if user in self.quotes:
            log.info('Removing a quote!')
            try:
                if ctx.author.id == self.quotes[user][_quote]['quotee'] or \
                        ctx.author.id == self.quotes[user][_quote]['savedBy']:
                    del self.quotes[user][_quote]
                    await ctx.send('We shall never speak of it again, sir!')
                    await self.quotes.save()
                else:
                    await ctx.send('I am sorry, sir, but you are neither the quotee, '
                                   'nor the person who requested this quote to be saved.')
            except:
                log.info('Unknown quote, cannot remove!')
                await ctx.send('Sorry sir, I don\'t seem to have a record of this quote.')


def setup(bot):
    bot.add_cog(Quotator(bot))
