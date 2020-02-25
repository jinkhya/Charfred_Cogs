import logging
import asyncio
from datetime import datetime
from threading import Event
from discord import Forbidden
from discord.ext import commands
from discord.utils import find
from utils import Config, permission_node

log = logging.getLogger('charfred')


class Porter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session
        self.loop = bot.loop
        self.promotees = Config(f'{self.bot.dir}/data/promotees_persist.json',
                                load=True, loop=self.bot.loop)
        self.memberRoleName = bot.cfg['cogcfgs'][f'{__name__}.memberRole'][0]
        try:
            self.hook_url = bot.cfg['cogcfgs'][f'{__name__}.spyhook'][0]
        except:
            self.hook_url = None
        self.flood = False
        self.autokicker = None
        if 'awaiting' not in self.promotees:
            self.promotees['awaiting'] = []

    def cog_unload(self):
        if self.autokicker:
            self.autokicker[1].set()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if str(member) in self.promotees['awaiting']:
            log.info(f'Promotee {member.name} has joined, promoting now.')
            memberRole = find(lambda r: r.name == self.memberRoleName, member.guild.roles)
            await member.edit(roles=[memberRole])
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
    async def floodmode(self, ctx):
        """Floodmode commands.

        This returns the current floodmode status,
        if no subcommand was given.
        """
        if self.flood:
            log.info('Floodmode active!')
            await ctx.sendmarkdown('# Floodmode is currently active!')
        else:
            log.info('Floodmode inactive!')
            await ctx.sendmarkdown('> Floodmode is currently inactive!')

    @floodmode.command(aliases=['start', 'on'])
    @permission_node(f'{__name__}.floodmode')
    async def activate(self, ctx):
        """Activates floodmode.

        During floodmode any joining users who have no pending membership
        will be automatically kicked.
        """

        log.info('Activated floodmode!')
        self.flood = True
        await ctx.sendmarkdown('Floodmode activated!')

    @floodmode.command(aliases=['stop', 'off'])
    @permission_node(f'{__name__}.floodmode')
    async def deactivate(self, ctx):
        """Deactivates floodmode."""

        log.info('Deactivated floodmode!')
        self.flood = False
        await ctx.sendmarkdown('Floodmode deactivated!')

    @commands.command()
    @permission_node(f'{__name__}.newbiepromote')
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
                await ctx.sendmarkdown('# User has not joined yet, adding to waitlist.')
            else:
                log.info('Cannot wait for invalid username!')
                await ctx.sendmarkdown(f'< \"{promotee}\" is in an invalid format, please try again!')
        else:
            log.info('User is already a member, promoting immediately.')
            memberRole = find(lambda r: r.name == self.memberRoleName, member.guild.roles)
            await member.edit(roles=[memberRole])
            await ctx.sendmarkdown('# User is already a member, promoting immediately.')

    @commands.group()
    @permission_node(f'{__name__}.autokick')
    async def autokick(self, ctx):
        """Discord autokick commands.

        This returns a status message,
        if no subcommand was given.
        """

        if self.autokicker:
            if not self.autokicker[0].done():
                await ctx.sendmarkdown('# Autokick is active; kick after '
                                       f'{self.autokicker[3]} minutes.')
        else:
            await ctx.sendmarkdown('< Autokick is not active. >')

    async def _hookit(self, member, content):
        log.info('Sending kick report!')
        hook_this = {
            'username': f'{member.name} via CharSpy',
            'avatar_url': f'{member.avatar_url}',
            'content': 'I got kicked for being a nobody after curfew!'
        }
        await self.session.post(self.hook_url, json=hook_this)

    @autokick.command()
    async def enable(self, ctx, kickafter: int=24, *, kickmsg):
        """Enable autokick, with given parameters.

        Requires a time in hours, after which to autokick users
        with no role, and a message which will be DM'd to the
        kicked user.
        The message will be sent in a markdown syntax block.
        """

        if self.autokicker and not self.autokicker[0].done():
            log.info('Autokick already active!')
            await ctx.sendmarkdown('# Autokick is already active!')
            return

        async def kicknotify(member):
            await ctx.sendmarkdown(member, kickmsg, deletable=False)

        async def stopnotify():
            await ctx.sendmarkdown('# Autokicking suspended!')

        def autokickdone(future):
            log.info(f'Stopping autokick.')
            if future.exception():
                log.warning(f'Exception in autokicker!')
            asyncio.run_coroutine_threadsafe(stopnotify(), self.loop)

        def startautokicking(event):
            log.info(f'Starting autokick with a timeout of {kickafter} minutes!')
            channel = ctx.message.channel
            while not event.is_set():
                pass


def setup(bot):
    permission_nodes = ['newbiepromote', 'floodmode']
    bot.register_nodes([f'{__name__}.{node}' for node in permission_nodes])
    bot.register_cfg(f'{__name__}.memberRole',
                     'Please enter the name of the baseline member role to be promoted to:\n',
                     'Member')
    bot.register_cfg(f'{__name__}.spyhook',
                     'Please enter the webhook url used for the Porter webhook functionality:\n',
                     '')
    bot.add_cog(Porter(bot))
