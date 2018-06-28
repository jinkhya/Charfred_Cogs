import logging
import random
import asyncio
from discord.ext import commands

log = logging.getLogger('charfred')

dances = [
    [u"└|ﾟεﾟ|┐", u"┌|ﾟзﾟ|┘", u"└|ﾟεﾟ|┐", u"┌|ﾟзﾟ|┘", u"└|ﾟεﾟ|┐", u"┌|ﾟзﾟ|┘"],
    [u"└|∵┌|", u"|┐∵|┘", u"└|∵┌|", u"|┐∵|┘", u"└|∵┌|", u"|┐∵|┘"],
    [u"(o^^)o", u"o(^^o)", u"(o^^)o", u"o(^^o)", u"(o^^)o", u"o(^^o)"],
    [u"|o∵|o", u"o|∵o|", u"|o∵|o", u"o|∵o|", u"|o∵|o", u"o|∵o|"],
    [u"(ノ￣ー￣)ノ", u"(〜￣△￣)〜", u"(ノ￣ω￣)ノ", u"(ノ￣ー￣)ノ", u"(〜￣△￣)〜", u"(ノ￣ω￣)ノ"]
]

faces = [
    u"(´﹃｀)", u"(・ε・｀)", u"(ง •̀ω•́)ง✧", u"╭( ･ㅂ･)و", u"ಠ‿↼", u"d(-_^)", u"d(´･ω･`)",
    u"٩(^ᴗ^)۶", u"ಥ◡ಥ", u"⚈ ̫ ⚈", u"∠(^ー^)", u"(^-^)ゝ", u"(∩^o^)⊃━☆ﾟ.*･｡ﾟ", u"ლ(・ヮ・ლ)"
]

pleasures = [
    'My pleasure, sir!', 'My pleasure, ma\'am', 'You are very welcome, sir!',
    'You are very welcome, madam!', 'Of course, your highness!', 'Of course, your ladyship!',
    'M\'lord *tips tophat*', 'Indubitably!', 'Fuck you!', '...', ' '
]

loves = [
    u"•́ε•̀٥", u"˶⚈Ɛ⚈˵", u"(・ε・｀)", u"(~￣³￣)~", u".+(´^ω^`)+.", u"ﾟ*｡(･∀･)ﾟ*｡", u"",
    u"(∩^o^)⊃━☆゜.*", u"ಠ◡ಠ", u"ʢᵕᴗᵕʡ", u"(^￢^)", u"(º﹃º)", u"ಠ_ರೃ", u"d(´･ω･`)"
]

gn9s = [
    'Good night, sir!', 'Good night!', 'Nighty night!', 'Sweet dreams!',
    'Sleep well!', 'Don\'t let the bedbugs bite!', 'Pleasant dreams!',
    'Glorious dreams to you, too!'
]

shrugs = [
    u"┐(￣ヘ￣)┌", u"ლ（╹ε╹ლ）", u"ლ(ಠ益ಠ)ლ", u"¯\_(⊙_ʖ⊙)_/¯",
    u"¯\_(ツ)_/¯", u"┐(´ー｀)┌", u"乁༼☯‿☯✿༽ㄏ", u"╮(╯_╰)╭"
]

shocks = [
    u"(ʘᗩʘ’)", u"(ʘ言ʘ╬)", u"(◯Δ◯∥)", u"(●Ω●;)"
]

spins = [
    [u"(　・ω)", u"(　・)", u"(　)", u"(・　)", u"(ω・　)", u"(・ω・)"],
    [u"(´･ω･`)", u"( ´･ω･)", u"( 　´･ω)", u"( 　　)", u"( 　　)", u"(ω･´　)", u"(･ω･´)", u"(｀･ω･´)"],
    [u"(･▽･)", u"( ･▽)", u"(　･)", u"(　　)", u"(･　)", u"(▽･ )", u"(･▽･)"],
    [u"(･＿･)", u"( ･_)", u"(　･)", u"(　　)", u"(･　)", u"(_･ )", u"(･＿･)"],
    [u"(°o°)", u"(°o。)", u"(。o。)", u"(。o°)", u"(°o°)", u"(°o。)", u"(。o。)", u"(。o°)"]
]


class Entertain:
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop

    @commands.command(aliases=['partytime'])
    async def dance(self, ctx):
        dance = random.choice(dances)
        step = await ctx.send(dance[0])
        await asyncio.sleep(2, loop=self.loop)
        for move in dance[1:]:
            await step.edit(content=move)
            await asyncio.sleep(2, loop=self.loop)

    @commands.command(aliases=['youspinmerightroundbabyrightround'])
    async def spin(self, ctx):
        spin = random.choice(spins)
        step = await ctx.send(spin[0])
        await asyncio.sleep(2, loop=self.loop)
        for turn in spin[1:]:
            await step.edit(content=turn)
            await asyncio.sleep(2, loop=self.loop)

    @commands.command(aliases=['*shrug*'])
    async def shrug(self, ctx):
        await ctx.send(random.choice(shrugs))

    @commands.command(aliases=['jikes', 'oh dear'])
    async def shock(self, ctx):
        await ctx.send(random.choice(shocks))

    @commands.command(aliases=['flip', 'table'])
    async def tableflip(self, ctx):
        unflipped = await ctx.send(u"(ಠ_ಠ) ┳━┳")
        await asyncio.sleep(2, loop=self.loop)
        await unflipped.edit(content=u"(╯ಠ_ಠ)╯︵┻━┻")

    @commands.command(aliases=['thank'])
    async def thanks(self, ctx):
        await ctx.send(random.choice(pleasures) + ' ' +
                       random.choice(faces))

    @commands.command(aliases=['gn9', 'gn8', 'goodnight', 'nn'])
    async def gn(self, ctx):
        await ctx.send(random.choice(gn9s) + ' ' +
                       random.choice(loves))


def setup(bot):
    bot.add_cog(Entertain(bot))
