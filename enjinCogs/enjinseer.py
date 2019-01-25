import logging
import json
from collections import namedtuple
from discord import Forbidden
from discord.ext import commands
from utils.discoutils import send, sendMarkdown, promptInput
from .utils.enjinutils import login, verifysession, post

log = logging.getLogger('charfred')

Enjinlogin = namedtuple('Enjinlogin', 'email password url site_id')


class Enjinseer:
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session
        if not hasattr(bot, 'enjinsession'):
            bot.enjinsession = None
        self.enjinsession = bot.enjinsession
        if not hasattr(bot, 'enjinlogin'):
            bot.enjinlogin = None
        self.enjinlogin = bot.enjinlogin

    @commands.group(hidden=True)
    @commands.is_owner()
    async def enjin(self, ctx):
        """Enjin Management commands."""
        pass

    @enjin.command()
    @commands.is_owner()
    async def login(self, ctx, email: str=None, password: str=None,
                    url: str=None, site_id: str=None):
        """Enjin user login and session saving.

        Establishes a session to be used by other enjin related cogs.
        """

        log.info('Starting enjin login!')
        if self.enjinsession and self.enjinlogin:
            valid = await verifysession(self.enjinlogin)
            if valid:
                log.info('Current enjin session still valid!')
                await sendMarkdown(ctx, "# Current enjin session is still valid!")
                return
            else:
                log.info('Current enjin session invalid!')
        self.enjinlogin = Enjinlogin(
            email=email,
            password=password,
            url=url,
            site_id=site_id
        )
        async with ctx.typing():
            log.info('Logging into Enjin...')
            await sendMarkdown(ctx, '> Logging in...')
            enjinsession = await login(self.session, self.enjinlogin)
            if enjinsession:
                self.enjinsession = enjinsession
                await sendMarkdown(ctx, '# Login successful!', deletable=False)
            else:
                await sendMarkdown(ctx, '< Login failed! >', deletable=False)
        log.info('Cleaning up login dialog...')
        try:
            await ctx.message.delete()
        except Forbidden:
            log.warning('No permission to clean up!')
        else:
            log.info('Cleaned up!')

    @enjin.command(aliases=['stupify', 'post'])
    @commands.is_owner()
    async def request(self, ctx, method: str, *params):
        """Run an arbitrary post request to the enjin api.

        Some basics, such as jsonrpc and current session id
        are set automagically! You just have to add the
        api method as the first parameter, and necessary
        parameters for that method, in key value pairs,
        seperated by spaces.
        """

        if not self.enjinlogin:
            await sendMarkdown(ctx, '< I am not logged in to enjin yet! >')

        async with ctx.typing():
            log.info('Running enjin post request...')
            payload = {
                'method': method
            }

            if params:
                log.info('Parsing parameters...')
                if not (len(params) % 2 == 0):
                    log.warning('Uneven number of keys/values!')
                    await sendMarkdown(ctx, '< Uneven number of keys/values! >')
                    return
                params = iter(params)
                params = dict(list(zip(params, params)))
                payload['params'] = params

            resp = await post(self.session, payload, self.enjinlogin.url)
            if resp:
                log.info('Request successful!')
                resp = json.dumps(resp, indent=2)
                await send(ctx, f'```json\n{resp[:1800]}```')
            else:
                log.warning('Request failed!')
                await sendMarkdown(ctx, '< Request failed for some reason! >')


def setup(bot):
    bot.add_cog(Enjinseer(bot))
