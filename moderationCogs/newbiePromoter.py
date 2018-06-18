import logging
from discord.ext import commands
from discord.utils import find
from utils.config import Config
from utils.discoutils import permissionNode, sendMarkdown

log = logging.getLogger('charfred')


class NewbiePromoter:
    def __init__(self, bot):
        self.bot = bot
        self.promotees = Config(f'{self.bot.dir}/data/promotees_persist.json',
                                load=True, loop=self.bot.loop)
        self.memberRoleName = bot.cfg['nodes']['spec:memberRole'][0]
        if 'awaiting' not in self.promotees:
            self.promotees['awaiting'] = []

    async def on_member_join(self, member):
        if str(member) in self.promotees['awaiting']:
            log.info(f'Promotee {member.name} has joined, promoting now.')
            memberRole = find(lambda r: r.name == self.memberRoleName, member.guild.roles)
            await member.add_roles(memberRole)
            self.promotees['awaiting'].remove(str(member))
            await self.promotees.save()

    @commands.command()
    @commands.guild_only()
    @permissionNode('newbiepromote')
    async def promote(self, ctx, promotee: str):
        """Promote a user to the baseline member role.

        Takes a username plus discriminator.
        If the user to promote is not already a member,
        he will be promoted upon joining the guild.
        The baseline member role is configurable.
        """

        try:
            member = await commands.MemberConverter().convert(ctx, promotee)
        except commands.BadArgument:
            if len(promotee) > 5 and promotee[-5] == '#':
                log.info('User hasn\'t joined yet, adding to waitlist.')
                self.promotees['awaiting'].append(promotee)
                await self.promotees.save()
                await sendMarkdown(ctx, '# User has not joined yet, adding to waitlist.')
            else:
                log.info('Cannot wait for invalid username!')
                await sendMarkdown(ctx, f'< \"{promotee}\" is in an invalid format, please try again!')
        else:
            log.info('User is already a member, promoting immediately.')
            memberRole = find(lambda r: r.name == self.memberRoleName, member.guild.roles)
            await member.add_roles(memberRole)
            await sendMarkdown(ctx, '# User is already a member, promoting immediately.')


def setup(bot):
    bot.add_cog(NewbiePromoter(bot))


permissionNodes = {
    'spec:memberRole': ['Please enter the name of the baseline member role to be promoted to', "Member"],
    'newbiepromote': ''
}
