import os
import re
import sys
import ctypes
import subprocess

from collections import namedtuple
from importlib import util as importutils
from .. import DCC, __application__

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__requirement_regex__ = re.compile(r'^([a-zA-Z0-9\._-]+)(?:\s?)([~>=,<]+)(?:\s?)([0-9\.]+)$')


Requirement = namedtuple('Requirement', ('name', 'operator', 'version'))


def getPythonInterpreter():
    """
    Returns the python interpreter for this DCC platform.

    :rtype: str
    """

    # Evaluate system executable
    #
    executable = os.path.abspath(sys.executable)
    directory, filename = os.path.split(executable)

    name = os.path.splitext(filename)[0].lower()

    if name == 'python':

        return executable

    # Evaluate current DCC application
    #
    if __application__ == DCC.MAX:

        if name in ('3dsmax', '3dsmaxbatch'):

            return os.path.join(directory, 'Python', 'python.exe')

        elif name == '3dsmaxpy':

            return os.path.join(directory, '3dsmaxpy.exe')

        else:

            raise RuntimeError(f'getPythonInterpreter() Unable to locate interpreter relative to: {executable}')

    elif __application__ == DCC.MAYA:

        if name in ('maya', 'mayabatch', 'mayapy'):

            return os.path.join(directory, 'mayapy.exe')

        else:

            raise RuntimeError(f'getPythonInterpreter() Unable to locate interpreter relative to: {executable}')

    else:

        raise RuntimeError(f'getPythonInterpreter() Unable to locate interpreter relative to: {executable}')


def ensurePythonInterpreter(executable):
    """
    Ensures that a valid Python interpreter is returned.

    :type executable: Union[str, None]
    :rtype: str
    """

    # Evaluate path type
    #
    if not isinstance(executable, str):

        return getPythonInterpreter()

    # Check if path is valid
    #
    isExecutable = executable.lower().endswith('.exe')
    exists = os.path.isfile(executable) and isExecutable

    if exists:

        return executable

    else:

        return getPythonInterpreter()


def isAdmin():
    """
    Evaluates if the user has administrative privileges.

    :rtype: bool
    """

    return ctypes.windll.shell32.IsUserAnAdmin()


def hasPip():
    """
    Evaluates if PIP exists.

    :rtype: bool
    """

    spec = importutils.find_spec('pip')
    exists = spec is not None

    return exists


def ensurePip(user=False, upgrade=False, executable=None):
    """
    Ensures that PIP is installed.

    :type user: bool
    :type upgrade: bool
    :type executable: str
    :rtype: bool
    """

    # Check if PIP exists
    #
    exists = hasPip()

    if exists and not upgrade:

        log.debug('PIP has already been installed!')
        return True

    # Evaluate user's administrative privileges
    #
    executable = ensurePythonInterpreter(executable)
    requiresAdmin = not user and not isAdmin()

    if requiresAdmin:

        # Try and install PIP via shell
        #
        args = ['-m', 'ensurepip', '--upgrade'] if user else ['-m', 'ensurepip']
        parameters = ' '.join(args)

        exitCode = None

        try:

            exitCode = ctypes.windll.shell32.ShellExecuteW(None, 'runas', executable, parameters, None, 1)

        except subprocess.CalledProcessError as exception:

            log.error(exception.output)
            exitCode = exception.returncode

        finally:

            return bool(exitCode >= 32)

    else:

        # Try and install PIP via subprocess
        #
        args = ['-m', 'ensurepip']
        if user: args.append('--user')
        if upgrade: args.append('--upgrade')

        exitCode = None

        try:

            exitCode = subprocess.check_call(args)

        except subprocess.CalledProcessError as exception:

            log.error(exception.output)
            exitCode = exception.returncode

        finally:

            return bool(exitCode == 0)


def getRequirements(filePath):
    """
    Returns any option variables from the supplied requirements file.

    :type filePath: str
    :rtype: List[Requirement]
    """

    # Iterate through file
    #
    requirements = []

    with open(filePath, 'r') as file:

        while True:

            # Check if line is empty
            #
            line = file.readline()

            if not line:

                break

            # Parse line for requirement
            #
            isComment = line.startswith('#')

            if isComment:

                continue

            # Check if line is valid
            #
            results = __requirement_regex__.findall(line)
            isValid = len(results) == 1

            if isValid:

                name, operator, version = results[0]
                requirements.append(Requirement(name=name, operator=operator, version=version))

            else:

                continue

    return requirements


def installRequirements(filePath, target=None, upgrade=True, executable=None):
    """
    Installs the supplied requirements file into the target directory.
    If no target is specified then the requirements directory is used instead.

    :type filePath: str
    :type target: str
    :type upgrade: bool
    :type executable: str
    :rtype: bool
    """

    # Ensure PIP is installed
    #
    executable = ensurePythonInterpreter(executable)
    success = ensurePip(executable=executable)

    if not success:

        log.warning('Unable to install PIP for requirements!')
        return False

    # Check if a target was supplied
    #
    args = None

    if target is not None:

        args = [executable, '-m', 'pip', 'install', '-r', filePath, '--target', target]

    else:

        args = [executable, '-m', 'pip', 'install', '-r', filePath, '--user']

    # Check if upgrade is required
    #
    if upgrade:

        args.append('--upgrade')

    # Try and install requirements
    #
    exitCode = None

    try:

        exitCode = subprocess.check_call(args)

    except subprocess.CalledProcessError as exception:

        log.error(exception.output)
        exitCode = exception.returncode

    finally:

        return bool(exitCode == 0)
