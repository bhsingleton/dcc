import os
import re
import sys
import ctypes
import subprocess

from collections import namedtuple
from importlib import util as importutils
from . import stringutils
from .. import DCC, __application__

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__requirement_regex__ = re.compile(r'^([a-zA-Z0-9\._-]+)(?:\s?)([~>=,<]+)(?:\s?)([0-9\.]+)$')


Requirement = namedtuple('Requirement', ('name', 'operator', 'version'))


def getPythonInterpreter(**kwargs):
    """
    Returns the python interpreter for this DCC platform.

    :type executable: str
    :rtype: str
    """

    # Evaluate system executable
    #
    executable = os.path.abspath(kwargs.get('executable', sys.executable))
    directory, filename = os.path.split(executable)

    strings = os.path.splitext(filename)
    name, extension = strings[0].lower(), strings[1].lower()

    if name == 'python' and extension == '.exe':

        return executable

    # Evaluate current DCC application
    #
    if __application__ == DCC.MAX:

        if name in ('3dsmax', '3dsmaxbatch') and extension == '.exe':

            return os.path.join(directory, 'Python', 'python.exe')

        elif name == '3dsmaxpy' and extension == '.exe':

            return os.path.join(directory, '3dsmaxpy.exe')

        else:

            raise RuntimeError(f'getPythonInterpreter() Unable to locate interpreter relative to: {executable}')

    elif __application__ == DCC.MAYA:

        if name in ('maya', 'mayabatch', 'mayapy') and extension == '.exe':

            return os.path.join(directory, 'mayapy.exe')

        else:

            raise RuntimeError(f'getPythonInterpreter() Unable to locate interpreter relative to: {executable}')

    else:

        raise RuntimeError(f'getPythonInterpreter() Unable to locate interpreter relative to: {executable}')


def isAdministrator():
    """
    Evaluates if the user has administrative privileges.

    :rtype: bool
    """

    return bool(ctypes.windll.shell32.IsUserAnAdmin())


def requiresAdministrator(**kwargs):
    """
    Evaluates if administrator privileges are required based on the supplied commandline arguments.

    :type executable: str
    :type user: bool
    :type target: bool
    :rtype: bool
    """

    # Check if user flag exists
    #
    user = kwargs.get('user', False)

    if user:

        return False

    # Check if a target path exists
    #
    target = kwargs.get('target', None)
    hasTarget = not stringutils.isNullOrEmpty(target)

    if hasTarget:

        return not os.access(target, os.R_OK | os.W_OK | os.X_OK)

    else:

        return not isAdministrator()  # TODO: Find a better fallback solution!


def hasPackage(name):
    """
    Evaluates if the supplied package name exists.

    :rtype: bool
    """

    spec = importutils.find_spec(name)
    exists = spec is not None

    return exists


def hasPip():
    """
    Evaluates if PIP exists.

    :rtype: bool
    """

    return hasPackage('pip')


def ensurePip(**kwargs):
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
    upgrade = kwargs.get('upgrade', False)

    if exists and not upgrade:

        log.debug('PIP has already been installed!')
        return True

    # Compose arguments
    #
    user = kwargs.get('user', False)
    args = ['-m', 'ensurepip']

    if user:

        args.append('--user')

    if upgrade:

        args.append('--upgrade')

    # Evaluate user's administrative privileges
    #
    executable = getPythonInterpreter(**kwargs)
    requiresAdmin = requiresAdministrator(**kwargs)

    exitCode = None

    if requiresAdmin:

        # Try and install PIP via shell
        #
        parameters = ' '.join(args)

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
        try:

            exitCode = subprocess.check_call([executable, *args])

        except subprocess.CalledProcessError as exception:

            log.error(exception.output)
            exitCode = exception.returncode

        finally:

            return bool(exitCode == 0)


def installPackage(name, **kwargs):
    """
    Installs the specified python package.

    :type name: str
    :type upgrade: bool
    :type user: bool
    :rtype: bool
    """
    
    # Ensure PIP is installed
    #
    executable = getPythonInterpreter(**kwargs)
    success = ensurePip(executable=executable)

    if not success:

        log.warning('Unable to ensure PIP!')
        return False
    
    # Compose arguments
    #
    target = kwargs.get('target', None)
    hasTarget = not stringutils.isNullOrEmpty(target)
    user = kwargs.get('user', False)
    upgrade = kwargs.get('upgrade', False)
    
    args = ['-m', 'pip', 'install', name]

    if hasTarget:

        args.extend(('--target', target))

    elif user:

        args.append('--user')

    else:

        pass

    if upgrade:

        args.append('--upgrade')
    
    # Evaluate user permissions
    #
    log.info(f'Installing python package: {name}')
    requiresAdmin = requiresAdministrator(**kwargs)

    exitCode = None

    if requiresAdmin:

        # Try and install package via shell
        #
        parameters = ' '.join(args)

        try:

            exitCode = ctypes.windll.shell32.ShellExecuteW(None, 'runas', executable, parameters, None, 1)

        except subprocess.CalledProcessError as exception:

            log.error(exception.output)
            exitCode = exception.returncode

        finally:

            return bool(exitCode >= 32)

    else:

        # Try and install package via subprocess
        #
        try:

            exitCode = subprocess.check_call([executable, *args])

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


def installRequirements(filePath, **kwargs):
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
    executable = getPythonInterpreter(**kwargs)
    success = ensurePip(executable=executable)

    if not success:

        log.warning('Unable to ensure PIP for requirements!')
        return False

    # Compose arguments
    #
    target = kwargs.get('target', None)
    hasTarget = not stringutils.isNullOrEmpty(target)
    user = kwargs.get('user', False)
    upgrade = kwargs.get('upgrade', False)

    args = ['-m', 'pip', 'install', '-r', filePath]

    if hasTarget:

        args.extend(('--target', target))

    elif user:

        args.append('--user')

    else:

        pass

    if upgrade:

        args.append('--upgrade')

    # Evaluate user permissions
    #
    log.info(f'Installing python requirements: {filePath}')
    requiresAdmin = requiresAdministrator(**kwargs)

    exitCode = None

    if requiresAdmin:
        
        # Try and install requirements via shell
        #
        parameters = ' '.join(args)

        try:

            exitCode = ctypes.windll.shell32.ShellExecuteW(None, 'runas', executable, parameters, None, 1)

        except subprocess.CalledProcessError as exception:

            log.error(exception.output)
            exitCode = exception.returncode

        finally:

            return bool(exitCode >= 32)

    else:
        
        # Try and install requirements via subprocess
        #
        try:

            exitCode = subprocess.check_call([executable, *args])

        except subprocess.CalledProcessError as exception:

            log.error(exception.output)
            exitCode = exception.returncode

        finally:

            return bool(exitCode == 0)
