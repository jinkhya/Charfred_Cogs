import logging
import random
from discord.ext import commands
from utils.discoutils import permissionNode, promptConfirm

log = logging.getLogger('charfred')


class Keywords:
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
            categories = '\n '.join(self.phrases.keys())
            await ctx.send(f'I know these categories:\n ```\n{categories}\n```')

    @vocab.command()
    @permissionNode('vocabAdd')
    async def add(self, ctx, category: str, *, phrase: str):
        """Add a new word or phrase to a category."""

        if category in self.phrases:
            log.info('Learning something!')
            self.phrases[category].append(phrase)
            await self.phrases.save()
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
            try:
                self.phrases[category].remove(phrase)
            except:
                log.info('Cannot remove, phrase unknown!')
                await ctx.send('Can\'t forget this, because I never even knew that!')
            else:
                await self.phrases.save()
                await ctx.send('Oh man, I think I forgot something...')
        else:
            log.info('Invalid category!')
            await ctx.send('I don\'t know that category!')

    @vocab.group()
    @permissionNode('categoryAdd')
    async def category(self, ctx):
        """Vocab category operations."""

        if ctx.invoked_subcommand is None:
            pass

    @category.command(name='add')
    @permissionNode('categoryAdd')
    async def catAdd(self, ctx, category: str):
        """Add new vocab category."""

        if category in self.phrases:
            log.info('Category already exists!')
            await ctx.send('Category already exists!')
        else:
            log.info(f'Adding {category} as new category.')
            self.phrases[category] = []
            await self.phrases.save()
            await ctx.send(f'Added {category}!')

    @category.command(name='remove')
    @permissionNode('categoryRemove')
    async def catRemove(self, ctx, category: str):
        """Remove a whole vocab category.

        Be real careful with this!
        """
        if category in ['nacks', 'errormsgs', 'replies']:
            log.info('Tried to delete important categories!')
            await ctx.send(f'{category} cannot be deleted, '
                           'it is vital to my character!')
            return

        if category in self.phrases:
            r, _ = await promptConfirm(ctx, f'You are about to delete {category},'
                                       '\nare you certain? [y|N]')
            if r:
                del self.phrases[category]
                await self.phrases.save()
                log.info(f'{category} deleted!')
                await ctx.send(f'{category} deleted!')
        else:
            log.info(f'{category} doesn\'t exist!')
            await ctx.send(f'{category} doesn\'t exist!')

    @commands.command(aliases=['talktome', 'speak', 'recite'])
    async def talk(self, ctx, category: str=None):
        """Say a word or phrase from the vocabulary.

        With optional category argument.
        """
        if category is None:
            log.info('Random gibberish!')
            await ctx.send(f'{random.choice(random.choice(list(self.phrases.values())))}')
        elif category in self.phrases:
            log.info(f'Random gibberish from {category}!')
            await ctx.send(f'{random.choice(self.phrases[category])}')
        else:
            log.info('Invalid category!')
            await ctx.send(f'Category: {category} does not exist or has been misspelled!')


def setup(bot):
    bot.add_cog(Keywords(bot))


permissionNodes = ['vocabAdd', 'vocabRemove', 'categoryAdd', 'categoryRemove']
