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
                role = self.bot.get_guild(raw.guild_id).get_role(watchorder['map'][emoji])
                try:
                    if watchorder['action'] == 'add':
                        await raw.member.add_roles(role)
                    else:
                        await raw.member.remove_roles(role)
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
                guild = self.bot.get_guild(raw.guild_id)
                role = self.bot.get_guild(raw.guild_id).get_role(watchorder['map'][emoji])
                member = guild.get_member(raw.user_id)
                try:
                    if watchorder['action'] == 'add':
                        await member.remove_roles(role)
                    else:
                        await member.add_roles(role)
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
    async def watch(self, ctx, message_id: str, action: str, *emojitorole):
        """Adds a message specified by its id to the watchlist, sets which action
        to perform and sets an emoji to role mapping table; you need to be
        in the channel the message is in for this to work!

        Current supported actions are: 'add' and 'remove',
        you can add several emoji role pairs, just list them one after
        the other with spaces between.

        Please use the role name to identify the role, if a role name has spaces
        in it, wrap it in "" .

        If there is already a mapping in place for the specified message, it will be
        replaced!
        """
        try:
            towatch = await ctx.channel.fetch_message(message_id)
        except NotFound:
            await sendmarkdown(ctx, '< Sorry, I can\'t find that message! >')
            return
        except Forbidden:
            await sendmarkdown(ctx, '< Oh dear, I don\'t seem to have access to that message. >')
            return
        except HTTPException:
            await sendmarkdown(ctx, '< Uh oh, something went wrong, I\'m terribly sorry! >')
            raise

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

        roles = []
        for rolename in rolelist:
            role = find(lambda r: r.name == rolename, ctx.guild.roles)
            if role is None:
                await sendmarkdown(ctx, f'< {rolename} did not match any existing role! '
                                   'Abort! >')
                return
            else:
                roles.append(role.id)

        self.autoroles['watchlist'][message_id] = {
            'action': action,
            'map': dict(zip(emojilist, roles))
        }
        await self.autoroles.save()
        await sendmarkdown(ctx, '# Observation is underway!')
        await towatch.add_reaction('🔭')
        log.info(f'Autorole: Watching {message_id}.')

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
