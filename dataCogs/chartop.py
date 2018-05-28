import os
import functools
import psutil
from discord.ext import commands
from utils.discoutils import permissionNode


class chartop:
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop

    def getCharInfo(pid):
        proc = psutil.Process(pid)
        with proc.oneshot():
            cpuPerc = proc.cpu_percent(interval=2)
            memInfo = proc.memory_info()
            memPerc = proc.memory_percent()
        return cpuPerc, memInfo, memPerc

    @commands.command(invoke_without_command=True, aliases=['chartop'])
    @permissionNode('chartop')
    async def top(self, ctx):
        """Get info on Charfred\'s process!"""

        charPid = os.getpid()
        charInfo = functools.partial(self.getCharInfo, charPid)
        cpuPerc, mem, memPerc = await self.loop.run_in_executor(None, charInfo)

        msg = [' Charfred Process Information ',
               '==============================',
               f'CPU Percentage:      {cpuPerc}',
               '-----------------------------',
               f'Resident Set Size:   {mem.rss}',
               f'Virtual Memory Size: {mem.vms}',
               '-----------------------------',
               f'Memory Percentage:   {memPerc}']
        msg = '\n'.join(msg)
        await ctx.send(f'```{msg}```')


def setup(bot):
    bot.add_cog(chartop(bot))


permissionNodes = ['chartop']
