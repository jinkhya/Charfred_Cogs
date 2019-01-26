import logging
import json
from discord.ext import commands
from utils.config import Config
from utils.discoutils import permissionNode, sendMarkdown, promptInput, promptConfirm, send
from .utils.enjinutils import post, verifysession

log = logging.getLogger('charfred')


class ApplicationHelper:
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session
        if hasattr(bot, 'enjinsession'):
            self.enjinsession = bot.enjinsession
        else:
            self.enjinsession = None
        if hasattr(bot, 'enjinlogin'):
            self.enjinlogin = bot.enjinlogin
        else:
            self.enjinlogin = None
        self.apptemplate = Config(f'{bot.dir}/configs/applicationtemplate.json',
                                  load=True, loop=bot.loop)

    @commands.group(aliases=['enjinapps', 'app'], invoke_without_command=True)
    @permissionNode('enjinapps')
    async def apps(self, ctx):
        """Enjin Application commands.

        Gives some enjin login status information, when no subcommand is given.
        """

        if hasattr(self.bot, 'enjinsession'):
            self.enjinsession = self.bot.enjinsession
        else:
            self.enjinsession = None
        if hasattr(self.bot, 'enjinlogin'):
            self.enjinlogin = self.bot.enjinlogin
        else:
            self.enjinlogin = None

        if not self.apptemplate:
            await sendMarkdown(ctx, '< No application template available! >')
        if not self.enjinsession:
            await sendMarkdown(ctx, '< Not logged into enjin! >')
        elif not self.enjinlogin:
            await sendMarkdown(ctx, '< No enjin login information available! >')
        else:
            valid = await verifysession(self.session, self.enjinlogin)
            if valid:
                await sendMarkdown(ctx, '# All is well!')
            else:
                await sendMarkdown(ctx, '< Current enjin session is invalid! >')

    @apps.command(aliases=['configure'])
    @permissionNode('enjinedittemplate')
    async def settemplate(self, ctx, correctappid: int):
        """Save a template for comparison against those applications correctness.

        You may specify an application id, for an \'ideal\' application,
        after which said application will be parsed and you will be prompted
        to select the fields that you wish your template to contain.
        """

        if self.apptemplate:
            log.info('Application template already saved.')
            b, _, _ = await promptConfirm(ctx, 'An application template already '
                                          'exists, do you wish to override?')
            if not b:
                await sendMarkdown(ctx, '> Configuration complete!')
                return
        payload = {
            'method': 'Applications.getApplication',
            'params': {
                'session_id': self.enjinsession.session_id,
                'application_id': correctappid
            }
        }
        app = await post(self.session, payload, self.enjinsession.url)
        if not app:
            log.info('No application recieved!')
            await sendMarkdown(ctx, '< Did not recieve an application! >')
            return
        app = app['result']
        fields = app['user_data']
        msg = ['# Retrieved Application contained the following entries:']
        qhashes = list(fields.keys())
        for i, key in enumerate(qhashes):
            msg.append(f'[{i}]: {fields[key]}')
        msg.append('\n> Please note that, unfortunately, the enjin api does '
                   'not return the actual prompts or questions attached to '
                   'each field, so you\'ll have to figure out which field '
                   'is which... (they should be in the correct order at least).')
        msg = '\n'.join(msg)
        await sendMarkdown(ctx, msg)
        await sendMarkdown(ctx, '> The next bit is gonna be a bit tricky...')
        selection, _, _ = await promptInput(
            ctx,
            '# Please enter the numbers for all the fields you wish to include '
            'in the template, together with a shortname for each field.\n\n'
            'The shortname should later help you identify which field is which.\n'
            '< it should be really short, and contain no spaces >\n'
            '> you may use underscores in place of spaces however\n'
            'In the end you should have a list like such:\n'
            '1 rule_1 2 rule_2 5 rule_11\n\n'
            '# Go on, type type! These prompts time out faster than you think...',
            360
        )
        if not selection or not (len(selection) % 2 == 0):
            log.info('Prompt failed!')
            await sendMarkdown(ctx, '< Prompt failed, please try again! >')
        selection = iter(selection)
        selection = dict(list(zip(selection, selection)))
        for k, v in selection.items():
            self.apptemplate[qhashes[k]] = [v, fields[qhashes[k]]]
        await self.apptemplate.save()
        await sendMarkdown(ctx, '# Template saved!\n> You may review the current '
                           'template via the viewtemplate command.')

    @apps.command()
    async def viewtemplate(self, ctx):
        """Prints the raw json of the current template."""

        log.info('Printing enjin application template.')
        template = json.dumps(self.apptemplate, indent=2)
        await sendMarkdown(ctx, '# Current enjin application template:')
        await send(ctx, f'```json\n{template}```')

    @apps.command(name='list')
    async def _list(self, ctx, type: str='open'):
        """Retrieves a condensed list of applications.

        You may specify a type, if you wish to see closed or rejected
        applications, otherwise it will default to open ones.
        """

        log.info('Retrieving applications...')
        payload = {
            'method': 'Applications.getList',
            'params': {
                'session_id': self.enjinsession.session_id,
                'type': type,
                'site_id': self.enjinsession.site_id
            }
        }
        apps = await post(self.session, payload, self.enjinsession.url)
        if not apps:
            log.warning('Application retrieval failed!')
            await sendMarkdown(ctx, f'< Application retrieval failed! >')
            return
        msg = [f'# The following applications are currently {type}:\n']
        for app in apps['result']['items']:
            msg.append('Application by: ' + app['username'])
            msg.append('Application ID: ' + app['application_id'] + '\n')
        msg = '\n'.join(msg)
        await sendMarkdown(ctx, msg)
        log.info('Applications retrieved and listed!')

    @apps.command(aliases=['check'])
    async def validate(self, ctx, applicationid: int):
        """Validate a given application against the saved template.

        Requires the application id for the application you wish to
        validate (you may use the apps list command to retrieve a
        list of such ids).
        """

        log.info('Validating application...')
        if not self.apptemplate:
            log.warning('No template found!')
            await sendMarkdown(ctx, '< No template found! Please configure'
                               'one before trying again! >')
            return
        payload = {
            'method': 'Applications.getApplication',
            'params': {
                'session_id': self.enjinsession.session_id,
                'application_id': applicationid
            }
        }
        app = await post(self.session, payload, self.enjinsession.url)
        if not app:
            log.warning('App could not be retrieved!')
            await sendMarkdown(ctx, '< App could not be retrieved! >')
            return
        user = app['result']['username']
        answers = app['result']['user_data']
        freeformfields = {k: v for k, v in answers.items() if k not in self.apptemplate}
        correctfields = {k: v for k, v in answers.items() if k in self.apptemplate and
                         v == self.apptemplate[k][1]}
        incorrectfields = {k: v for k, v in answers.items() if k not in freeformfields and
                           k not in correctfields}
        msg = [f'# Application by: {user}']
        for k, v in correctfields.items():
            shortname = self.apptemplate[k][0]
            msg.append(f'# {shortname}: {v}')
        msg.append('\n\n')
        for k, v in incorrectfields.items():
            shortname = self.apptemplate[k][0]
            msg.append(f'< {shortname}: {v} >')
        msg.append('\n\n> Correct fields are color coded in blue (#)\n'
                   '> Incorrect fields are color coded in yellow (<>)')
        msg = '\n'.join(msg)
        await sendMarkdown(ctx, msg)


def setup(bot):
    bot.add_cog(ApplicationHelper(bot))


permissionNodes = ['enjinapps', 'enjinedittemplate']
