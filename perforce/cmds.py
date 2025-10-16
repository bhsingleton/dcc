"""
Low level python module used for issuing perforce commands to the server.
By default, each command will generate a repository based on the user's perforce environment settings.
Each command is capable of augmenting the environment settings to support clients with different streams.
"""
import os

from time import time
from collections import namedtuple
from . import createAdapter
from ..python import importutils

P4 = importutils.tryImport('P4', __locals__=locals(), __globals__=globals())
ConnectionStatus = namedtuple('ConnectionStatus', ('connected', 'expiration', 'timestamp'))

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__connections__ = {}  # type: dict[str, ConnectionStatus]


def logResults(results, **kwargs):
    """
    Outputs the supplied results object to the logger.

    :type results: Union[list, dict]
    :rtype: None
    """
    
    # Check if quite was enabled
    #
    quiet = kwargs.get('quiet', False)
    
    if quiet:
        
        return
    
    # Check value type
    #
    if isinstance(results, (list, tuple)):

        for result in results:

            logResults(result)

    elif isinstance(results, dict):

        for (key, value) in results.items():

            log.info(value)

    else:

        pass


def logErrors(errors, **kwargs):
    """
    Outputs the supplied errors object to the logger.

    :type errors: Union[list, dict]
    :rtype: None
    """

    # Check if quite was enabled
    #
    quiet = kwargs.get('quiet', False)

    if quiet:
        
        return

    # Check value type
    #
    if isinstance(errors, (list, tuple)):

        for error in errors:

            logErrors(error)

    elif isinstance(errors, dict):

        for (key, value) in errors.items():

            log.error(value)

    else:

        pass


def files(*args, **kwargs):
    """
    Lists files from the depot tree based on the supplied paths.
    To perform a depot search use the following syntax: //{depot}/.../*.fbx
    To perform a client search use the following syntax: //{client}/.../*.fbx
    To limit a get request to a specific directory use: //{depot}/*

    :rtype: List[dict]
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)
    specs = []

    try:

        p4.connect()
        specs = p4.run('files', '-e', *args)

    except P4.P4Exception:

        logErrors(p4.errors, **kwargs)

    finally:

        p4.disconnect()
        return specs


def dirs(*args, **kwargs):
    """
    Lists directories from the depot tree based on the supplied paths.

    :rtype: List[dict]
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)
    specs = []

    try:

        p4.connect()
        specs = p4.run('dirs', '-C', *args)

    except P4.P4Exception:

        logErrors(p4.errors, **kwargs)

    finally:

        p4.disconnect()
        return specs


def where(*args, **kwargs):
    """
    Lists all path variations for the supplied list of paths.
    Each indexed dictionary contains the following keys: 'clientFile', 'depotFile' and 'path'.

    :rtype: List[Dict[str, str]]
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)
    specs = []

    try:

        p4.connect()
        specs = p4.run('where', *args)

    except P4.P4Exception:

        logErrors(p4.errors, **kwargs)

    finally:

        p4.disconnect()
        return specs


def fstat(*args, **kwargs):
    """
    Returns file stats for each supplied file.

    :rtype: List[dict]
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)
    specs = []

    try:

        p4.connect()
        specs = p4.run('fstat', *args)

    except P4.P4Exception:

        logErrors(p4.errors, **kwargs)

    finally:

        p4.disconnect()
        return specs


def sync(*args, **kwargs):
    """
    Syncs the supplied files from perforce.

    :key flush: bool
    :rtype: List[dict]
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)
    flush = kwargs.get('flush', False)

    specs = []

    try:

        p4.connect()

        if flush:

            specs = p4.run('sync', '-k', *args)

        else:

            specs = p4.run('sync', '-f', *args)

        logResults(specs, **kwargs)

    except P4.P4Exception:

        logErrors(p4.errors, **kwargs)

    finally:

        p4.disconnect()
        return specs


def add(*args, **kwargs):
    """
    Marks the supplied files to be added to the depot.
    All file paths should be supplied as arguments!

    :key changelist: int
    :rtype: dict
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)
    changelist = kwargs.get('changelist', 'default')

    specs = []

    try:

        p4.connect()
        specs = p4.run('add', '-c', changelist, *args)
        logResults(specs, **kwargs)

    except P4.P4Exception:

        logErrors(p4.errors, **kwargs)

    finally:

        p4.disconnect()
        return specs


def edit(*args, **kwargs):
    """
    Checks out the supplied files for editing.
    All file paths should be supplied as arguments!

    :key changelist: int
    :rtype: dict
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)
    changelist = kwargs.get('changelist', 'default')

    specs = []

    try:

        p4.connect()
        specs = p4.run('edit', '-c', changelist, *args)
        logResults(specs, **kwargs)

    except P4.P4Exception:

        logErrors(p4.errors, **kwargs)

    finally:

        p4.disconnect()
        return specs


def move(fromFile, toFile, **kwargs):
    """
    Moves the local file to the new location.

    :type fromFile: str
    :type toFile: str
    :key changelist: int
    :rtype: bool
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)
    changelist = kwargs.get('changelist', 'default')

    success = False

    try:

        p4.connect()
        specs = p4.run('move', '-r', '-c', changelist, fromFile, toFile)
        logResults(specs, **kwargs)

        success = True

    except P4.P4Exception:

        logErrors(p4.errors, **kwargs)

    finally:

        p4.disconnect()
        return success


