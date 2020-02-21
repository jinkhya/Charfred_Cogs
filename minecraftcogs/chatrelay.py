import logging
import asyncio
from concurrent.futures import CancelledError
from discord.ext import commands
from utils.config import Config
from utils.discoutils import sendmarkdown, permission_node

log = logging.getLogger('charfred')


class ChatRelay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop
        self.server = None
        self.inqueue = asyncio.Queue(maxsize=64, loop=self.loop)
        self.outqueues = {}
        self.inqueue_worker_task = None
        self.relaycfg = Config(f'{bot.dir}/configs/chatrelaycfg.toml',
                               load=True, loop=self.loop)
        if 'ch_to_clients' not in self.relaycfg:
            self.relaycfg['ch_to_clients'] = {}
            self.relaycfg._save()
        if 'client_to_ch' not in self.relaycfg:
            self.relaycfg['client_to_ch'] = {}
            self.relaycfg._save()

    def cog_unload(self):
        if self.server:
            log.info('CR: Closing relay server.')
            self.server.close()
            if self.inqueue_worker_task:
                self.inqueue_worker_task.cancel()
            self.loop.create_task(self.server.wait_closed())

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.server is None:  # Don't even do anything if the server isn't running.
            return

        if message.author.bot or (message.guild is None):
            return

        if message.content and (message.channel.id in self.relaycfg['ch_to_clients']):

            # Check whether the message is a command, as determined
            # by having a valid prefix, and don't proceed if it is.
            prefix = await self.bot.get_prefix(message)
            if isinstance(prefix, str):
                if message.content.startswith(prefix):
                    return
            else:
                try:
                    if message.content.startswith(tuple(prefix)):
                        return
                except TypeError:
                    # If we get here, then the prefixes are borked.
                    raise

            msg_content = message.clean_content.strip().replace('\n', '\\n').replace(':', '\:')
            content = f':MSG::Discord::{message.author.display_name}::{msg_content}::\n'
            for client in self.relaycfg['ch_to_clients'][message.channel.id]:
                try:
                    self.outqueues[client].put_nowait((5, content))
                except KeyError:
                    pass
                except asyncio.QueueFull:
                    pass

    @commands.group(invoke_without_command=True)
    async def chatrelay(self, ctx):
        """Minecraft chat relay commands.

        This returns a list of all Minecraft servers currently
        connected and what channel they're linked to.
        """

        info = ['# Chat Relay Status:']
        if self.server and self.server.sockets:
            info.append('\n# Relay server is online.\n')
        else:
            info.append('\n< Relay server is offline! >\n')
        if self.outqueues:
            info.append('\n# Currently connected clients:')
            for server in self.outqueues:
                info.append(f'- {server}')
        if self.relaycfg['ch_to_clients']:
            info.append('\n# Relay configuration:')
            for channel_id, clients in self.relaycfg['ch_to_clients'].items():
                channel = self.bot.get_channel(channel_id)
                info.append(f'{channel.name if channel else channel_id}:')
                if clients:
                    for client in clients:
                        info.append(f'- {client}')
                    else:
                        info.append('\n')
                else:
                    info.append('> No clients configured.\n')
        if len(info) == 2:
            info.append('> No clients connected, nothing configured.')
        await sendmarkdown(ctx, '\n'.join(info)

    async def incoming_worker(self, reader, client):
        log.info(f'CR-Incoming: Worker for {client} started.')
        try:
            while True:
                data = await reader.readline()
                if not data:
                    log.info(f'CR-Incoming: {client} appears to have disconnected!')
                    break
                try:
                    data = data.decode()
                except UnicodeDecodeError as e:
                    log.info(f'CR-Incoming: {e}')
                    continue
                try:
                    self.inqueue.put_nowait((client, data))
                except asyncio.QueueFull:
                    log.warning(f'CR-Incoming: Incoming queue full, message dropped!')
        except CancelledError:
            raise
        finally:
            log.info(f'CR-Incoming: Worker for {client} exited.')

    async def outgoing_worker(self, writer, client):
        log.info(f'CR-Outgoing: Worker for {client} started.')
        try:
            while True:
                try:
                    _, data = await self.outqueues[client].get()
                except (KeyError, AttributeError):
                    log.error(f'CR-Outgoing: Outqueue for {client} is gone!'
                              ' Connection shutting down!')
                    break
                else:
                    data = data.encode()
                    writer.write(data)
                    await writer.drain()
        except CancelledError:
            raise
        finally:
            log.info(f'CR-Outgoing: Worker for {client} exited.')

    async def connection_handler(self, reader, writer):
        peer = str(writer.get_extra_info("peername"))
        log.info(f'CR-Connection: New connection established with {peer}!')
        handshake = await reader.readline()
        if not handshake:
            log.warning(f'CR-Connection: No handshake from {peer} recieved!'
                        ' Connection shutting down!')
            writer.close()
            return

        handshake = handshake.decode()
        hshk = handshake.split('::')
        if hshk[0] == ':HSHK':
            try:
                client = hshk[1]
            except IndexError:
                log.warning(f'CR-Connection: Invalid handshake: {handshake}')
                client = None
        else:
            log.warning(f'CR-Connection: Invalid handshake: {handshake}')
            client = None

        if client is None:
            log.warning(f'CR-Connection: Using client address as name.')
            client = peer

        self.outqueues[client] = asyncio.PriorityQueue(maxsize=24, loop=self.loop)

        in_task = self.loop.create_task(self.incoming_worker(reader, client))
        out_task = self.loop.create_task(self.outgoing_worker(writer, client))

        _, waiting = await asyncio.wait([in_task, out_task],
                                        return_when=asyncio.FIRST_COMPLETED)
        for task in waiting:
            task.cancel()

        try:
            queue = self.outqueues.pop(client)
        except KeyError:
            pass
        else:
            log.info(f'CR-Connection: Outque for {client} removed with'
                     f' {queue.qsize()} items.')

        writer.close()
        log.info(f'CR-Connection: Connection with {client} closed!')

    async def inqueue_worker(self):
        log.info('CR-Inqueue: Worker started!')
        try:
            while True:
                client, data = await self.inqueue.get()
                if client not in self.relaycfg['client_to_ch']:
                    continue
                data = data.split('::')
                if data[0] == ':MSG':
                    channel = self.bot.get_channel(self.relaycfg['client_to_ch'][client])
                    if not channel:
                        log.warning(f'CR-Inqueue: MSG from {client} could not be relayed!'
                                    ' Registered channel does not exist!')
                        continue
                    await channel.send(f'[**{data[1]}**] {data[2]} : {data[3]}')
        except CancelledError:
            raise
        finally:
            log.info('CR-Inqueue: Worker exited.')

    @chatrelay.command(aliases=['start', 'init'])
    @permission_node(f'{__name__}.chatrelay.init')
    async def initialize(self, ctx, port):
        """This initializes the relay server on the given port,
        allowing connections from Minecraft servers to be established.

        Be sure to also set up at least one channel to relay chat
        to and from, using the 'register' subcommand, otherwise
        chat recieved from clients will just be dropped!
        """

        if self.server:
            log.warning('CR: Server already established!')
            await sendmarkdown(ctx, '> Server already running!')
            return
        self.inqueue_worker_task = self.loop.create_task(self.inqueue_worker())
        self.server = await asyncio.start_server(self.connection_handler, '127.0.0.1', port,
                                                 loop=self.loop)
        log.info('CR: Server started!')
        await sendmarkdown(ctx, '# Server started.')

    @chatrelay.command(aliases=['stop'])
    @permission_node(f'{__name__}.chatrelay.init')
    async def close(self, ctx):
        """This closes the relay server, disconnecting all clients.
        """

        if not self.server:
            log.info('CR: No server to be closed.')
            await sendmarkdown(ctx, '> No server to be closed.')
            return
        self.server.close()
        self.inqueue_worker_task.cancel()
        await self.server.wait_closed()
        log.info('CR: Server closed!')
        self.server = None
        await sendmarkdown(ctx, '# Server closed, all clients disconnected!')

    @chatrelay.command(aliases=['listen'])
    @permission_node(f'{__name__}.chatrelay.register')
    async def register(self, ctx, client: str):
        """Registers a channel to recieve chat from a given client,
        and send chat from the channel to the client.

        The channel you run this in will be the registered channel.

        You can get a list of clients by just running 'chatrelay'
        without a subcommand.
        """

        channel_id = str(ctx.channel.id)
        if client not in self.outqueues:
            await sendmarkdown(ctx, '< Client unknown, registering anyway. >\n'
                               '< Please check if you got the name right,'
                               ' when the client eventually connects. >')
        log.info(f'CR: Registering {ctx.channel.name} for {client}.')

        if client in self.relaycfg['client_to_ch'] and self.relaycfg['client_to_ch'][client]:
            channel = self.bot.get_channel(self.relaycfg['client_to_ch'][client])
            if channel == ctx.channel:
                await sendmarkdown(ctx, f'> {client} is already registered with this channel!')
            else:
                await sendmarkdown(ctx, f'< {client} is already registered with {channel.name}! >\n'
                                   '> A client can only be registered to one channel.\n'
                                   '> Please unregister the other channel first!')
            return
        else:
            self.relaycfg['client_to_ch'][client] = channel_id
            if channel_id in self.relaycfg['ch_to_clients']:
                self.relaycfg['ch_to_clients'][channel_id].append(client)
            else:
                self.relaycfg['ch_to_clients'][channel_id] = [client]

        await self.relaycfg.save()
        await sendmarkdown(ctx, f'# {ctx.channel.name} is now registered for'
                           f' recieving chat from, and sending chat to {client}.')

    @chatrelay.command(aliases=['unlisten'])
    @permission_node(f'{__name__}.chatrelay.register')
    async def unregister(self, ctx, client: str):
        """Unregisters a channel from recieving chat from a given
        client or sending chat to that client.

        The channel you run this in will be the unregistered channel.

        You can get a list of clients by just running 'chatrelay'
        without a subcommand.
        """

        channel_id = str(ctx.channel.id)
        if client not in self.outqueues:
            await sendmarkdown(ctx, '< Client unknown, unregistering anyway. >\n'
                               '< Please check if you got the name right,'
                               ' when the client eventually connects. >')
        log.info(f'CR: Unregistering {ctx.channel.name} for {client}.')

        if client in self.relaycfg['client_to_ch']:
            del self.relaycfg['client_to_ch'][client]

            try:
                self.relaycfg['ch_to_clients'][channel_id].remove(client)
            except ValueError:
                log.critical(f'CR: Relay mapping inconsistency detected!')
                raise
            else:
                await sendmarkdown(ctx, '# This channel will no longer send chat to'
                                   f' or recieve chat from {client}!')
            finally:
                await self.relaycfg.save()
        else:
            await sendmarkdown(ctx, '> This channel is not registered yet.')


def setup(bot):
    bot.add_cog(ChatRelay(bot))
