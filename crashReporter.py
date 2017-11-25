#!/usr/bin/env python

from discord.ext import commands
import os
import glob
import asyncio
import logging
from .utils.discoutils import has_permission, sendReply
from .configs import configs as cfg
# cfg no longer has serverspath, rebuild to use Config

log = logging.getLogger('charfred')


class crashReporter:
    def __init__(self, bot):
        self.bot = bot

    # TODO: Implement all of this without pastebin,
    # possibly with some heavier processing of the crashreport itself,
    # so that it fits into an embedd.
    async def getPasteKey(session):
        async with session.post(
            'https://pastebin.com/api/api_login.php',
            data={'api_dev_key': cfg.pastebinToken,
                  'api_user_name': cfg.pastebinUser,
                  'api_user_password': cfg.pastebinPass}) as resp:
            return await resp.text()

    @commands.command(aliases=['report', 'crashreports'])
    @has_permission('crashreport')
    async def crashreport(self, ctx, server: str, age: str=None):
        """Retrieves the last crashreport for the given server;
        Takes a relative age parameter, 0 for the newest report,
        1 for the one before, etc.
        """
        if age is None:
            reportFile = sorted(
                glob.iglob(cfg['serverspath'] + f'/{server}/crash-reports/*'),
                key=os.path.getmtime,
                reverse=True
            )[0]
        else:
            reportFile = sorted(
                glob.iglob(cfg['serverspath'] + f'/{server}/crash-reports/*'),
                key=os.path.getmtime,
                reverse=True
            )[int(age)]
        proc = await asyncio.create_subprocess_exec(
            'awk',
            '/^Time: /{e=1}/^-- Head/{e=1}/^-- Block/{e=1}/^-- Affected/{e=1}/^-- System/{e=0}/^A detailed/{e=0}{if(e==1){print}}',
            reportFile,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        log.info(f'Getting report for {server}.')
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            log.info(f'Report retrieved successfully.')
        else:
            log.warning('Failed to retrieve report!')
            return
        report = stdout.decode().strip()
        params = {
            'api_dev_key': cfg.pastebinToken,
            'api_option': 'paste',
            'api_paste_code': report,
            'api_user_key': self.bot.pasteKey,
            'api_paste_private': '2',
            'api_paste_expire_date': '10M'
        }
        async with self.bot.session as cs:
            async with cs.get('https://pastebin.com/api/api_post.php',
                              params=params) as resp:
                pasteLink = await resp.text()
                print(f'Generated pastebin link: {pasteLink}')
        await sendReply(ctx, pasteLink)


def setup(bot):
    bot.add_cog(crashReporter(bot))
