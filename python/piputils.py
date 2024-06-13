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
            results = __regex__.findall(line)
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

    # Check if an executable was supplied
    #
    if executable is None:

        executable = sys.executable

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
