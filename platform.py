import sys
import os

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def getExecutable():
    """
    Returns the executable this session is running from.

    :rtype: str
    """

    return sys.executable


def getApplication():
    """
    Returns the name of the application this session is running from.

    :rtype: str
    """

    return os.path.splitext(os.path.split(getExecutable())[1])[0]

