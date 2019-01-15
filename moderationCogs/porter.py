import logging
from discord import Forbidden
from discord.ext import commands
from discord.utils import find
from utils.config import Config
from utils.discoutils import permissionNode, sendMarkdown

log = logging.getLogger('charfred')


class Porter:
    def __init__(self, bot):
        self.bot = bot
        self.promotees = Config(f'{self.bot.dir}/data/promotees_persist.json',
                                load=True, loop=self.bot.loop)
        self.memberRoleName = bot.cfg['nodes']['spec:memberRole'][0]
        self.flood = False
        if 'awaiting' not in self.promotees:
            self.promotees['awaiting'] = []

    async def on_member_join(self, member):
        if str(member) in self.promotees['awaiting']:
            log.info(f'Promotee {member.name} has joined, promoting now.')
            memberRole = find(lambda r: r.name == self.memberRoleName, member.guild.roles)
            await member.add_roles(memberRole)
            self.promotees['awaiting'].remove(str(member))
            await self.promotees.save()
            return

        if self.flood:
            if member.top_role.name == '@everyone':
                log.info(f'Floodmode: {member.name} has no pending membership!')
                try:
                    await member.send(f'Hey there {member.name},\nsorry for kicking you from '
                                      f'{member.guild.name}, but we are currently in floodmode.'
                                      '\nIf you have a pending application please wait for it '
                                      'to be approved and then try joining our Discord again!\n'
                                      'Good day!\n\n - This is a machine generated message, '
                                      'replies are futile!')
                    await member.kick(reason="No pending membership!")
                except Forbidden:
                    log.warning('No permission to kick members!')
                    log.warning('They still got the kick DM and are probably very confused now!')
                else:
                    log.info(f'Floodmode: {member.name} was kicked!')

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def floodmode(self, ctx):
        """Floodmode commands.

        This returns the current floodmode status,
        if no subcommand was given.
        """
        if self.flood:
            log.info('Floodmode active!')
            await sendMarkdown(ctx, '# Floodmode is currently active!')
        else:
            log.info('Floodmode inactive!')
            await sendMarkdown(ctx, '> Floodmode is currently inactive!')

    @floodmode.command(aliases=['start', 'on'])
    @commands.guild_only()
    @permissionNode('floodmode')
    async def activate(self, ctx):
        """Activates floodmode.

        During floodmode any joining users who have no pending membership
        will be automatically kicked.
        """

        log.info('Activated floodmode!')
        self.flood = True
        await sendMarkdown(ctx, 'Floodmode activated!')

    @floodmode.command(aliases=['stop', 'off'])
    @commands.guild_only()
    @permissionNode('floodmode')
    async def deactivate(self, ctx):
        """Deactivates floodmode."""

        log.info('Deactivated floodmode!')
        self.flood = False
        await sendMarkdown(ctx, 'Floodmode deactivated!')

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
    bot.add_cog(Porter(bot))


permissionNodes = {
    'spec:memberRole': ['Please enter the name of the baseline member role to be promoted to', "Member"],
    'newbiepromote': '',
    'floodmode': ''
}
