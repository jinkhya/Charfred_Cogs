import discord
import logging
from ttldict import TTLOrderedDict
from discord.ext import commands
from ..utils.discoutils import has_permission, sendEmbed
from ..utils.mcuser import MCUser, mojException

log = logging.getLogger('charfred')


class stalkCmds:
    def __init__(self, bot):
        self.bot = bot
        self.stalkdict = TTLOrderedDict(default_ttl=60)

    @commands.command(aliases=['backgroundcheck', 'check', 'creep'])
    @commands.cooldown(60, 60)
    @has_permission('stalk')
    async def stalk(self, ctx, lookupName: str):
        """Fetch some incriminatory information on a player.

        Gets info such as UUID, past-names and avatar.
        """

        log.info(f'Stalking \"{lookupName}\"...')
        if lookupName in self.stalkdict.keys():
            mcU = self.stalkdict.get(lookupName)
            log.info(f'Retrieved data for \"{lookupName}\" from cache.')
        else:
            try:
                mcU = await MCUser.create(lookupName, self.bot.session)
                self.stalkdict[lookupName] = mcU
            except mojException as e:
                log.warning(e.message)
                reportCard = discord.Embed(
                    title=e.message,
                    type="rich",
                    colour=discord.Colour.dark_red()
                )
                await sendEmbed(ctx, reportCard)
                return
        reportCard = discord.Embed(
            title="__Subject: " + mcU.name + "__",
            url='http://mcbouncer.com/u/' + mcU.uuid,
            type='rich',
            color=0x0080c0
        )
        reportCard.set_author(
            name="Classified Report",
            url='https://google.com/search?q=minecraft%20' +
            mcU.name,
            icon_url='https://crafatar.com/avatars/' +
            mcU.uuid
        )
        reportCard.set_thumbnail(
            url='https://crafatar.com/renders/head/' +
            mcU.uuid + '?overlay'
        )
        reportCard.add_field(
            name="Current Name:",
            value="```\n" + mcU.name + "\n```"
        )
        reportCard.add_field(
            name="UUID:",
            value="```\n" + mcU.uuid + "\n```"
        )
        reportCard.add_field(
            name="Links!:",
            value=f"[MCBans](https://www.mcbans.com/player/{mcU.name}/)\n"
            f"[Statistic](https://minecraft-statistic.net/en/player/{mcU.name}.html)\n"
            f"[MCBouncer](http://mcbouncer.com/u/{mcU.uuid})\n"
            f"[Google](https://google.com/search?q=minecraft%20{mcU.name})"
        )
        if mcU.demo:
            reportCard.add_field(
                name="__**DEMO ACCOUNT**__",
                value="Watch out for this!"
            )
        if mcU.legacy:
            reportCard.add_field(
                name="*Legacy*",
                value="This guy is old-school!"
            )
        if mcU.nameHistory is not None:
            pastNames = ', '.join(mcU.nameHistory)
            reportCard.add_field(name="Past names:",
                                 value=pastNames)
        reportCard.set_footer(text="Report compiled by Agent Charfred")
        log.info('Sent Reportcard.')
        await sendEmbed(ctx, reportCard)


def setup(bot):
    bot.add_cog(stalkCmds(bot))


permissionNodes = ['stalk']
