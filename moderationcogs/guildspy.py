import logging
from discord.ext import commands

log = logging.getLogger('charfred')


class Guildspy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session
        self.cfg = bot.cfg
        try:
            self.hook_url = self.cfg['nodes']['spec:spyHook'][0]
        except:
            self.hook_url = None

    async def _hookit(self, member, content):
        log.info('Sending spy report!')
        hook_this = {
            'username': f'{member.name} via CharSpy',
            'avatar_url': f'{member.avatar_url}',
            'content': content
        }
        await self.session.post(self.hook_url, json=hook_this)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Ban spy."""
        log.info('Member got banned, ouch!')
        if self.hook_url:
            hook_this = {
                'username': f'{user.name} via CharSpy',
                'avatar_url': f'{user.avatar_url}',
                'embeds': [{
                    'title': 'Ban Action:',
                    'color': 0x008080,
                    'image': {
                        'url': 'https://cdn.discordapp.com/attachments/327174378527653889/535248231265992744/O3DHIA5.gif'
                    },
                    'fields': [{
                        'name': f'I, {user.name}',
                        'value': 'was banned!'
                    }]
                }]
            }
            log.info('Sending spy report!')
            await self.session.post(self.hook_url, json=hook_this)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Join spy."""
        log.info('Member joined!')
        if self.hook_url:
            content = f'{member.name}#{member.discriminator} has joined!\nID: {member.id}'
            await self._hookit(member, content)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Leave spy."""
        log.info('Member left!')
        if self.hook_url:
            if member.top_role.name == '@everyone':
                role = 'nobody'
            else:
                role = member.top_role.name
            content = f'{member.name}#{member.discriminator} has left, he was a {role}!'
            await self._hookit(member, content)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Member role-update spy."""
        if len(before.roles) == len(after.roles):
            return
        log.info('Member has updated roles.')
        if self.hook_url:
            if len(before.roles) > len(after.roles):
                roles = list(set(before.roles) - set(after.roles))
                verb = 'lost'
            else:
                roles = list(set(after.roles) - set(before.roles))
                verb = 'gained'
            content = f'I have {verb} the {roles[0]} role!'
            await self._hookit(after, content)


def setup(bot):
    bot.add_cog(Guildspy(bot))


permissionNodes = {
    'spec:spyHook': ['Please enter the webhook url for the LargeSibling spy functionality\n', '']
}
