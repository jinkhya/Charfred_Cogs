import logging
import random
from discord.ext import commands
from utils.discoutils import permissionNode

log = logging.getLogger('charfred')


class keywords:
    def __init__(self, bot):
        self.bot = bot
        self.phrases = bot.keywords

    @commands.group(invoke_without_command=True)
    async def vocab(self, ctx):
        """Charfred vocabulary operations.

        Add and remove words or phrases from
        Charfred\'s vocabulary.
        Without a subcommand, this returns the list
        of all vocab categories.
        """

        if ctx.invoked_subcommand is None:
            categories = '\n'.join(self.phrases.keys())
            await ctx.send(f'I know these categories:\n `{categories}`')

    @vocab.command()
    @permissionNode('vocabAdd')
    async def add(self, ctx, category: str, *, phrase: str):
        """Add a new word or phrase to a category."""

        if category in self.phrases:
            log.info('Learning something!')
            self.phrases[category].append(phrase)
            await ctx.send(phrase)
        else:
            log.info('Invalid category!')
            await ctx.send('I don\'t know that category!')

    @vocab.command()
    @permissionNode('vocabRemove')
    async def remove(self, ctx, category: str, *, phrase: str):
        """Remove a word or phrase from a category."""

        if category in self.phrases:
            log.info('Forgetting something!')
            self.phrases[category].remove(phrase)
            await ctx.send('Oh man, I think I forgot something...')
        else:
            log.info('Invalid category!')
            await ctx.send('I don\'t know that category!')

    @commands.command(aliases=['talktome', 'speak', 'whatsonyourmind'])
    async def talk(self, ctx, category: str=None):
        """Say a word or phrase from the vocabulary.

        With optional category argument.
        """
        if category is None:
            log.info('Random gibberish!')
            await ctx.send(f'{random.choice(random.choice(self.phrases.values()))}')
        else:
            log.info(f'Random gibberish from {category}!')
            await ctx.send(f'{random.choice(self.phrases[category])}')


def setup(bot):
    bot.add_cog(keywords(bot))


permissionNodes = ['vocabAdd', 'vocabRemove']
