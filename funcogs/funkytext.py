import discord
import logging
import random
from functools import partial
from pyfiglet import Figlet
from discord.ext import commands
from utils.discoutils import send

log = logging.getLogger('charfred')

superscript = [
    "\u030d", "\u030e", "\u0304", "\u0305", "\u033f",
    "\u0311", "\u0306", "\u0310", "\u0352", "\u0357",
    "\u0351", "\u0307", "\u0308", "\u030a", "\u0342",
    "\u0343", "\u0344", "\u034a", "\u034b", "\u034c",
    "\u0303", "\u0302", "\u030c", "\u0350", "\u0300",
    "\u030b", "\u030f", "\u0312", "\u0313", "\u0314",
    "\u033d", "\u0309", "\u0363", "\u0364", "\u0365",
    "\u0366", "\u0367", "\u0368", "\u0369", "\u036a",
    "\u036b", "\u036c", "\u036d", "\u036e", "\u036f",
    "\u033e", "\u035b", "\u0346", "\u031a"
]

middlescript = [
    "\u0315", "\u031b", "\u0340", "\u0341", "\u0358",
    "\u0321", "\u0322", "\u0327", "\u0328", "\u0334",
    "\u0335", "\u0336", "\u034f", "\u035c", "\u035d",
    "\u035e", "\u035f", "\u0360", "\u0362", "\u0338",
    "\u0337", "\u0361", "\u0489"
]

subscript = [
    "\u0316", "\u0317", "\u0318", "\u0319", "\u031c",
    "\u031d", "\u031e", "\u031f", "\u0320", "\u0324",
    "\u0325", "\u0326", "\u0329", "\u032a", "\u032b",
    "\u032c", "\u032d", "\u032e", "\u032f", "\u0330",
    "\u0331", "\u0332", "\u0333", "\u0339", "\u033a",
    "\u033b", "\u033c", "\u0345", "\u0347", "\u0348",
    "\u0349", "\u034d", "\u034e", "\u0353", "\u0354",
    "\u0355", "\u0356", "\u0359", "\u035a", "\u0323"
]

zalgoScripts = [superscript, middlescript, subscript]


class FunkyText(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop

    def _zalgofy(self, amount, text):
        if amount < 0:
            text = text[:abs(amount)]
        elif amount == 0:
            text = text[:1]
            amount = 10

        if not text:
            text = 'HE SEES!'

        nonspaceindeces = [i for i, c in enumerate(text) if not c.isspace()]
        zalgoindeces = random.sample(nonspaceindeces, amount)
        text = list(text)

        for i in zalgoindeces:
            text[i] = f'{random.choice(random.choice(zalgoScripts))}{text[i]}'

        text = ''.join(text)
        return text

    @commands.command()
    async def zalgo(self, ctx, amount, *, text: str):
        """Zalgofy some text.

        Takes a number for the amount and some text.
        Optionally you can enter 'nickname' instead of
        an amount, to get a (hopefully) 32-character-limit
        friendly result.
        """

        if amount == 'nickname':
            z = partial(self._zalgofy, (32 - len(text)), text)
        elif int(amount) > 8:
            z = partial(self._zalgofy, 3, 'HE DISAPPROVES!')
        else:
            z = partial(self._zalgofy, int(amount), text)

        msg = await self.loop.run_in_executor(None, z)

        try:
            log.info('HE APPROVES!')
            await ctx.message.delete()
        except discord.Forbidden:
            log.warning('Couldn\'t delete msg!')
            pass
        finally:
            await send(ctx, msg)

    @commands.command()
    async def figlet(self, ctx, fnt: str, *, text: str):
        """Apply a figlet font to some text.

        Takes a fontname and some text.
        """

        try:
            log.info('Figyfy!')
            fig = Figlet(font=fnt)
        except:
            log.warning('Couldn\'t find font!')
            await send(ctx, f'Sorry, but {fnt} isn\'t known to pyfiglet!')
            await send(ctx, 'Please see http://www.figlet.org/fontdb.cgi\n'
                       'for a list of all available fonts, with examples!')
        else:
            figText = fig.renderText(text)

            try:
                await ctx.message.delete()
            except discord.Forbidden:
                log.warning('Couldn\'t delete msg!')
                pass
            finally:
                await send(ctx, f'```\n{figText}\n```')


def setup(bot):
    bot.add_cog(FunkyText(bot))
