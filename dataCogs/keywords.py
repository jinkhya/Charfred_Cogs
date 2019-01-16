import logging
import random
from discord.ext import commands
from utils.discoutils import permissionNode, promptConfirm, send

log = logging.getLogger('charfred')


class Keywords:
    def __init__(self, bot):
        self.bot = bot
        self.phrases = bot.keywords

    @commands.group(invoke_without_command=True)
    async def vocab(self, ctx):
        """Charfred vocabulary commands.

        Add and remove words or phrases from
        Charfred\'s vocabulary.
        This returns the list of all vocab categories,
        if no subcommand was given.
        """

        categories = '\n '.join(self.phrases.keys())
        await send(ctx, f'I know these categories:\n ```\n{categories}\n```')

    @vocab.command()
    @permissionNode('vocabAdd')
    async def add(self, ctx, category: str, *, phrase: str):
        """Add a new word or phrase to a category."""

        if category in self.phrases:
            log.info('Learning something!')
            self.phrases[category].append(phrase)
            await self.phrases.save()
            await send(ctx, phrase)
        else:
            log.info('Invalid category!')
            await send(ctx, 'I don\'t know that category!')

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
                await send(ctx, 'Can\'t forget this, because I never even knew that!')
            else:
                await self.phrases.save()
                await send(ctx, 'Oh man, I think I forgot something...')
        else:
            log.info('Invalid category!')
            await send(ctx, 'I don\'t know that category!')

    @vocab.group(invoke_without_command=True)
    @permissionNode('categoryAdd')
    async def category(self, ctx):
        """Vocab category commands."""

        pass

    @category.command(name='add')
    @permissionNode('categoryAdd')
    async def catAdd(self, ctx, category: str):
        """Add new vocab category."""

        if category in self.phrases:
            log.info('Category already exists!')
            await send(ctx, 'Category already exists!')
        else:
            log.info(f'Adding {category} as new category.')
            self.phrases[category] = []
            await self.phrases.save()
            await send(ctx, f'Added {category}!')

    @category.command(name='remove')
    @permissionNode('categoryRemove')
    async def catRemove(self, ctx, category: str):
        """Remove a whole vocab category.

        Be real careful with this!
        """
        if category in ['nacks', 'errormsgs', 'replies']:
            log.info('Tried to delete important categories!')
            await send(ctx, f'{category} cannot be deleted, '
                       'it is vital to my character!')
            return

        if category in self.phrases:
            r, _, _ = await promptConfirm(ctx, f'You are about to delete {category},'
                                          '\nare you certain? [y|N]')
            if r:
                del self.phrases[category]
                await self.phrases.save()
                log.info(f'{category} deleted!')
                await send(ctx, f'{category} deleted!')
        else:
            log.info(f'{category} doesn\'t exist!')
            await send(ctx, f'{category} doesn\'t exist!')

    @commands.command(aliases=['talktome', 'speak', 'recite'])
    async def talk(self, ctx, category: str=None):
        """Say a word or phrase from the vocabulary.

        With optional category argument.
        """
        if category is None:
            log.info('Random gibberish!')
            await send(ctx, f'{random.choice(random.choice(list(self.phrases.values())))}')
        elif category in self.phrases:
            log.info(f'Random gibberish from {category}!')
            await send(ctx, f'{random.choice(self.phrases[category])}')
        else:
            log.info('Invalid category!')
            await send(ctx, f'Category: {category} does not exist or has been misspelled!')


def setup(bot):
    bot.add_cog(Keywords(bot))


permissionNodes = ['vocabAdd', 'vocabRemove', 'categoryAdd', 'categoryRemove']
