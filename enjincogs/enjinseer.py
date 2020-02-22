import logging
import json
from collections import namedtuple
from discord.ext import commands
from utils.config import Config
from utils.discoutils import permission_node
from .utils.enjinutils import login, post

log = logging.getLogger('charfred')

Enjinlogin = namedtuple('Enjinlogin', 'email password url site_id')


class Enjinseer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session
        if not hasattr(bot, 'enjinsession'):
            bot.enjinsession = None
        self.enjinsession = bot.enjinsession
        if not hasattr(bot, 'enjinlogin'):
            bot.enjinlogin = None
        self.enjinlogin = bot.enjinlogin

        self.enjincfg = Config(
            f'{bot.dir}/configs/enjincfg.json',
            loop=self.bot.loop, load=True
        )

    @commands.group(hidden=True)
    async def enjin(self, ctx):
        """Enjin Management commands."""
        pass

    @enjin.command()
    @permission_node(f'{__name__}.enjinlogin')
    async def login(self, ctx, email: str = None, password: str = None,
                    url: str = None, site_id: str = None):
        """Enjin user login and session saving.

        Establishes a session to be used by other enjin related cogs.
        """

        log.info('Starting enjin login!')

        if None in (email, password, url, site_id):
            log.info('No credentials given, trying config...')
            if 'login' in self.enjincfg:
                log.info('Logging in with saved credentials...')
                email, password, url, site_id = self.enjincfg['login']
            else:
                log.warning('No saved credentials available!')
                await ctx.sendmarkdown('< No credentials! Login impossible. >')
                return
        else:
            if url.endswith('/'):
                url = url[:-1]

        self.enjinlogin = self.bot.enjinlogin = Enjinlogin(
            email=email,
            password=password,
            url=url,
            site_id=site_id
        )

        async with ctx.typing():
            log.info('Logging into Enjin...')
            await ctx.sendmarkdown('> Logging in...')
            enjinsession = await login(self.session, self.enjinlogin)
            if enjinsession:
                self.enjinsession = self.bot.enjinsession = enjinsession
                self.enjincfg['login'] = [email, password, url, site_id]
                await ctx.sendmarkdown('# Login successful!', deletable=False)
            else:
                await ctx.sendmarkdown('< Login failed! >', deletable=False)

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

        if not self.enjinsession:
            await ctx.sendmarkdown('< I am not logged in to enjin yet! >')
            return

        async with ctx.typing():
            log.info('Running enjin post request...')
            payload = {
                'method': method
            }

            if params:
                log.info('Parsing parameters...')
                if not (len(params) % 2 == 0):
                    log.warning('Uneven number of keys/values!')
                    await ctx.sendmarkdown('< Uneven number of keys/values! >')
                    return
                params = iter(params)
                params = dict(list(zip(params, params)))
                payload['params'] = params
                payload['params']['session_id'] = self.enjinsession.session_id
            else:
                payload['params'] = {
                    'session_id': self.enjinsession.session_id
                }

            resp = await post(self.session, payload, self.enjinsession.url)
            if resp:
                log.info('Request successful!')
                resp = json.dumps(resp, indent=2)
                resp = [resp[i:i + 1800] for i in range(0, len(resp), 1800)]
                for section in resp[:8]:
                    await ctx.send(f'```json\n{section}```')
            else:
                log.warning('Request failed!')
                await ctx.sendmarkdown('< Request failed for some reason! >')


def setup(bot):
    bot.register_nodes([f'{__name__}.enjinlogin'])
    bot.add_cog(Enjinseer(bot))
