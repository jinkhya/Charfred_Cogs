import logging
import discord
from discord.ext import commands

log = logging.getLogger('charfred')


class moderation:
    def __init__(self, bot):
        self.bot = bot
        self.dir = bot.dir
        self.loop = bot.loop

    async def on_message(self, message):
        if message.author.id in (self.bot.user.id, self.bot.owner_id):
            return
        if message.guild.id is None:
            return

        if self.bot.cfg['nodes']['spec:moderation'][0]:
            if message.author.status is discord.Status.offline:
                await message.author.send(f'Don\'t be rude! Go online before you post!')
                try:
                    await message.delete()
                except discord.Forbidden:
                    await message.add_reaction('\N{PILE OF POO}')
        else:
            if message.author.status is discord.Status.offline:
                await message.add_reaction('\N{PILE OF POO}')

    @commands.command(aliases=['getthemop', 'cleanup'])
    @commands.guild_only()
    @commands.cooldown(1, 20)
    async def wipe(self, ctx):
        """Wipes up all the poop!

        Or at least most of it...
        """

        async with ctx.typing():
            to_wipe = []
            async for msg in ctx.history():
                if len(msg.reactions) > 0:
                    for react in msg.reactions:
                        if str(react.emoji) == '\N{PILE OF POO}' and react.me:
                            to_wipe.append(msg)
            for msg in to_wipe:
                await msg.remove_reaction('\N{PILE OF POO}', self.bot.user)


def setup(bot):
    bot.add_cog(moderation(bot))


permissionNodes = {
    'spec:moderation': ['Would you like to filter out messages from people who are offline? (their messages will be deleted if possible)\n', False]
}
