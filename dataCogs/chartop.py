import os
import psutil
from discord.ext import commands
from utils.discoutils import permissionNode


class chartop:
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop

    def getCharInfo():
        charProc = psutil.Process(os.getpid())
        with charProc.oneshot():
            cCPUPerc = charProc.cpu_percent(interval=2)
            cMemInfo = charProc.memory_info()
            cMemPerc = charProc.memory_percent()
        return cCPUPerc, cMemInfo, cMemPerc

    @commands.command(invoke_without_command=True, aliases=['chartop'])
    @permissionNode('chartop')
    async def top(self, ctx):
        """Get info on Charfred\'s process!"""

        cpuPerc, mem, memPerc = await self.loop.run_in_executor(None, self.getCharInfo)

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
