import os
import sys
import platform

from string import ascii_uppercase
from ctypes import windll
from fnmatch import fnmatch
from typing import List
from dcc.python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def getDriveLetters():
    """
    Returns all the available drive letters.

    :rtype: List[str]
    """

    # Evaluate user's operating system
    #
    name = platform.system()

    if name != 'Windows':

        return []

    # Collect letters using drive bitmask
    #
    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()

    for letter in ascii_uppercase:

        if bitmask & 1:

            drives.append(letter)

        bitmask >>= 1

    return drives


def isDriveLetter(string):
    """
    Evaluates if the supplied string represents a drive letter.

    :type string: str
    :rtype: bool
    """

    return fnmatch(string, '?:')


def ensureDirectory(path):
    """
    Ensures that the supplied directory exists.

    :type path: str
    :rtype: None
    """

    # Check if this is a file
    # If so, then get the parent directory
    #
    if os.path.isfile(path):

        path = os.path.dirname(path)

    # Ensure directories exist
    #
    os.makedirs(path, exist_ok=True)


def isPathRelative(path):
    """
    Evaluates if the supplied path is relative.

    :type path: str
    :rtype: bool
    """

    # Check for empty strings
    #
    if stringutils.isNullOrEmpty(path):

        return False

    # Check if path starts with drive letter
    #
    segments = os.path.normpath(path).split(os.path.sep)
    numSegments = len(segments)

    if numSegments > 0:

        return not isDriveLetter(segments[0])

    else:

        return False


def isPathRelativeTo(path, directory):
    """
    Evaluates if the supplied path is relative to the given directory.

    :type path: str
    :type directory: str
    :rtype: bool
    """

    # Check for empty strings
    #
    if stringutils.isNullOrEmpty(path) or stringutils.isNullOrEmpty(directory):

        return False

    # Normalize and compare paths
    #
    path = os.path.normpath(os.path.expandvars(path))
    directory = os.path.normpath(os.path.expandvars(directory))

    return os.path.normcase(path).startswith(os.path.normcase(directory))


def isPathVariable(path):
    """
    Evaluates if the supplied path contains an environment variable.

    :type path: str
    :rtype: bool
    """

    return path.startswith(('%', '$'))


def makePathRelativeTo(path, directory):
    """
    Returns a path relative to the supplied directory.

    :type path: str
    :type directory: str
    :rtype: str
    """

    # Check for empty strings
    #
    if stringutils.isNullOrEmpty(path) or stringutils.isNullOrEmpty(directory):

        return ''

    # Check if path is relative to directory
    #
    path = os.path.normpath(path)
    directory = os.path.normpath(os.path.expandvars(directory))

    if isPathRelativeTo(path, directory):

        relativePath = os.path.relpath(path, directory)
        log.info('%s > %s' % (path, relativePath))

        return relativePath

    else:

        log.warning('Cannot make: %s, relative to: %s' % (path, directory))
        return path


def makePathAbsolute(path, paths=None):
    """
    Returns an absolute path using the supplied paths to resolve.

    :type path: str
    :type paths: Union[List[str], None]
    :rtype: str
    """

    # Check for empty strings
    #
    if stringutils.isNullOrEmpty(path):

        return ''

    # Inspect path type
    #
    path = os.path.normpath(os.path.expandvars(path))

    if os.path.isabs(path):

        return path

    # Iterate through paths
    #
    paths = sys.path if stringutils.isNullOrEmpty(paths) else paths

    for directory in paths:

        # Check if directory is valid
        #
        if stringutils.isNullOrEmpty(directory):

            continue

        # Check if combined path is valid
        #
        absolutePath = os.path.join(directory, path)

        if os.path.exists(absolutePath):

            return absolutePath

        else:

            continue

    # Notify user
    #
    log.warning('Unable to make path absolute: %s' % path)
    return path


def makePathVariable(path, variable):
    """
    Converts all the texture paths to variable.
    The supplied variable name must contain a dollar sign!

    :type path: str
    :type variable: str
    :rtype: str
    """

    # Check for empty strings
    #
    if stringutils.isNullOrEmpty(path) or stringutils.isNullOrEmpty(variable):

        return ''

    # Check if path is relative to variable
    #
    absolutePath = makePathAbsolute(path)
    directory = os.path.expandvars(variable)

    if isPathRelativeTo(absolutePath, directory):

        variablePath = os.path.join(variable, os.path.relpath(absolutePath, directory))
        log.debug('%s > %s' % (absolutePath, variablePath))

        return variablePath

    else:

        log.warning('Unable to make path variable: %s' % path)
        return path
