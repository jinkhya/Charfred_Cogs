import logging
import discord
from random import randrange
from discord.ext import commands
from utils.config import Config
from utils.flipbooks import Flipbook
from utils.discoutils import permissionNode, send

log = logging.getLogger('charfred')


class Quotator:
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.quotes = Config(f'{bot.dir}/data/quotes.json',
                             load=True, loop=self.loop)

    async def on_reaction_add(self, reaction, user):
        if str(reaction.emoji) == '💾' and reaction.count == 1:
            if user.bot or reaction.message.author.bot:
                return

            if reaction.message.embeds:
                await reaction.message.add_reaction('🖕')
                return

            log.info('Saving a quote!')
            quotee = reaction.message.author
            quote = reaction.message.content
            id = str(quotee.id)

            if id not in self.quotes:
                self.quotes[id] = []

            self.quotes[id].append({'quote': quote,
                                    'savedBy': user.id})
            await self.quotes.save()
            await reaction.message.add_reaction('👌')

    @commands.group(invoke_without_command=True)
    @permissionNode('quote')
    async def quote(self, ctx, member: discord.Member=None, _index: int=None):
        """User Quote operations.

        Without a subcommand, this returns a list
        of all users that are registered in the
        quote repository.
        """

        if member and str(member.id) in self.quotes:
            id = str(member.id)
            if _index is None:
                log.info('Random quote!')
                _index = randrange(len(self.quotes[id]))
                q = self.quotes[id][_index]['quote']
            else:
                try:
                    log.info('Specific quote!')
                    q = self.quotes[id][_index]['quote']
                except (KeyError, IndexError):
                    log.info('No quote with that index!')
                    await send(ctx, 'Sorry sir, there is no quote under that number!')
                    return
            if member.nick:
                name = member.nick
            else:
                name = member.name
            await send(ctx, f'{q}\n\n_{name}; Quote #{_index}_')
        else:

            log.info('Break 1')
            converter = commands.MemberConverter()

            async def getName(id):
                log.info('Converting...')
                member = await converter.convert(ctx, id)
                if member.nick:
                    return member.nick
                else:
                    return member.name

            members = '\n'.join([await getName(id) for id in self.quotes.keys()])
            log.info('Break 2')
            await send(ctx, f'I have quotes from these members:\n ```\n{members}\n```')

    @quote.command(aliases=['delete', 'unquote'])
    async def remove(self, ctx, member: discord.Member, *, _index: int):
        """Remove a specific quote.

        Takes the user who was quoted, and
        the ID of the quote to be removed,
        which is shown at the bottom of each
        quote.

        Only the user who saved the quote,
        and the quoted user can do this.
        """

        if str(member.id) in self.quotes:
            id = str(member.id)
            log.info('Removing a quote!')
            try:
                if ctx.author.id == member.id or \
                        ctx.author.id == self.quotes[id][_index]['savedBy']:
                    del self.quotes[id][_index]
                    await send(ctx, 'We shall never speak of it again, sir!')
                    await self.quotes.save()
                else:
                    await send(ctx, 'I am sorry, sir, but you are neither the quotee, '
                               'nor the person who requested this quote to be saved.')
            except:
                log.info('Unknown quote, cannot remove!')
                await send(ctx, 'Sorry sir, I don\'t seem to have a record of this quote.')
        else:
            log.info('Unknown member!')
            await send(ctx, 'Sorry lass, I don\'t seem to have heard of this person before.')

    @quote.command(name='list')
    async def _list(self, ctx, member: discord.Member):
        """List all quotes from a specific user.

        Quotes are presented as a nice flipbook, for
        easy and non-spammy perusal!
        """

        if str(member.id) in self.quotes:
            id = str(member.id)
            log.info('Showing quotes!')

            quotelist = []
            for index, quotemeta in enumerate(self.quotes[id]):
                quote = quotemeta['quote']
                quotelist.append(f'#{index}: {quote:.50}')

            if member.nick:
                name = member.nick
            else:
                name = member.name
            quoteFlip = Flipbook(ctx, quotelist, entries_per_page=12,
                                 title=f'Shit {name} says!',
                                 color=discord.Color.blurple())
            await quoteFlip.flip()

        else:
            log.info('Unknown member!')
            await send(ctx, 'Sorry lass, I don\'t seem to have heard of this person before.')


def setup(bot):
    bot.add_cog(Quotator(bot))


permissionNodes = ['quote']
