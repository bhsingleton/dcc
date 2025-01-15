import os
import sys

from enum import IntEnum


class DCC(IntEnum):
    """
    Enum class of all supported DCC applications.
    """

    UNKNOWN = -1
    MAX = 0
    MAYA = 1


def detectApplication(executable):
    """
    Returns the DCC application in use.
    TODO: Come up with a more elegant solution for detecting the active DCC application!

    :type executable: str
    :rtype: DCC
    """

    # Evaluate supplied argument
    #
    if not isinstance(executable, str):

        raise TypeError(f'detectApplication() expects a str ({type(executable).__name__} given)!')

    # Evaluate current executable path
    #
    segments = executable.split(os.sep)

    for segment in segments:

        # Evaluate path segment
        #
        if segment.startswith('3ds Max'):

            return DCC.MAX

        elif segment.startswith('Maya'):

            return DCC.MAYA

        else:

            continue

    return DCC.UNKNOWN


__executable__ = os.path.normpath(sys.executable)
__application__ = detectApplication(__executable__)
