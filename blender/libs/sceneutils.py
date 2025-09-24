import bpy
import sys
import os

from ...python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def isBatchMode():
    """
    Evaluates if the scene is running in batch mode.

    :rtype: bool
    """

    # Check if binary path is valid
    # If so, then we're currently in background mode!
    #
    if stringutils.isNullOrEmpty(bpy.app.binary_path):

        return True

    # Check if python interpreter is derived from blender
    #
    pythonHome = os.path.normpath(os.path.dirname(sys.executable))
    binaryPath = os.path.normpath(os.path.dirname(bpy.app.binary_path))

    return not pythonHome.startswith(binaryPath)