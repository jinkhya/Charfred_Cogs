import logging
from discord import Forbidden, HTTPException, NotFound
from discord.ext import commands
from discord.utils import find
from utils.config import Config
from utils.discoutils import permission_node, sendmarkdown

log = logging.getLogger('charfred')


class Autorole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.autoroles = Config(f'{bot.dir}/data/autoroles.json',
                                load=True, loop=self.loop)
        if 'watchlist' not in self.autoroles:
            self.autoroles['watchlist'] = {}
            self.autoroles._save()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, raw):
        message_id = str(raw.message_id)
        if message_id in self.autoroles['watchlist']:
            watchorder = self.autoroles['watchlist'][message_id]
            emoji = str(raw.emoji)
            if emoji in watchorder['map']:
                log.info(f'Autorole: Reaction recognized: {emoji}')
                reason = watchorder['reason']
                watchorder = watchorder['map'][emoji]
                role = self.bot.get_guild(raw.guild_id).get_role(watchorder['role'])
                try:
                    if watchorder['action'] == 'add':
                        await raw.member.add_roles(role, reason=reason)
                    else:
                        await raw.member.remove_roles(role, reason=reason)
                except Forbidden:
                    log.warning('Autorole: Could not assign role, no permission!')
                except HTTPException:
                    log.warning('Autorole: HTTPException on assigning role!')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, raw):
        message_id = str(raw.message_id)
        if message_id in self.autoroles['watchlist']:
            watchorder = self.autoroles['watchlist'][message_id]
            emoji = str(raw.emoji)
            if emoji in watchorder['map']:
                log.info(f'Autorole: Reaction recognized: {emoji}')
                reason = watchorder['reason']
                guild = self.bot.get_guild(raw.guild_id)
                watchorder = watchorder['map'][emoji]
                role = self.bot.get_guild(raw.guild_id).get_role(watchorder['role'])
                member = guild.get_member(raw.user_id)
                try:
                    if watchorder['action'] == 'add':
                        await member.remove_roles(role, reason=reason)
                    else:
                        await member.add_roles(role, reason=reason)
                except Forbidden:
                    log.warning('Autorole: Could not assign role, no permission!')
                except HTTPException:
                    log.warning('Autorole: HTTPException on assigning role!')

    @commands.group()
    @permission_node(f'{__name__}.management')
    async def autorole(self, ctx):
        """Autorole commands.
        """
        pass

    @autorole.group(aliases=['observe'], invoke_without_command=True)
    async def watch(self, ctx, message_id: str, reason: str='Autorole'):
        """Adds a message specified by its id to the watchlist.

        You can optionally add a reason that will be added to each role add/remove
        action resulting from watching this message (only visible in the audit log).

        This alone doesn't really do anything, you'll need to also use
        the 'autorole watch mapping' command.
        """

        log.debug(message_id)
        log.debug(f'{isinstance(message_id, str)}')

        try:
            ctx.me.fetch_message(message_id)
        except NotFound:
            await sendmarkdown(ctx, '< Sorry, I can\'t find that message! >')
        except Forbidden:
            await sendmarkdown(ctx, '< Oh dear, I don\'t seem to have access to that message. >')
        except HTTPException:
            await sendmarkdown(ctx, '< Uh oh, something went wrong, I\'m terribly sorry! >')
            raise
        else:
            self.autoroles['watchlist'][message_id] = {
                'reason': reason,
                'map': {}
            }
            await self.autoroles.save()
            await sendmarkdown(ctx, '# Observation is underway!')
            log.info(f'Autorole: Watching {message_id} for reason: \"{reason}\".')

    @watch.command(aliases=['map'])
    async def mapping(self, ctx, message_id: str, action: str, *emojitorole):
        """Sets an emoji to role mapping table for the message being
        watched, identified by its id, and which action to perform,
        current supported actions are: 'add' and 'remove',
        you can add several emoji role pairs, just list them one after
        the other with spaces between.

        Please use the role name to identify the role, if a role name has spaces
        in it, wrap it in "" .

        If there is already a mapping in place for the specified message, it will be
        replaced!
        """
        if message_id not in self.autoroles['watchlist']:
            await sendmarkdown(ctx, '< The specified message is currently not under'
                               ' observation, please use the watch command first! >')
            return

        if not (action == 'add' or action == 'remove'):
            await sendmarkdown(ctx, '< Unknown action, only add and remove '
                               'are currently supported. >')
            return

        l1 = emojitorole[0::2]
        l2 = emojitorole[1::2]

        if not (len(l1) == len(l2)):
            await sendmarkdown(ctx, '< You have entered an uneven number of emoji and roles,'
                               ' please only enter pairs. >')
            return

        if find(lambda r: r.name == l1[0], ctx.guild.roles):
            rolelist = l1
            emojilist = l2
        elif find(lambda r: r.name == l2[0], ctx.guild.roles):
            rolelist = l2
            emojilist = l1
        else:
            await sendmarkdown(ctx, '< Well this is awkward, you seem to have not entered'
                               ' a valid role, please try again! >')
            return

        self.autoroles['watchlist'][message_id]['action'] = action
        self.autoroles['watchlist'][message_id]['map'] = dict(zip(emojilist, rolelist))
        await self.autoroles.save()
        await sendmarkdown(ctx, '# Mapping added!')
        log.info(f'Autorole: Added mapping for {message_id}.')

    @autorole.command(aliases=['stop', 'cancel'])
    async def endwatch(self, ctx, message_id: str):
        """Removes a message identified by its id from the watchlist.

        This also clears the emoji to role mapping table for that message.
        """
        if message_id in self.autoroles['watchlist']:
            del self.autoroles['watchlist'][message_id]
            await self.autoroles.save()
            await sendmarkdown(ctx, '# Observation called off!')
            log.info(f'Autorole: Watch on {message_id} cancelled.')
        else:
            await sendmarkdown(ctx, '< Specified message is not currently under observation! >')


def setup(bot):
    bot.register_nodes([f'{__name__}.management'])
    bot.add_cog(Autorole(bot))
