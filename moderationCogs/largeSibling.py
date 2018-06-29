import logging

log = logging.getLogger('charfred')


class LargeSibling:
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session
        self.cfg = bot.cfg
        try:
            toSpyOn = self.cfg['nodes']['spec:spyOnChannels'][0]
            self.toSpyOn = [int(chan) for chan in toSpyOn.split()]
        except:
            self.toSpyOn = []
        try:
            self.hook_url = self.cfg['nodes']['spec:spyHook'][0]
        except:
            self.hook_url = None

    async def on_message(self, message):
        """Channel spy."""
        if message.author.bot or (message.guild.id is None):
            return
        if self.hook_url and (message.channel.id in self.toSpyOn):
            log.info('Spying on channel!')
            hook_this = {
                'username': f'{message.author.name} in {message.channel.name} via CharSpy',
                'avatar_url': f'{message.author.avatar_url}',
                'content': f'{message.content}'
            }
            await self.session.post(self.hook_url, json=hook_this)

    async def on_member_join(self, member):
        """Join spy."""
        log.info('Member joined!')
        if self.hook_url:
            log.info('Sending spy report!')
            hook_this = {
                'username': f'{member.name} via CharSpy',
                'avatar_url': f'{member.avatar_url}',
                'content': f'{member.name}#{member.discriminator} has joined!\n'
                           f'ID: {member.id}'
            }
            await self.session.post(self.hook_url, json=hook_this)

    async def on_member_remove(self, member):
        """Leave spy."""
        log.info('Member left!')
        if self.hook_url:
            log.info('Sending spy report!')
            hook_this = {
                'username': f'{member.name} via CharSpy',
                'avatar_url': f'{member.avatar_url}',
                'content': f'{member.name}#{member.discriminator} has left!'
            }
            await self.session.post(self.hook_url, json=hook_this)

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
        if self.hook_url:
            log.info('Sending spy report!')
            hook_this = {
                'username': f'{after.name} via CharSpy',
                'avatar_url': f'{after.avatar_url}',
                'content': f'I have {verb} the {roles[0]} role!'
            }
            await self.session.post(self.hook_url, json=hook_this)


def setup(bot):
    bot.add_cog(LargeSibling(bot))


permissionNodes = {
    'spec:spyHook': ['Please enter the webhook url for the LargeSibling spy functionality\n',
                     ''],
    'spec:spyOnChannels': ['Please enter all the channel\'s IDs that you wish to spy on!\n'
                           'Seperated by spaces only!', '']
}
