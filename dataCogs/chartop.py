import os
import functools
import psutil
from discord.ext import commands
from utils.discoutils import permissionNode, send


class Chartop:
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop

    def getProcInfo(self, pid):
        proc = psutil.Process(pid)
        with proc.oneshot():
            cpuPerc = proc.cpu_percent(interval=3)
            memInfo = proc.memory_info()
            memPerc = proc.memory_percent()
        return cpuPerc, memInfo, memPerc

    def humanReadable(self, n):
        symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
        prefix = {}
        for i, s in enumerate(symbols):
            prefix[s] = 1 << (i + 1) * 10
        for s in reversed(symbols):
            if n >= prefix[s]:
                value = float(n) / prefix[s]
                return '%.1f%s' % (value, s)
        return "%sB" % n

    @commands.command(invoke_without_command=True, aliases=['chartop'])
    @permissionNode('chartop')
    async def top(self, ctx):
        """Get info on Charfred\'s process!"""

        charPid = os.getpid()
        charInfo = functools.partial(self.getProcInfo, charPid)
        cpuPerc, mem, memPerc = await self.loop.run_in_executor(None, charInfo)
        memPerc = '%.2f' % memPerc

        msg = [' Charfred Process Information ',
               '==============================',
               f'CPU Percentage:      {cpuPerc}%',
               ' ',
               f'Resident Set Size:   {self.humanReadable(mem.rss)}',
               f'Virtual Memory Size: {self.humanReadable(mem.vms)}',
               ' ',
               f'Memory Percentage:   {memPerc}']
        msg = '\n'.join(msg)
        await send(ctx, f'```{msg}```')


def setup(bot):
    bot.add_cog(Chartop(bot))


permissionNodes = ['chartop']
