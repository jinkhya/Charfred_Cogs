import logging

log = logging.getLogger('charfred')


class LargeSibling:
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session
        self.cfg = bot.cfg

    async def on_member_join(self, member):
        """Join spy."""
        log.info('Member joined!')
        try:
            hook_url = self.cfg['nodes']['spec:spyHook'][0]
        except:
            pass
        else:
            if hook_url:
                log.info('Sending spy report!')
                hook_this = {
                    'username': f'{member.name} via CharSpy',
                    'avatar_url': f'{member.avatar_url}',
                    'content': f'{member.name}#{member.discriminator} has joined!\n'
                               f'ID: {member.id}\nThis is an automated message, do not reply!'
                }
                await self.session.post(hook_url, json=hook_this)

    async def on_member_remove(self, member):
        """Leave spy."""
        log.info('Member left!')
        try:
            hook_url = self.cfg['nodes']['spec:spyHook'][0]
        except:
            pass
        else:
            if hook_url:
                log.info('Sending spy report!')
                hook_this = {
                    'username': f'{member.name} via CharSpy',
                    'avatar_url': f'{member.avatar_url}',
                    'content': f'{member.name}#{member.discriminator} has left!\n'
                               'This is an automated message, do not reply!'
                }
                await self.session.post(hook_url, json=hook_this)

    async def on_member_update(self, before, after):
        """Member role-update spy."""
        if len(before.roles) == len(after.roles):
            return
        log.info('Member has updated roles.')
        if len(before.roles) > len(after.roles):
            roles = list(set(before.roles) - set(after.roles))
            verb = 'lost'
        else:
            roles = list(set(after.roles) - set(before.roles))
            verb = 'gained'
        try:
            hook_url = self.cfg['nodes']['spec:spyHook'][0]
        except:
            pass
        else:
            if hook_url:
                log.info('Sending spy report!')
                hook_this = {
                    'username': f'{after.name} via CharSpy',
                    'avatar_url': f'{after.avatar_url}',
                    'content': f'I have {verb} the {roles[0]} role!\n'
                               'This is an automated message, do not reply!'
                }
                await self.session.post(hook_url, json=hook_this)


def setup(bot):
    bot.add_cog(LargeSibling(bot))


permissionNodes = {
    'spec:spyHook': ['Please enter the webhook url for the LargeSibling spy functionality\n',
                     None]
}
