import logging

from pint import UnitRegistry, DimensionalityError, DefinitionSyntaxError, \
    UndefinedUnitError

from discord import Embed
from discord.ext import commands
from utils.discoutils import sendmarkdown, send

log = logging.getLogger('charfred')


class UnitConverter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session
        self.ur = UnitRegistry()
        self.ur.autoconvert_offset_to_baseunit = True

    @commands.group()
    async def convert(self, ctx):
        """Converts stuff.

        Just measurements and temperatures for now.
        """
        pass

    @convert.command()
    async def units(self, ctx, measurement: str, targetunit: str):
        """Converts a measurement to given target units.

        If you wanna convert temperatures, please use: 'deg' in front of the
        usual letter for your units, such as 'degC' for Celsius or 'degF' for
        Fahrenheit.
        """
        try:
            m = self.ur(measurement)
            out = m.to(targetunit)
        except DimensionalityError as e:
            log.warning(e)
            await sendmarkdown(ctx, f'< Error! >'
                               f'< {e} >')
        except DefinitionSyntaxError as e:
            log.warning(e)
            await sendmarkdown(ctx, f'< Unable to parse {measurement}! >\n'
                               f'< {e} >')
        except UndefinedUnitError as e:
            log.warning(e)
            await sendmarkdown(ctx, '< Sorry, I can only do basic units >\n'
                               '< and temperatures. >')
        else:
            await sendmarkdown(ctx, f'# {measurement} is (roughly) {out}')

    @convert.command()
    async def block(self, ctx, x, z):
        """Convert Minecraft x, z coordinates to chunk and region.
        """

        chunk = f'{(int(x) >> 4)}, {(int(z) >> 4)}'
        regionfile = 'r.' + str((int(x) >> 4) // 32) + '.' + str((int(z) >> 4) // 32) + '.mca'
        await sendmarkdown(ctx, f'# Coordinates {x}, {z} correspond to:\n'
                           f'Chunk coordinates: {chunk}\n\n'
                           f'Region file: {regionfile}')

    @convert.command()
    async def uuid(self, ctx, uuid: str):
        """Convert Minecraft UUID to Userprofile Info.

        More of a 'fetch' than a 'convert', since the data isn't actually
        stored in the UUID, but what the hell...
        """

        async with self.session.get('https://sessionserver.mojang.com/'
                                    f'session/minecraft/profile/{uuid}') as r:
            d = await r.json()
        if not d:
            await sendmarkdown(ctx, '< Couldn\'t get anything, sorry! >')
            return
        card = Embed(
            title=f'__Subject: {d["name"]}__',
            type='rich',
            color=0xe77070
        )
        card.set_thumbnail(
            url=f'https://crafatar.com/renders/body/{uuid}?overlay'
        )
        card.add_field(
            name="Current Name:",
            value="```\n" + d["name"] + "\n```"
        )
        card.add_field(
            name="UUID: (hey, you already know this!)",
            value="```\n" + uuid + "\n```"
        )
        card.set_footer(text="Look at that asshole... ಠ_ಠ")
        await send(ctx, embed=card)


def setup(bot):
    bot.add_cog(UnitConverter(bot))
