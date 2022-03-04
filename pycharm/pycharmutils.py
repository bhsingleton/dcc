import os
import sys

from six.moves import winreg

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__port__ = 4434


def findPycharm():
    """
    Returns the location of pycharm from the user's machine.
    To do this we have to use the registry editor...

    :rtype: str
    """

    # Open local machine registry
    #
    registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    key = winreg.OpenKey(registry, r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall')

    if key is None:

        return ''

    # Iterate through sub keys
    #
    numSubKeys = winreg.QueryInfoKey(key)[0]

    for i in range(numSubKeys):

        try:

            # Open sub key
            #
            enumKey = winreg.EnumKey(key, i)
            subKey = winreg.OpenKey(key, enumKey)

            displayName = winreg.QueryValueEx(subKey, "DisplayName")[0]

            # Check if this is pycharm
            #
            if displayName.startswith('JetBrains PyCharm') or displayName.startswith('PyCharm'):

                return winreg.QueryValueEx(subKey, "InstallLocation")[0]

            else:

                continue

        except EnvironmentError:

            continue

    return ''


def setupDebugger():
    """
    Opens a command port between maya and pycharm.
    Please note at this time the egg file needs to be extracted for this to work!

    :rtype: None
    """

    # Check if debugging can be enabled
    #
    pycharmDir = findPycharm()

    if not os.path.exists(pycharmDir):

        log.info('Unable to locate pycharm to setup debugger!')
        return

    # Append helpers to system path
    #
    debugEgg = os.path.join(pycharmDir, r'debug-eggs\pydevd-pycharm')

    if debugEgg not in sys.path:

        log.info('Appending "%s" to python paths!' % debugEgg)
        sys.path.append(debugEgg)


def startDebugger(*args, **kwargs):
    """
    Runtime method used to connect maya to pycharm from remote debugging.
    See the following for details: https://github.com/juggernate/PyCharm-Maya-Debugging

    :rtype: None
    """

    try:

        import pydevd

        pydevd.stoptrace()
        pydevd.settrace('localhost', port=__port__, stdoutToServer=True, stderrToServer=True, suspend=False)

    except ImportError:

        log.warning('Unable to remote debug without a copy of Pycharm installed!')


def stopDebugger(*args, **kwargs):
    """
    Runtime method used to disconnect maya from pycharm for remote debugging.

    :rtype: None
    """

    try:

        import pydevd
        pydevd.stoptrace()

    except ImportError:

        log.warning('Unable to remote debug without a copy of Pycharm installed!')
