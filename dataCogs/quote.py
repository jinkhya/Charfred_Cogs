import logging
from random import randrange
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

            if reaction.message.embeds:
                await reaction.message.add_reaction('\N{CROSS MARK}')
                return

            log.info('Saving a quote!')
            quotee = reaction.message.author
            quote = reaction.message.content

            if quotee.name not in self.quotes:
                self.quotes[quotee.name] = []

            self.quotes[quotee.name].append({'quote': quote,
                                             'quotee': quotee.id,
                                             'savedBy': user.id})
            await self.quotes.save()
            await reaction.message.add_reaction('\N{WHITE HEAVY CHECK MARK}')

    @commands.group(invoke_without_command=True)
    async def quote(self, ctx, user: str=None):
        """User Quote operations.

        Without a subcommand, this returns a list
        of all users that are registered in the
        quote repository.
        """

        if user and user in self.quotes:
            log.info('Random quote!')
            qIndex = randrange(len(self.quotes[user]))
            q = self.quotes[user][qIndex]['quote']
            await ctx.send(f'{q}\n\n_Quote #{qIndex}_')
        else:
            users = '\n '.join(self.quotes.keys())
            await ctx.send(f'I have quotes from these users:\n ```\n{users}\n```')

    @quote.command(aliases=['delete', 'unquote'])
    async def remove(self, ctx, user: str, *, _index: int):
        """Remove a specific quote.

        Takes the user who was quoted, and
        the ID of the quote to be removed,
        which is shown at the bottom of each
        quote.

        Only the user who saved the quote,
        and the quoted user can do this.
        """

        if user in self.quotes:
            log.info('Removing a quote!')
            try:
                if ctx.author.id == self.quotes[user][_index]['quotee'] or \
                        ctx.author.id == self.quotes[user][_index]['savedBy']:
                    del self.quotes[user][_index]
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
