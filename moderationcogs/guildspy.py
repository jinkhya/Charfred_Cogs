import logging
from discord import Webhook, AsyncWebhookAdapter, Embed
from discord.ext import commands

log = logging.getLogger('charfred')


class Guildspy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session
        self.cfg = bot.cfg
        try:
            self.hook = Webhook.from_url(self.cfg['cogcfgs'][f'{__name__}.spyhook'][0],
                                         adapter=AsyncWebhookAdapter(self.session))
        except KeyError:
            self.hook = None

    async def _hookit(self, member, content):
        log.info('Sending spy report!')
        await self.hook.send(
            username=f'{member.name} via CharSpy',
            avatar_url=f'{member.avatar_url}',
            content=content
        )

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Ban spy."""
        log.info('Member got banned, ouch!')
        if self.hook:
            hook_embed = Embed(
                title='Ban Action:',
                color=0x008080
            )
            hook_embed.set_image('https://cdn.discordapp.com/attachments/'
                                 '327174378527653889/535248231265992744/O3DHIA5.gif')
            hook_embed.add_field(
                name=f'I, {user.name}',
                value='was banned!'
            )
            log.info('Sending spy report!')
            await self.hook.send(
                username=f'{user.name} via CharSpy',
                avatar_url=f'{user.avatar_url}',
                embed=hook_embed
            )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Join spy."""
        log.info('Member joined!')
        if self.hook:
            content = f'{member.name}#{member.discriminator} has joined!\nID: {member.id}'
            await self._hookit(member, content)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Leave spy."""
        log.info('Member left!')
        if self.hook:
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
        if self.hook:
            if len(before.roles) > len(after.roles):
                roles = list(set(before.roles) - set(after.roles))
                verb = 'lost'
            else:
                roles = list(set(after.roles) - set(before.roles))
                verb = 'gained'
            content = f'I have {verb} the {roles[0]} role!'
            await self._hookit(after, content)


def setup(bot):
    bot.register_cfg(f'{__name__}.spyhook',
                     'Please enter the webhook url for the Guildspy webhook functionality:\n',
                     '')
    bot.add_cog(Guildspy(bot))
