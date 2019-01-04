from discord.ext import commands
import re
import asyncio
import logging
from utils.discoutils import permissionNode, sendMarkdown
from utils.flipbooks import Flipbook

log = logging.getLogger('charfred')

cronpat = re.compile('^(?P<disabled>#)*((?P<reboot>@reboot)|(?P<min>(\*/\d+|\*|(\d+,?)+))\s(?P<hour>(\*/\d+|\*|(\d+,?)+))\s(?P<day>(\*/\d+|\*|(\d+,?)+)))\s.*spiffy\s(?P<cmd>\w+)\s(?P<server>\w+)\s(?P<args>.*)>>')
every = '*/'
always = '*'


class CronReader:
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.servercfg = bot.servercfg

    def _parseCron(self, crontab):
        parsedlines = []
        for l in crontab:
            if 'spiffy' not in l:
                continue
            match = cronpat.match(l)
            if not match:
                continue
            disabled, reboot, min, hour, day, cmd, server, args = match.group('disabled',
                                                                              'reboot',
                                                                              'min', 'hour',
                                                                              'day', 'cmd',
                                                                              'server', 'args')
            state = '> ' if disabled else '# '
            if reboot:
                condition = 'Runs at reboot:'
                output = f'{state}{condition} {cmd} {server}'
                if args:
                    output += f' {args}'
                parsedlines.append(output)
            else:
                condition = 'Runs'
                if every in min:
                    m = f'every {min[2:]} minutes'
                elif always in min:
                    m = 'every minute'
                else:
                    m = f'at {min} minutes'

                if every in hour:
                    h = f'every {hour[2:]} hours'
                elif always in hour:
                    h = 'every hour'
                else:
                    h = f'at {hour} hours'

                if every in day:
                    d = f'every {day[2:]} days'
                elif always in day:
                    d = 'every day'
                else:
                    d = f'on these days: {day}'

                output = f'{state}{condition} {m}, {h}, {d}: {cmd} {server}'
                if args:
                    output += f' {args}'
                parsedlines.append(output)

        parsedlines.append('< Please note that greyed out lines indicate\n'
                           'disabled cron jobs! Blue lines are enabled. >')
        return parsedlines

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @permissionNode('cronread')
    async def cron(self, ctx):
        """Crontab operations.

        Without a subcommand, this returns an overview
        of cronjobs that apply to any known minecraft
        servers, configured with Charfred.
        """

        log.info('Fetching current crontab...')
        proc = await asyncio.create_subprocess_exec(
            'crontab',
            '-l',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            log.info('Crontab retrieved successfully.')
        else:
            log.warning('Failed to retrieve crontab!')
            return
        crontab = stdout.decode().strip().split('\n')
        log.info('Parsing crontab...')
        spiffycron = await self.loop.run_in_executor(None, self._parseCron, crontab)
        # cronFlip = Flipbook(ctx, spiffycron, entries_per_page=8, title='Spiffy Cronjobs')
        # await cronFlip.flip()
        for i in range(0, len(spiffycron), 12):
            out = '\n'.join(spiffycron[i:i + 12])
            await sendMarkdown(ctx, out)


def setup(bot):
    bot.add_cog(CronReader(bot))


permissionNodes = ['cronread']
