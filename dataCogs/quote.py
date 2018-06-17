import logging
import discord
from random import randrange
from discord.ext import commands
from utils.config import Config
from utils.discoutils import permissionNode, sendMarkdown

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

            if quotee.id not in self.quotes:
                self.quotes[quotee.id] = []

            self.quotes[quotee.id].append({'quote': quote,
                                           'savedBy': user.id})
            await self.quotes.save()
            await reaction.message.add_reaction('👌')

    @commands.group(invoke_without_command=True)
    @permissionNode('quote')
    async def quote(self, ctx, member=None, _index: int=None):
        """User Quote operations.

        Without a subcommand, this returns a list
        of all users that are registered in the
        quote repository.
        """

        if member:
            try:
                member = await commands.MemberConverter().convert(ctx, member)
            except commands.BadArgument:
                await sendMarkdown(ctx, 'Given member could not be resolved, sorry!')
                return
            if member.id in self.quotes:
                if _index is None:
                    log.info('Random quote!')
                    _index = randrange(len(self.quotes[member.id]))
                    q = self.quotes[member.id][_index]['quote']
                else:
                    try:
                        log.info('Specific quote!')
                        q = self.quotes[member.id][_index]['quote']
                    except (KeyError, IndexError):
                        log.info('No quote with that index!')
                        await ctx.send('Sorry sir, there is no quote under that number!')
                        return
                if member.nick:
                    name = member.nick
                else:
                    name = member.name
                await ctx.send(f'{q}\n\n_{name}; Quote #{_index}_')
                return

        converter = commands.MemberConverter()

        async def getName(id):
            member = await converter.convert(ctx, id)
            if member.nick:
                return member.nick
            else:
                return member.name

        members = '\n'.join([await getName(id) for id in self.quotes.keys()])
        await ctx.send(f'I have quotes from these members:\n ```\n{members}\n```')

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

        if member.id in self.quotes:
            log.info('Removing a quote!')
            try:
                if ctx.author.id == member.id or \
                        ctx.author.id == self.quotes[member.id][_index]['savedBy']:
                    del self.quotes[member.id][_index]
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


permissionNodes = ['quote']
