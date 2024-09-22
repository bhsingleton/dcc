import os
import re
import sys
import stat
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


__file__ = re.compile(r'(?:[a-zA-Z]:[\\\/])(?:[a-zA-Z0-9_\-]+[\\\/])*([a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+)')
__directory__ = re.compile(r'(?:[a-zA-Z]:[\\\/])(?:[a-zA-Z0-9_\-]+[\\\/])*')


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


def isFileLike(string):
    """
    Evaluates if the supplied string represents a file path.
    No validation is done to test whether the file exists or not!

    :rtype: None
    """

    return __file__.match(string) is not None


def ensureDirectory(path):
    """
    Ensures that the supplied directory exists.

    :type path: str
    :rtype: None
    """

    # Check if this is a file
    # If so, then get the parent directory
    #
    if isFileLike(path):

        path = os.path.dirname(path)

    # Ensure trailing directories exist
    #
    if not os.path.exists(path):

        os.makedirs(path)


def isReadOnly(path):
    """
    Evaluates if the specified path is read-only.

    :type path: str
    :rtype: bool
    """

    if os.path.isfile(path):

        return not os.access(path, os.R_OK | os.W_OK)

    else:

        return False


def ensureWritable(path):
    """
    Ensures the specified path is writable.

    :type path: str
    :rtype: None
    """

    if os.path.isfile(path) and isReadOnly(path):

        os.chmod(path, stat.S_IWRITE)


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

    return path.startswith('$') or (path.startswith('%') and path.endswith('%'))


def makePathRelativeTo(path, directory, force=False):
    """
    Returns a path relative to the supplied directory.

    :type path: str
    :type directory: str
    :type force: bool
    :rtype: str
    """

    # Check for empty strings
    #
    if stringutils.isNullOrEmpty(path) or stringutils.isNullOrEmpty(directory):

        return ''

    # Check if path is relative to directory
    #
    path = os.path.normpath(os.path.expandvars(path))
    directory = os.path.normpath(os.path.expandvars(directory))

    if isPathRelativeTo(path, directory) or force:

        relativePath = os.path.relpath(path, directory)
        log.info(f'Relativizing path: {path} > {relativePath}')

        return relativePath

    else:

        log.warning(f'Unable to make: {path}, relative to: {directory}')
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

            log.info(f'Absolutifying path: {path} > {absolutePath}')
            return absolutePath

        else:

            continue

    # Notify user
    #
    log.warning(f'Unable to make path absolute: {path}')
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
        log.info(f'Variablizing path: {absolutePath} > {variablePath}')

        return variablePath

    else:

        log.warning(f'Unable to make path variable: {path}')
        return path
