from discord.ext import commands
from discord.utils import find
import re
import logging
from utils.config import Config
from utils.discoutils import permission_node, sendmarkdown
from .utils.mcservutils import isUp, sendCmd

log = logging.getLogger('charfred')


class Customs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.servercfg = bot.servercfg
        self.customcmds = Config(
            f'{self.bot.dir}/configs/customCmds.json',
            loop=self.bot.loop,
            load=True
        )

    @commands.group(invoke_without_command=True, aliases=['cc'])
    @permission_node(f'{__name__}.custom')
    async def custom(self, ctx):
        """Custom Minecraft server commands commands.

        This returns a list of all currently registered custom console
        commands, if no subcommand was given.
        """

        msg = ['Custom Console Commands Library',
               '===============================']
        for name, cmd in self.customcmds.items():
            msg.append(name)
            msg.append(f"\t{cmd['role']}")
            msg.append(f"\t{cmd['cmd']}\n")
        msg = '\n'.join(msg)
        await sendmarkdown(ctx, msg)

    @custom.command(aliases=['edit', 'modify'])
    @permission_node(f'{__name__}.customEdit')
    async def add(self, ctx, name: str, minRole: str, *, cmd: str):
        """Add a custom command to the library.

        Takes a name to save the command under,
        a minimum required Discord role, and
        a variable length console command.
        Anything after the name parameter becomes
        part of the command.
        If you want your command to take arguments,
        you can place them anywhere in the command,
        by putting {} in their place.
        These will later be replaced in order from
        left to right, with the given arguments,
        when the command is ran.
        """
        self.customcmds[name] = {'role': minRole, 'cmd': cmd}
        log.info(f'Added \"{cmd}\" to custom console commands library as \"{name}\".')
        await sendmarkdown(ctx, f'# Added \"{cmd}\" to your custom console commands'
                           ' library as \"{name}\".')
        await self.customcmds.save()

    @custom.command(aliases=['delete'])
    @permission_node(f'{__name__}.customEdit')
    async def remove(self, ctx, name: str):
        """Remove a custom command from the library.

        Takes the name the command to delete is
        registered under.
        """
        del self.customcmds[name]
        log.info(f'Removed \"{name}\" from your custom console commands library.')
        await sendmarkdown(ctx, f'# Removed \"{name}\" from your custom console commands library.')
        await self.customcmds.save()

    @custom.command(aliases=['execute', 'exec'])
    async def run(self, ctx, cmd: str, server: str, *args: str):
        """Runs a custom command from the library.

        Takes the name the command to run is registered
        under, a name of the target server and a variable
        number of arguments, which will be applied, if the
        custom command supports them.
        Target server can also be the \'all\' keyword,
        to iterate over all known servers, sending the
        command to each one.
        """
        msg = ['Command Log', '===========']
        if cmd not in self.customcmds:
            log.warning(f'\"{cmd}\" is undefined!')
            await sendmarkdown(ctx, f'< \"{cmd}\" is undefined! >')
            return
        _cmd = self.customcmds[cmd]['cmd']
        minRole = self.customcmds[cmd]['role']
        minRole = find(lambda r: r.name == minRole, ctx.guild.roles)
        if ctx.author.top_role < minRole:  # TODO: Don't even allow ranks that don't exist!
            log.warning(f'User is missing permissions for {cmd}!')
            await sendmarkdown(ctx, f'< You are not permitted to run {cmd}! >\n'
                               f'< Minimum required role is {str(minRole)}. >')
            return
        log.info(f'Required: {str(minRole)}; User has: {str(ctx.author.top_role)}')

        if args:
            _cmd = _cmd.format(*args)
        msg.append(f'# Executing \"{_cmd}\"...')

        if re.match('^all$', server, flags=re.I):
            for server in self.servercfg['servers']:
                if isUp(server):
                    log.info(f'Executing \"{cmd}\" on {server}.')
                    await sendCmd(self.loop, server, _cmd)
                    msg.append(f'# on {server};')
                else:
                    log.warning(f'Could not execute \"{cmd}\", {server} is offline!')
                    msg.append(f'< {server} is offline! >')
        else:
            if isUp(server):
                log.info(f'Executing \"{cmd}\" on {server}.')
                await sendCmd(self.loop, server, _cmd)
                msg.append(f'# on {server};')
            else:
                log.warning(f'Could not execute \"{cmd}\", {server} is offline!')
                msg.append(f'< {server} is offline! >')
        await sendmarkdown(ctx, '\n'.join(msg))


def setup(bot):
    permission_nodes = ['custom', 'customEdit']
    bot.register_nodes([f'{__name__}.{node}' for node in permission_nodes])
    bot.add_cog(Customs(bot))
