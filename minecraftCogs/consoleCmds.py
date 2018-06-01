from discord.ext import commands
import logging
from utils.config import Config
from utils.discoutils import sendMarkdown, permissionNode
from .utils.mcservutils import isUp, sendCmd

log = logging.getLogger('charfred')


class ConsoleCmds:
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.servercfg = bot.servercfg

    @commands.group()
    @commands.guild_only()
    @permissionNode('whitelist')
    async def player(self, ctx):
        """Minecraft player management operations."""

        if ctx.invoked_subcommand is None:
            pass

    @player.group()
    @permissionNode('whitelist')
    async def whitelist(self, ctx):
        """Minecraft player whitelisting operations."""

        if ctx.invoked_subcommand is None:
            pass

    @whitelist.command()
    async def add(self, ctx, player: str):
        """Add a player to the whitelist."""

        msg = ['Command Log', '==========']
        for server in self.servercfg['servers']:
            if isUp(server):
                log.info(f'Whitelisting {player} on {server}.')
                await sendCmd(self.loop, server, f'whitelist add {player}')
                msg.append(f'# Whitelisted {player} on {server}.')
            else:
                log.warning(f'Could not whitelist {player} on {server}.')
                msg.append(f'< Unable to whitelist {player}, {server} is offline! >')
        await sendMarkdown(ctx, '\n'.join(msg))

    @whitelist.command()
    async def remove(self, ctx, player: str):
        """Remove a player from the whitelist."""

        msg = ['Command Log', '==========']
        for server in self.servercfg['servers']:
            if isUp(server):
                log.info(f'Unwhitelisting {player} on {server}.')
                await sendCmd(self.loop, server, f'whitelist remove {player}')
                msg.append(f'# Unwhitelisting {player} on {server}.')
            else:
                log.warning(f'Could not unwhitelist {player} on {server}.')
                msg.append(f'< Unable to unwhitelist {player}, {server} is offline! >')
        await sendMarkdown(ctx, '\n'.join(msg))

    @whitelist.command()
    async def check(self, ctx, player: str):
        """Check if a player is on the whitelist."""

        msg = ['Command Log', '==========']
        for server in self.servercfg['servers']:
            with open(
                self.servercfg['serverspath'] + f'/{server}/whitelist.json', 'r'
            ) as whitelist:
                if player in whitelist.read():
                    msg.append(f'# {player} is whitelisted on {server}.')
                else:
                    msg.append(f'< {player} is NOT whitelisted on {server}. >')
        await sendMarkdown(ctx, '\n'.join(msg))

    @player.command()
    @permissionNode('kick')
    async def kick(self, ctx, server: str, player: str):
        """Kick a player from a specified server.

        Takes a servername and playername, in that order.
        """

        msg = ['Command Log', '==========']
        if isUp(server):
            log.info(f'Kicking {player} from {server}.')
            await sendCmd(self.loop, server, f'kick {player}')
            msg.append(f'# Kicked {player} from {server}.')
        else:
            msg.append(f'< {server} is not online! >')
        await sendMarkdown(ctx, '\n'.join(msg))

    @player.command()
    @permissionNode('ban')
    async def ban(self, ctx, player: str):
        """Bans a player, and unwhitelists just to be safe."""

        msg = ['Command Log', '==========']
        for server in self.servercfg['servers']:
            if isUp(server):
                log.info(f'Banning {player} on {server}.')
                await sendCmd(self.loop, server, f'ban {player}')
                log.info(f'Unwhitelisting {player} on {server}.')
                await sendCmd(self.loop, server, f'whitelist remove {player}')
                msg.append(f'# Banned {player} from {server}.')
            else:
                log.warning(f'Could not ban {player} from {server}.')
                msg.append(f'< Unable to ban {player}, {server} is offline! >')
        await sendMarkdown(ctx, '\n'.join(msg))

    @commands.command(aliases=['pass'])
    @commands.guild_only()
    @permissionNode('relay')
    async def relay(self, ctx, server: str, *, command: str):
        """Relays a command to a servers\' console.

        Takes a servername and a command, in that order.
        """

        msg = ['Command Log', '==========']
        if isUp(server):
            log.info(f'Relaying \"{command}\" to {server}.')
            await sendCmd(self.loop, server, command)
            msg.append(f'# Relayed \"{command}\" to {server}.')
        else:
            log.warning(f'Could not relay \"{command}\" to {server}.')
            msg.append(f'< Unable to relay command, {server} is offline! >')
        await sendMarkdown(ctx, '\n'.join(msg))


def setup(bot):
    if not hasattr(bot, 'servercfg'):
        bot.servercfg = Config(f'{bot.dir}/configs/serverCfgs.json',
                               default=f'{bot.dir}/configs/serverCfgs.json_default',
                               load=True, loop=bot.loop)
    bot.add_cog(ConsoleCmds(bot))


permissionNodes = ['whitelist', 'kick', 'ban', 'relay']
