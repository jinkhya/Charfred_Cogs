#!/usr/bin/env python

import psutil
import asyncio
import logging
from .discoutils import sendReply_codeblocked

log = logging.getLogger('charfred')


def isUp(server):
    """Checks whether a server is up, by searching for its process."""
    for process in psutil.process_iter(attrs=['cmdline']):
        if f'{server}.jar' in process.info['cmdline']:
            return True
    return False


def termProc(server):
    """Finds the process for a given server and terminates it."""
    for process in psutil.process_iter(attrs=['cmdline']):
        if f'{server}.jar' in process.info['cmdline']:
            process.terminate()
            return True
    return False


async def sendCmd(loop, server, cmd):
    """Passes a given command string to a server's screen."""
    log.info(f'Sending \"{cmd}\" to {server}.')
    proc = await asyncio.create_subprocess_exec(
        'screen', '-S', server, '-X', 'stuff', f'{cmd}\r',
        loop=loop
    )
    await proc.wait()


async def sendCmds(loop, server, *cmds):
    """Passes all given command strings to a server's screen."""
    for cmd in cmds:
        log.info(f'Sending \"{cmd}\" to {server}.')
        proc = await asyncio.create_subprocess_exec(
            'screen', '-S', server, '-X', 'stuff', f'{cmd}\r',
            loop=loop
        )
        await proc.wait()


async def exec_cmd(loop, ctx, *args):
    """Runs a given (shell) command and returns the output"""
    async with ctx.typing():
        proc = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            loop=loop
        )
        print('Executing:', args)
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            print('Finished:', args)
        else:
            print('Failed:', args)
        return stdout.decode().strip()


async def exec_cmd_reply(loop, ctx, *args):
    """Runs a given (shell) command and sends the output
    as a codeblocked message to the appropriate commandchannel"""
    async with ctx.typing():
        proc = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE,
            loop=loop
        )
        print('Executing:', args)
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            print('Finished:', args)
        else:
            print('Failed:', args)
        msg = stdout.decode().strip()
        await sendReply_codeblocked(ctx, msg)
