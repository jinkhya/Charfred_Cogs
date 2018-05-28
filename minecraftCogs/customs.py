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

    @commands.group(aliases=['cc'])
    @commands.guild_only()
    @permissionNode('custom')
    async def custom(self, ctx):
        if ctx.invoked_subcommand is None and ctx.subcommand_passed is not None:
            if ctx.subcommand_passed in self.customcmds and len(ctx.args) >= 2:
                log.info(f'Invoking custom command: \"{ctx.args[0]}\".')
                ctx.invoke(
                    self.run, ctx.subcommand_passed, ctx.args[1:]
                )

    @custom.command(aliases=['edit', 'modify'])
    @permissionNode('customEdit')
    async def add(self, ctx, name: str, *, cmd: str):
        self.customcmds[name] = cmd
        log.info(f'Added \"{cmd}\" to your custom console commands library.')
        await sendReply(ctx, f'Added \"{cmd}\" to your custom console commands library.')
        await self.customcmds.save()

    @custom.command(aliases=['delete'])
    @permissionNode('customEdit')
    async def remove(self, ctx, name: str):
        del self.customcmds[name]
        log.info(f'Removed \"{name}\" from your custom console commands library.')
        await sendReply(ctx, f'Removed \"{name}\" from your custom console commands library.')
        await self.customcmds.save()

    @custom.command(name='list')
    async def _list(self, ctx):
        msg = ['Custom Console Commands Library',
               '===============================']
        for name, cmd in self.customcmds.items():
            msg.append(name)
            msg.append(f'\t{cmd}')
        msg = '\n'.join(msg)
        await sendReply_codeblocked(ctx, msg, encoding='json')

    @custom.command(aliases=['execute', 'exec'])
    async def run(self, ctx, cmd: str, server: str, *args: str):
        msg = ['Command Log', '===========']
        if cmd not in self.customcmds:
            log.warning(f'\"{cmd}\" is undefined!')
            msg.append(f'[Error]: \"{cmd}\" is undefined!')
            return
        _cmd = self.customcmds[cmd]
        if re.match('all$', server, flags=re.I):
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
