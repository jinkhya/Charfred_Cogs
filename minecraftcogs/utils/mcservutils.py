import psutil
import asyncio
import logging
import os
import re
import glob
import functools

log = logging.getLogger('charfred')


def isUp(server):
    """Checks whether a server is up, by searching for its process.

    Returns a boolean indicating whether the server is up or not.
    """
    for process in psutil.process_iter(attrs=['cmdline']):
        if f'{server}.jar' in process.info['cmdline']:
            return True
    return False


def termProc(server):
    """Finds the process for a given server and terminates it.

    Returns a boolean indicating whether the process was terminated.
    """
    for process in psutil.process_iter(attrs=['cmdline']):
        if f'{server}.jar' in process.info['cmdline']:
            toKill = process.children()
            toKill.append(process)
            for p in toKill:
                p.terminate()
            gone, alive = psutil.wait_procs(toKill, timeout=3)
            for p in alive:
                p.kill()
            gone, alive = psutil.wait_procs(toKill, timeout=3)
            if not alive:
                return True
            else:
                return False
    return False


def getProc(server):
    """Finds and returns the Process object for a given server."""

    for process in psutil.process_iter(attrs=['cmdline']):
        if f'{server}.jar' in process.info['cmdline']:
            return process
    return None


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


async def serverStart(server, servercfg, loop):
    """Start a given Minecraft server."""

    cwd = os.getcwd()
    os.chdir(servercfg['serverspath'] + f'/{server}')
    proc = await asyncio.create_subprocess_exec(
        'screen', '-h', '5000', '-dmS', server,
        *(servercfg['servers'][server]['invocation']).split(), 'nogui',
        loop=loop
    )
    await proc.wait()
    os.chdir(cwd)


async def serverStop(server, loop):
    """Stop a given Minecraft server."""

    await sendCmds(
        loop,
        server,
        'title @a times 20 40 20',
        'title @a title {\"text\":\"STOPPING SERVER NOW\", \"bold\":true, \"italic\":true}',
        'broadcast Stopping now!',
        'save-all',
    )
    await asyncio.sleep(5, loop=loop)
    await sendCmd(
        loop,
        server,
        'stop'
    )


async def serverTerminate(server, loop):
    """Terminates a serverprocess forcefully.

    Returns a boolean indicating whether the process,
    was successfully terminated.
    """
    _termProc = functools.partial(termProc, server)
    killed = await loop.run_in_executor(None, _termProc)
    return killed


async def serverStatus(servers, loop):
    """Queries the status of one or all known Minecraft servers.

    Returns a list of status messages for all queried servers.
    """
    def getStatus():
        statuses = []
        for s in servers:
            if isUp(s):
                log.info(f'{s} is running.')
                statuses.append(f'# {s} is running.')
            else:
                log.info(f'{s} is not running.')
                statuses.append(f'< {s} is not running! >')
        statuses = '\n'.join(statuses)
        return statuses

    statuses = await loop.run_in_executor(None, getStatus)
    return statuses


def buildCountdownSteps(cntd):
    """Builds and returns a list of countdown step triples,
    consisting of 'time to announce', 'time in seconds to wait',
    and 'the timeunit to announce'.
    """

    countpat = re.compile(
        '(?P<time>\d+)((?P<minutes>[m].*)|(?P<seconds>[s].*))', flags=re.I
    )
    steps = []
    for i, step in enumerate(cntd):
        s = countpat.search(step)
        if s.group('minutes'):
            time = int(s.group('time'))
            secs = time * 60
            unit = 'minutes'
        else:
            time = int(s.group('time'))
            secs = time
            unit = 'seconds'
        if i + 1 > len(cntd) - 1:
            steps.append((time, secs, unit))
        else:
            st = countpat.search(cntd[i + 1])
            if st.group('minutes'):
                t = int(st.group('time')) * 60
            else:
                t = int(st.group('time'))
            steps.append((time, secs - t, unit))
    return steps


def getcrashreport(server, serverspath, nthlast: int=0):
    """Retrieves the filename of the nth latest crashreport
    for a given server, in addition to the date of last modification.
    """

    rpath = sorted(
        glob.iglob(serverspath + f'/{server}/crash-reports/*'),
        key=os.path.getmtime,
        reverse=True
    )[nthlast]
    return rpath, os.path.getmtime(rpath)


def parsereport(rpath):
    """Retrieves and parses a crashreport given its path.
    Returns a list containing crashreport flavor text,
    time, description, short stacktrace and affected level
    section, if available, in a ready to print format.
    """

    with open(rpath, 'r') as r:
        # Discard until flavortext is found.
        while True:
            l = r.readline()
            if not l:
                break
            if l.startswith('// '):
                flavor = l
                break
        # Read in Time and Description lines.
        r.readline()
        crashtime = r.readline()
        desc = r.readline()
        r.readline()
        # Read in short stacktrace.
        strace = []
        while True:
            l = r.readline()
            if not l or l == '\n':
                break
            strace.append(l)
        # Look for relevant sections in remaining report.
        block = []
        level = []
        phase = []
        while True:
            l = r.readline()
            if not l:
                break
            if l.startswith('-- Block'):
                block.append('# Block entity being ticked:\n')
                while True:
                    l = r.readline()
                    if not l or l == '\n' or l == 'Stacktrace:\n':
                        break
                    block.append(l)
            if l.startswith('-- Affected'):
                level.append('# Affected level:\n')
                while True:
                    l = r.readline()
                    if not l or l == '\n':
                        break
                    level.append(l)
            if l.startswith('-- Sponge'):
                phase.append('# Sponge PhaseTracker:\n')
                r.readline()
                r.readline()
                while True:
                    l = r.readline()
                    if not l or l == '\n' or l.startswith('/***'):
                        break
                    phase.append(l)
                if len(phase) <= 1:
                    phase = []

    return crashtime, desc, strace, flavor, level, block, phase


def formatreport(rpath, crashtime, desc, flavor, strace, *sections):
    """Format given report sections into discord messegable chunks."""

    report = []
    report.append('> ' + os.path.basename(rpath) + '\n')
    report.append('# ' + flavor + '\n')
    report.append('# ' + crashtime)
    report.append('# ' + desc + '\n')
    report.append('# Shortened Stacktrace:\n')
    report.extend(strace[:4])
    report = ''.join(report)

    chunks = [report]

    chunk = ''
    for s in sections:
        siter = iter(s)
        while len(chunk) < 2000:
            try:
                l = next(siter)
            except StopIteration:
                break
            if (len(l) + len(chunk)) < 2000:
                chunk += l
            else:
                chunks.append(chunk)
                chunk = l
    else:
        chunks.append(chunk)

    return chunks