def delete(*args, **kwargs):
    """
    Marks a file for delete from the server.
    All file paths should be supplied as arguments!

    :rtype: dict
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)
    specs = []

    try:

        p4.connect()
        specs = p4.run('delete', '-c', kwargs.get('changelist', 'default'), *args)
        logResults(specs, **kwargs)

    except P4.P4Exception:

        logErrors(p4.errors, **kwargs)

    finally:

        p4.disconnect()
        return specs


def revert(*args, **kwargs):
    """
    Reverts any changes made to the supplied files.

    :rtype: List[dict]
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)
    specs = []

    try:

        # Revert files
        #
        p4.connect()
        specs = p4.run('revert', '-a', *args)
        logResults(specs, **kwargs)

    except P4.P4Exception:

        logErrors(p4.errors, **kwargs)

    finally:

        p4.disconnect()
        return specs


def clients(*args, **kwargs):
    """
    Collects ALL clients specs associated with the supplied user.

    :rtype: List[dict]
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)
    host = kwargs.get('host', None)

    specs = []

    try:

        # Collect clients associated with user
        #
        p4.connect()

        if host is not None:

            specs = [x for x in p4.iterate_clients(['-u', p4.user]) if x['Host'] == host]

        else:

            specs = [x for x in p4.iterate_clients(['-u', p4.user])]

    except P4.P4Exception:

        logErrors(p4.errors, **kwargs)

    finally:

        p4.disconnect()
        return specs


def client(*args, **kwargs):
    """
    Fetches client specs from the server using the supplied name.

    :rtype: dict
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)
    specs = []

    try:

        p4.connect()
        specs = p4.fetch_client(args[0])

    except P4.P4Exception:

        logErrors(p4.errors, **kwargs)

    finally:

        p4.disconnect()
        return specs


def depots(*args, **kwargs):
    """
    Collects ALL depot specs from the server.

    :rtype: List[dict]
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)
    specs = []

    try:

        p4.connect()
        specs = list(p4.iterate_depots())

    except P4.P4Exception:

        logErrors(p4.errors, **kwargs)

    finally:

        p4.disconnect()
        return specs


def depot(*args, **kwargs):
    """
    Fetches depot specs from the server using the supplied name.

    :rtype: dict
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)
    specs = []

    try:

        p4.connect()
        specs = p4.fetch_depot(args[0])

    except P4.P4Exception:

        logErrors(p4.errors, **kwargs)

    finally:

        p4.disconnect()
        return specs


def changes(*args, **kwargs):
    """
    Returns a list of changelist specs from the server associated with the supplied client.
    If no client is supplied then the environment variables are used instead.
    An additional status keyword can be supplied to limit the types of changelists returned.

    :key client: str
    :key status: str
    :rtype: List[dict]
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)
    specs = []

    try:

        p4.connect()
        specs = p4.run('changes', '-c', kwargs.get('client', os.environ['P4CLIENT']), '-s', kwargs.get('status', 'pending'))

    except P4.P4Exception:

        logErrors(p4.errors, **kwargs)

    finally:

        p4.disconnect()
        return specs


def login(password, **kwargs):
    """
    Performs a login for the supplied username and password.

    :type password: str
    :key user: str
    :key port: str
    :rtype: bool
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)
    p4.password = password

    success = False

    try:

        p4.connect()
        specs = p4.run_login()

        success = int(specs[0]['TicketExpiration']) > 0

    except P4.P4Exception:

        logErrors(p4.errors, **kwargs)

    finally:

        p4.disconnect()
        return success


def isConnected(*args, **kwargs):
    """
    Evaluates if the user is connected to P4 and the time left before their session expires.
    The time is returned in seconds!

    :key user: str
    :key port: str
    :rtype: Tuple[bool, int]
    """

    global __connections__

    # Check if connection status exists
    #
    server = os.environ.get('P4PORT', 'localhost:1666')
    status = __connections__.get(server, None)

    if isinstance(status, ConnectionStatus):

        # Evaluate connection status
        #
        if not status.connected:

            del __connections__[server]
            return isConnected(*args, **kwargs)

        # Evaluate expiration time
        # If expired go ahead and repoll the connection
        #
        currentTime = time()
        elapsedTime = currentTime - status.timestamp

        expired = elapsedTime > status.expiration

        if expired:

            del __connections__[server]
            return isConnected(*args, **kwargs)

        else:

            return status.connected, (status.expiration - elapsedTime)

    else:

        # Poll connection status
        #
        p4 = createAdapter(**kwargs)
        currentTime = time()

        connected, expiration = False, 0

        try:

            p4.connect()
            specs = p4.run('login', '-s')

            connected, expiration = p4.connected(), int(specs[0]['TicketExpiration'])
            __connections__[p4.port] = ConnectionStatus(connected, expiration, currentTime)

        except P4.P4Exception:

            logErrors(p4.errors, **kwargs)

        finally:

            p4.disconnect()
            return connected, expiration
