from discord.ext import commands
import re
import logging
from utils.config import Config
from utils.discoutils import permissionNode, sendReply_codeblocked, sendReply
from .utils.mcservutils import isUp, sendCmd

log = logging.getLogger('charfred')


class customs:
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
    @commands.guild_only()
    @permissionNode('custom')
    async def custom(self, ctx):
        """Custom Minecraft server commands operations.

        Without a subcommand, this returns a list
        of all currently registered custom console
        commands.
        """

        if ctx.invoked_subcommand is None:
            msg = ['Custom Console Commands Library',
                   '===============================']
            for name, cmd in self.customcmds.items():
                msg.append(name)
                msg.append(f'\t{cmd}')
            msg = '\n'.join(msg)
            await sendReply_codeblocked(ctx, msg, encoding='json')

    @custom.command(aliases=['edit', 'modify'])
    @permissionNode('customEdit')
    async def add(self, ctx, name: str, *, cmd: str):
        """Add a custom command to the library.

        Takes a name to save the command under
        and a variable length console command.
        Anything after the name parameter becomes
        part of the command.
        If you want your command to take arguments,
        you can place them anywhere in the command,
        by putting \{\} in their place.
        These will later be replaced in order from
        left to right, with the given arguments,
        when the command is ran.
        """
        self.customcmds[name] = cmd
        log.info(f'Added \"{cmd}\" to your custom console commands library.')
        await sendReply(ctx, f'Added \"{cmd}\" to your custom console commands library.')
        await self.customcmds.save()

    @custom.command(aliases=['delete'])
    @permissionNode('customEdit')
    async def remove(self, ctx, name: str):
        """Remove a custom command from the library.

        Takes the name the command to delete is
        registered under.
        """
        del self.customcmds[name]
        log.info(f'Removed \"{name}\" from your custom console commands library.')
        await sendReply(ctx, f'Removed \"{name}\" from your custom console commands library.')
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
            msg.append(f'[Error]: \"{cmd}\" is undefined!')
            return
        _cmd = self.customcmds[cmd]
        if re.match('^all$', server, flags=re.I):
            for server in self.servercfg['servers']:
                if isUp(server):
                    log.info(f'Executing \"{cmd}\" on {server}.')
                    if args:
                        await sendCmd(self.loop, server, _cmd.format(*args))
                    else:
                        await sendCmd(self.loop, server, _cmd)
                    msg.append(f'[Info] Executed \"{cmd}\" on {server}.')
                else:
                    log.warning(f'Could not execute \"{cmd}\", {server} is offline!')
                    msg.append(f'[Error]: Unable to execute \"{cmd}\", {server}, is offline!')
        else:
            if isUp(server):
                log.info(f'Executing \"{cmd}\" on {server}.')
                if args:
                    await sendCmd(self.loop, server, _cmd.format(*args))
                else:
                    await sendCmd(self.loop, server, _cmd)
                msg.append(f'[Info] Executed \"{cmd}\" on {server}.')
            else:
                log.warning(f'Could not execute \"{cmd}\", {server} is offline!')
                msg.append(f'[Error]: Unable to execute \"{cmd}\", {server}, is offline!')
        await sendReply_codeblocked(ctx, '\n'.join(msg))


def setup(bot):
    bot.add_cog(customs(bot))


permissionNodes = ['custom', 'customEdit']
