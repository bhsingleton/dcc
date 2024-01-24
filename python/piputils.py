import os
import re
import sys
import stat
import subprocess

from collections import namedtuple

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__regex__ = re.compile(r'^([a-zA-Z0-9\._-]+)(?:\s?)([~>=,<]+)(?:\s?)([0-9\.]+)$')


Requirement = namedtuple('Requirement', ('name', 'operator', 'version'))


def getRequirements(filePath):
    """
    Returns any option variables from the supplied requirements file.

    :type filePath: str
    :rtype: Tuple[List[Requirement], Dict[str, Any]]
    """

    # Iterate through file
    #
    requirements = []
    options = {}

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
            line = line.replace('#', '').lstrip().rstrip()

            results = __regex__.findall(line)
            numResults = len(results)

            if numResults != 1:

                continue

            # Append requirement
            #
            name, operator, version = results[0]

            if isComment:

                options[name] = version

            else:

                requirements.append(Requirement(name=name, operator=operator, version=version))

    return requirements, options


def updateRequirements(filePath, requirements, options, **kwargs):
    """
    Updates the specified path with the supplied requirements and options.

    :type filePath: str
    :type requirements: List[Requirement]
    :type options: Dict[str, Any]
    :key lastModified: float
    :rtype: None
    """

    # Check if file is read-only
    #
    isReadOnly = not os.access(filePath, os.R_OK | os.W_OK)

    if isReadOnly:

        os.chmod(filePath, stat.S_IWRITE)

    # Update requirements file
    #
    with open(filePath, 'w') as file:

        lines = [f'# {key}=={value}\n' for (key, value) in options.items()]
        file.writelines(lines)

        lines = [f'{requirement.name}{requirement.operator}{requirement.version}\n' for requirement in requirements]
        file.writelines(lines)

    # Check if last-modified time was supplied
    #
    lastModified = kwargs.get('lastModified', None)

    if isinstance(lastModified, float):

        os.utime(filePath, (lastModified, lastModified))


def installRequirements(filePath, target=None, executable=None):
    """
    Installs the supplied requirements file into the target directory.
    If no target is specified then the requirements directory is used instead.

    :type filePath: str
    :type target: str
    :type executable: str
    :rtype: bool
    """

    # Check if an executable was supplied
    #
    if executable is None:

        executable = sys.executable

    # Check if a target was supplied
    #
    args = None

    if target is not None:

        args = [executable, '-m', 'pip', 'install', '-r', filePath, '--target', target, '--upgrade']

    else:

        args = [executable, '-m', 'pip', 'install', '-r', filePath, '--user', '--upgrade']

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
