import logging
import re
from random import choice, randint
from discord.ext import commands

log = logging.getLogger('charfred')

predictions = {
    'good': [
        'Certainly!', 'Quite.', 'Most definitely.', 'I have it on good authority, yes!',
        'Indubitably!', 'Yeah, absolutely.', 'Sure.', 'The Council agrees!',
        'Yes, sir!', 'Yes, ma\'am!', 'You got it!', u'd(>_・ )'
    ],
    'neutral': [
        'I dunno, maybe?', 'Can\'t say for sure.', u'¯\_(ツ)_/¯', u'¯\_(⊙_ʖ⊙)_/¯',
        'Possibly?', 'Why don\'t you ask somebody else?', 'Poop', 'Uncertain!',
        'I can\'t even... why would you ask me that?', 'You really believe everything '
        'you hear, don\'t you?'
    ],
    'bad': [
        'Absolutely not!', 'Nay!', 'Nope!', 'I don\'t think so.',
        'Fuck you!', 'The Council denies!', 'I must disagree.', 'Narp!',
        'No, sir!', 'No, ma\'am, my apologies, ma\'am!'
    ]
}

notquestion = [
    'That\'s not a question.', 'What\'s the question?', 'Can you rephrase that as a question?',
    u'Why don\'t you try using one of these? ( ◑ω◑☞)☞ ?', 'I can only recognize questions with'
    ' a ? in it.'
]

dicepat = re.compile('^(?P<amount>\d*)[dD](?P<dice>4|6|8|10|12|20|120)$')


class Fate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['8ball'])
    async def eightball(self, ctx, *, question):
        """Ask the magic 8-Ball!

        Only yes or no questions please.
        """

        if '?' not in question:
            await ctx.send(choice(notquestion))
        else:
            await ctx.send(
                choice(predictions[choice(predictions.keys())])
            )

    @commands.command()
    async def roll(self, ctx, dice):
        """Roll some dice, let chaos decide!

        Specify which dice you wanna roll in classic
        tabletop RPG style, for example: 1d6, 2d8 or 4d20.
        I've got: d4, d6, d8, d10, d12, d20, and a single,
        rare and elusive d120.
        """

        m = dicepat.search(dice)
        if not m:
            await ctx.send('Please specify your dice in tabletop RPG style, '
                           'like 2d20, for a roll with 2 20 sided dice.')
            return

        amount = m.group('amount')
        dice = m.group('dice')

        if not dice:
            await ctx.send('Sorry, I don\'t have those dice.')
            return
        else:
            dice = int(dice)

        if not amount:
            amount = 1
        elif amount > 12:
            await ctx.send('Come on, be resonable, I only have 12 of each '
                           'of these!')
            return
        else:
            amount = int(amount)

        if dice == 120 and amount > 1:
            await ctx.send('I only have one of those, but here we go:' +
                           randint(1, 120))
        elif amount == 1:
            await ctx.send(f'*roll* ... {randint(1, dice)}')
        else:
            results = [dice] * amount
            await ctx.send('   '.join(map(lambda n: str(randint(1, n)), results)))


def setup(bot):
    bot.add_cog(Fate(bot))
