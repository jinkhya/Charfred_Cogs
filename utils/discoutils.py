import discord
from discord.ext import commands
import random
import functools
from ..configs import keywords


def has_permission(cmd):
    def predicate(ctx):
        if ctx.channel.id == ctx.bot.cfg['defaultCmdCh'] or \
           ctx.channel.id in ctx.bot.cfg['nodes'][cmd]['channels']:
            names = ctx.bot.cfg['nodes'][cmd]['ranks']
            getter = functools.partial(discord.utils.get, ctx.author.roles)
            return any(getter(name=name) is not None for name in names)
        else:
            return False
    return commands.check(predicate)


async def sendReply(ctx, msg):
    await ctx.send(f'{random.choice(keywords.replies)}\n{msg}')


async def sendReply_codeblocked(ctx, msg, encoding=None):
    if encoding is None:
        mesg = f'\n```markdown\n{msg}\n```'
    else:
        mesg = f'\n```{encoding}\n{msg}\n```'
    await ctx.send(f'{random.choice(keywords.replies)}' + mesg)


async def sendEmbed(ctx, emb):
    await ctx.send(f'{random.choice(keywords.replies)}', embed=emb)
