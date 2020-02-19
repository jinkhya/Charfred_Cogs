import logging

from pint import UnitRegistry, DimensionalityError, DefinitionSyntaxError

from discord.ext import commands
from utils.discoutils import sendmarkdown

log = logging.getLogger('charfred')


class UnitConverter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ur = UnitRegistry()
        self.ur.autoconvert_offset_to_baseunit = True

    @commands.group()
    async def convert(self, ctx):
        """Converts stuff.

        Just measurements for now.
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
            sendmarkdown(ctx, f'< Error! >'
                         f'< {e} >')
        except DefinitionSyntaxError as e:
            log.warning(e)
            sendmarkdown(ctx, f'< Unable to parse {measurement}! >'
                         f'< {e} >')
        else:
            sendmarkdown(ctx, f'# {measurement} is (roughly) {out}')


def setup(bot):
    bot.add_cog(UnitConverter(bot))
