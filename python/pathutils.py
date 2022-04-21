import os

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

        return ''

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
