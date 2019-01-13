import logging
from discord.utils import find

log = logging.getLogger('charfred')


class Annoyances:
    def __init__(self, bot):
        self.bot = bot

    async def on_member_update(self, before, after):
        """Kellas support safeguard."""

        if len(before.roles) == len(after.roles):
            return
        log.info('Kella has a new role!')
        if len(before.roles) > len(after.roles):
            roles = list(set(before.roles) - set(after.roles))
            supportrole = find(lambda r: r.name == 'support', roles)
            if supportrole:
                log.warning('Kella is NOT supportive!')
                await after.remove_roles(supportrole)
                jin = await self.bot.get_user(167341028091756544)
                await jin.send('BAD JIN! 🖕')


def setup(bot):
    bot.add_cog(Annoyances(bot))
