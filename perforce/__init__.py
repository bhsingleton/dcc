import os
import platform
import subprocess
import getpass
import socket

from ..python import importutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


CREATION_FLAGS = 0x08000000
PING_FLAG = '-n' if platform.system().lower() == 'windows' else '-c'


P4 = importutils.tryImport('P4', __locals__=locals(), __globals__=globals())


def createAdapter(**kwargs):
    """
    Returns a P4 adapter configured for the current user.
    If no keyword arguments are supplied then environment variables are queried.

    :key user: The username of the account.
    :key port: The server address to access.
    :key host: The host name to filter values.
    :key client: The client name associated with the user.
    :rtype: P4
    """

    # Define new instance of P4
    #
    p4 = P4()

    # Check if a user was supplied
    #
    user = kwargs.get('user', None)

    if user is None:

        user = os.environ.get('P4USER', getpass.getuser())

    # Check if a port was supplied
    #
    port = kwargs.get('port', None)

    if port is None:

        port = os.environ.get('P4PORT', '1666')

    # Check if a host was supplied
    #
    host = kwargs.get('host', None)

    if host is None:

        host = os.environ.get('P4HOST', socket.gethostname())

    # Check if a client was supplied
    #
    client = kwargs.get('client', None)

    if client is None:

        client = os.environ.get('P4CLIENT', '')

    # Check if a password was supplied
    #
    password = kwargs.get('password', None)

    if password is None:

        password = os.environ.get('P4PASSWD', '')

    # Cast values to str before assigning
    #
    p4.user = str(user)
    p4.port = str(port)
    p4.host = str(host)
    p4.client = str(client)
    p4.password = str(password)

    return p4


def isConnected():
    """
    Evaluates if the perforce server is available.

    :rtype: bool
    """

    host = os.environ.get('P4PORT', 'localhost:1666').split(':')[0]
    command = 'ping {flag} 1 {host}'.format(flag=PING_FLAG, host=host)

    return subprocess.call(command, creationflags=CREATION_FLAGS) == 0
