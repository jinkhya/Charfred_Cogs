import io
import textwrap
import traceback
import logging
from contextlib import redirect_stdout
from discord.ext import commands

log = logging.getLogger('charfred')


class evaluator:
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None

    @commands.command(hidden=True, aliases=['eval', 'pyeval', 'stupify'])
    @commands.is_owner()
    async def evaluate(self, ctx, *, body: str):
        """Eval some python code!

        Put it in a \'py\' highlighted codeblock.
        """

        if body.startswith('```py') and body.endswith('```'):
            body = '\n'.join(body.split('\n')[1:-1])
        else:
            await ctx.message.add_reaction('\N{THUMBS DOWN SIGN}')
            return await ctx.send('You forgot to use a py codeblock!')

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            log.info('Running exec...')
            exec(to_compile, env)
        except Exception as e:
            log.error('exec failed!')
            traceback.print_exc()
            await ctx.message.add_reaction('\N{THUMBS DOWN SIGN}')
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']

        try:
            with redirect_stdout(stdout):
                log.info('Running func()...')
                ret = await func()
        except Exception as e:
            log.error('func() failed!')
            traceback.print_exc()
            value = stdout.getvalue()
            await ctx.message.add_reaction('\N{THUMBS DOWN SIGN}')
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\N{HAND WITH INDEX AND MIDDLE FINGERS CROSSED}')
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')


def setup(bot):
    bot.add_cog(evaluator(bot))
