from discord.ext import commands
from discord import Color
import logging
import os
import tarfile
from shutil import rmtree
from utils.config import Config
from utils.flipbooks import Flipbook
from utils.discoutils import permissionNode, sendMarkdown, promptConfirm
from .utils.mcservutils import isUp

log = logging.getLogger('charfred')


class ServerBackups:
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.servercfg = bot.servercfg

    @commands.group()
    @commands.guild_only()
    @permissionNode('backup')
    async def backup(self, ctx):
        """Minecraft server backup operations."""

        if ctx.invoked_subcommand is None:
            pass

    @backup.command(aliases=['listAll'])
    async def list(self, ctx, server: str):
        """List available backups for a specified server."""

        if server not in self.servercfg['servers']:
            log.warning(f'{server} has been misspelled or not configured!')
            await sendMarkdown(ctx, f'< {server} has been misspelled or not configured! >')
            return
        bpath = self.servercfg['backupspath']
        availablebackups = [archive for archive in os.listdir(f'{bpath}/{server}')
                            if os.path.isfile(f'{bpath}/{server}/{archive}') and
                            archive.endswith('.tar.gz')]
        availablebackups.sort()
        backupsbook = Flipbook(ctx, availablebackups, entries_per_page=8,
                               title=f'Backups for {server}', color=Color.blurple())
        await backupsbook.flip()

    @backup.group()
    @permissionNode('applyBackup')
    async def apply(self, ctx):
        """Backup application operations."""

        if ctx.invoked_subcommand is None:
            pass

    def getbackupfile(self, server, part):
        bpath = self.servercfg['backupspath']
        backup = [file for file in os.listdir(f'{bpath}/{server}')
                  if os.path.isfile(f'{bpath}/{server}/{file}') and
                  file.endswith('.tar.gz') and part in file]
        if len(backup) > 1:
            return None
        else:
            return f'{bpath}/{server}/{backup[0]}'

    @apply.command()
    async def full(self, ctx, server: str, backup: str):
        """Applies a full world backup.

        All world files currently in place will be overwritten.

        The 'backup' argument takes the filename for the backup
        to be used, NOT the path to it!;
        However you do not need to put in the whole file name,
        any unique part of the file name will suffice,
        such as the datetime stamp of it.
        """

        backupfile = self.getbackupfile(server, backup)
        if backupfile is None:
            log.warning(f'{backup} did not match any backups for {server}!')
            await sendMarkdown(ctx, f'< {backup} did not match any backups for {server}! >')
            return
        log.info(f'Preparing for full backup application using {backupfile}!')
        await sendMarkdown(ctx, f'Using {backupfile}')
        r, _, _ = await promptConfirm(ctx, 'Would you like to proceed?')
        if r:
            log.info('Confirmed!')
            if isUp(server):
                log.warning(f'{server} still up, cannot proceed!')
                await sendMarkdown(ctx, f'{server} is still up, cannot proceed!')
                return
            serverpath = self.servercfg['serverspath']
            worldpath = f'{serverpath}/{server}/world'
            try:
                log.info(f'Deleting {worldpath}')
                rmtree(worldpath)
            except Exception as e:
                log.error(e + '\nBackup application failed!')
                return
            else:
                log.info(f'{worldpath} deleted!')
                await sendMarkdown(ctx, 'This next step might take some time...')

                def extracthelper():
                    with tarfile.open(backupfile, 'r:gz') as tf:
                        tf.extractall(f'{serverpath}/{server}/')

                await self.loop.run_in_executor(None, extracthelper)
                log.info('World folder extracted from backup and placed!')
                await sendMarkdown(ctx, 'World folder replaced, job done!')
        else:
            log.info('Aborted!')

    @apply.command()
    async def partial(self, ctx, server: str, backup: str, *regions):
        """Applies a partial world backup,
        replacing only specified regions.

        All specified region files currently in place will be
        overwritten.

        The 'backup' argument takes the filename for the backup
        to be used, NOT the path to it!;
        However you do not need to put in the whole file name,
        any unique part of the file name will suffice,
        such as the datetime stamp of it.

        The 'regions' argument takes one or many region file names;
        These need to be full filenames, such as 'r.1.1.mca'.
        """

        backupfile = self.getbackupfile(server, backup)
        if backupfile is None:
            log.warning(f'{backup} did not match any backups for {server}!')
            await sendMarkdown(ctx, f'< {backup} did not match any backups for {server}! >')
            return
        log.info(f'Preparing for partial backup application using {backupfile}!')
        await sendMarkdown(ctx, f'Using {backupfile}')
        log.info('Regions to be extracted:')
        for r in regions:
            log.info(r)
        await sendMarkdown(ctx, 'Regions that will be extracted:\n' +
                           '\n'.join(regions))
        r, _, _ = await promptConfirm(ctx, 'Would you like to proceed?')
        if r:
            log.info('Confirmed!')
            if isUp(server):
                log.warning(f'{server} still up, cannot proceed!')
                await sendMarkdown(ctx, f'{server} is still up, cannot proceed!')
                return
            serverpath = self.servercfg['serverspath']
            regionpath = f'{serverpath}/{server}/world/region'
            deleted = []
            failed = False
            for r in regions:
                try:
                    os.remove(f'{regionpath}/{r}')
                    log.info(f'Deleting {regionpath}/{r}')
                except Exception as e:
                    log.error(e + f'\nDeletion of {r} failed!')
                    failed = True
                    await sendMarkdown(ctx, f'Deletion of {r} failed!')
                else:
                    deleted.append(r)
            if failed:
                await sendMarkdown(ctx, 'There were some errors encountered '
                                   'during deletion!\nThe following regions '
                                   'were deleted successfully however:\n' +
                                   '\n'.join(deleted) + '\nPartial backup '
                                   'application will continue, but only the '
                                   'successfully deleted regions will be '
                                   'replaced, please investigate why the '
                                   'other regions failed to be deleted '
                                   'manually!')
            else:
                await sendMarkdown(ctx, 'All specified regions successfully '
                                   'deleted! Continuing with replacement...')

            def extracthelper():
                with tarfile.open(backupfile, 'r:gz') as tf:
                    for r in regions:
                        tf.extract(f'world/region/{r}', path=f'{serverpath}/{server}')

            await self.loop.run_in_executor(None, extracthelper)
            log.info('Regions extracted from backup and placed!')
            await sendMarkdown(ctx, 'Regions replaced, job done!')
        else:
            log.info('Aborted!')


def setup(bot):
    if not hasattr(bot, 'servercfg'):
        bot.servercfg = Config(f'{bot.dir}/configs/serverCfgs.json',
                               default=f'{bot.dir}/configs/serverCfgs.json_default',
                               load=True, loop=bot.loop)
    bot.add_cog(ServerBackups(bot))


permissionNodes = ['backup', 'applyBackup']
