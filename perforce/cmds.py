"""
Low level python module used for issuing perforce commands to the server.
By default each command will generate a repository based on the user's perforce environment settings.
Each command is capable of augmenting the environment settings to support clients with different streams.
"""
import os

from P4 import P4Exception
from . import createAdapter

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def logResults(results):
    """
    Outputs the supplied results object to the logger.

    :type results: Union[list, dict]
    :rtype: None
    """

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


def logErrors(errors):
    """
    Outputs the supplied errors object to the logger.

    :type errors: Union[list, dict]
    :rtype: None
    """

    # Check value type
    #
    if isinstance(errors, (list, tuple)):

        for error in errors:

            logResults(error)

    elif isinstance(errors, dict):

        for (key, value) in errors.items():

            log.info(value)

    else:

        pass


def files(*args, **kwargs):
    """
    Lists files from the depot tree based on the supplied paths.
    To perform a depot search use the following syntax: //{depot}/.../*.fbx
    To perform a client search used the following syntax: //{client}/.../*.fbx
    To limit a get request to a specific directory use: //{depot}/*

    :rtype: list[dict]
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)

    try:

        p4.connect()
        specs = p4.run('files', '-e', *args)
        p4.disconnect()

        return specs

    except P4Exception:

        logErrors(p4.errors)


def dirs(*args, **kwargs):
    """
    Lists directories from the depot tree based on the supplied paths.

    :rtype: list[dict]
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)

    try:

        p4.connect()
        specs = p4.run('dirs', '-C', *args)
        p4.disconnect()

        return specs

    except P4Exception:

        logErrors(p4.errors)


def where(*args, **kwargs):
    """
    Lists all path variations for the supplied list of paths.
    Each indexed dictionary contains the following keys: 'clientFile', 'depotFile' and 'path'.

    :rtype: list[dict[str:str]]
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)

    try:

        p4.connect()
        fileSpecs = p4.run('where', *args)
        p4.disconnect()

        return fileSpecs

    except P4Exception:

        logErrors(p4.errors)


def sync(*args, **kwargs):
    """
    Syncs the supplied depot files from perforce.
    This method excepts depot files so be sure to convert local paths using where.

    :rtype: dict
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)

    try:

        # Sync on files
        #
        p4.connect()
        results = p4.run('sync', '-f', *args)
        p4.disconnect()

        # Display perforce feedback
        #
        logResults(results)
        return results

    except P4Exception:

        logErrors(p4.errors)


def add(*args, **kwargs):
    """
    Marks a local file to add to the server.
    All file paths should be supplied as arguments!

    :rtype: dict
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)

    try:

        # Check out files
        #
        p4.connect()
        results = p4.run('add', '-c', kwargs.get('changelist', 'default'), *args)
        p4.disconnect()

        # Display perforce feedback
        #
        logResults(results)
        return results

    except P4Exception:

        logErrors(p4.errors)


def edit(*args, **kwargs):
    """
    Checks out a file for editing.
    All file paths should be supplied as arguments!

    :rtype: dict
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)

    try:

        # Check out files
        #
        p4.connect()
        results = p4.run('edit', '-c', kwargs.get('changelist', 'default'), *args)
        p4.disconnect()

        # Display perforce feedback
        #
        logResults(results)
        return results

    except P4Exception:

        logErrors(p4.errors)


def delete(*args, **kwargs):
    """
    Marks a file for delete from the server.
    All file paths should be supplied as arguments!

    :rtype: dict
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)

    try:

        # Check out files
        #
        p4.connect()
        results = p4.run('delete', '-c', kwargs.get('changelist', 'default'), *args)
        p4.disconnect()

        # Display perforce feedback
        #
        logResults(results)
        return results

    except P4Exception:

        logErrors(p4.errors)


def revert(*args, **kwargs):
    """
    Reverts any changes made to the supplied files.

    :rtype: list[dict]
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)

    try:

        # Revert files
        #
        p4.connect()
        results = p4.run('revert', '-a', *args)
        p4.disconnect()

        # Display perforce feedback
        #
        logResults(results)
        return results

    except P4Exception:

        logErrors(p4.errors)


def clients(*args, **kwargs):
    """
    Collects ALL clients specs associated with the supplied user.

    :rtype: list[dict]
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)

    try:

        # Connect to server
        #
        p4.connect()

        # Collect clients associated with user
        #
        host = kwargs.get('host', None)
        specs = None

        if host is not None:

            specs = [x for x in p4.iterate_clients(['-u', p4.user]) if x['Host'] == host]

        else:

            specs = [x for x in p4.iterate_clients(['-u', p4.user])]

        # Disconnect from server
        #
        p4.disconnect()
        return specs

    except P4Exception:

        logErrors(p4.errors)


def client(*args, **kwargs):
    """
    Fetches client specs from the server using the supplied name.

    :rtype: dict
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)

    try:

        p4.connect()
        specs = p4.fetch_client(args[0])
        p4.disconnect()

        return specs

    except P4Exception:

        logErrors(p4.errors)


def depots(*args, **kwargs):
    """
    Collects ALL depot specs from the server.

    :rtype: list[dict]
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)

    try:

        p4.connect()
        specs = [x for x in p4.iterate_depots()]
        p4.disconnect()

        return specs

    except P4Exception:

        logErrors(p4.errors)


def depot(*args, **kwargs):
    """
    Fetches depot specs from the server using the supplied name.

    :rtype: dict
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)

    try:

        p4.connect()
        specs = p4.fetch_depot(args[0])
        p4.disconnect()

        return specs

    except P4Exception:

        logErrors(p4.errors)


def changes(*args, **kwargs):
    """
    Returns a list of changelist specs from the server associated with the supplied client.
    If no client is supplied then the environment variables are used instead.
    An additional status keyword can be supplied to limit the types of changelists returned.

    :keyword client: str
    :keyword status: str
    :rtype: list[dict]
    """

    # Create repository
    #
    p4 = createAdapter(**kwargs)

    try:

        # Sync on files
        #
        p4.connect()
        results = p4.run('changes', '-c', kwargs.get('client', os.environ['P4CLIENT']), '-s', kwargs.get('status', 'pending'))
        p4.disconnect()

        return results

    except P4Exception:

        logErrors(p4.errors)
