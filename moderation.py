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
                    await message.add_reaction(':poop:')
        else:
            if message.author.status is discord.Status.offline:
                await message.add_reaction(':poop:')


def setup(bot):
    bot.add_cog(moderation(bot))


permissionNodes = {
    'spec:moderation': ['Would you like to filter out messages from people who are offline? (their messages will be deleted if possible)\n', False]
}
