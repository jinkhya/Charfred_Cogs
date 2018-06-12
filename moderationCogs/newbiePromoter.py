import logging
import discord
from discord.ext import commands
from discord.utils import find
from utils.config import Config
from utils.discoutils import permissionNode

log = logging.getLogger('charfred')


class NewbiePromoter:
    def __init__(self, bot):
        self.bot = bot
        self.promotees = Config(f'{self.bot.dir}/data/promotees_persist.json',
                                load=True, loop=self.loop)
        self.memberRoleName = bot.cfg['nodes']['spec:memberRole'][0]

    async def on_member_join(self, member):
        if member.id in self.promotees['awaiting']:
            memberRole = find(lambda r: r.name == self.memberRoleName, member.guild.roles)
            await member.add_roles(memberRole)
            self.promotees['awaiting'].remove(member.id)
            await self.promotees.save()

    @commands.command()
    @commands.guild_only()
    @permissionNode('newbiepromote')
    async def promote(self, ctx, user: discord.User):
        """Promote a user to the baseline member role.

        If the user to promote is not already a member,
        he will be promoted upon joining the guild.
        The baseline member role is configurable.
        """
        member = ctx.guild.get_member(user.id)
        if member:
            memberRole = find(lambda r: r.name == self.memberRoleName, member.guild.roles)
            await member.add_roles(memberRole)
        else:
            self.promotees['awaiting'].append(user.id)
            await self.promotees.save()


def setup(bot):
    bot.add_cog(NewbiePromoter(bot))


permissionNodes = {
    'spec:memberRole': ['Please enter the name of the baseline member role to be promoted to', "Member"],
    'newbiepromote': ''
}
