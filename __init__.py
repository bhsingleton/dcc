import os
import sys

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def rollback():
    """
    Removes all modules, derived from the dcc package, from the system module.
    This will force any future imported modules to recompile.

    :rtype: None
    """

    # Iterate through modules
    # Use this package to differentiate modules
    #
    directory = os.path.dirname(os.path.abspath(__file__))
    moduleNames = set(sys.modules.keys())

    for moduleName in moduleNames:

        # Check if module has file attribute
        #
        module = sys.modules[moduleName]

        if not hasattr(module, '__file__'):

            continue

        # Check for none type
        #
        if module.__file__ is None:

            continue

        # Check if module falls under python paths
        #
        filePath = os.path.abspath(module.__file__)

        if filePath.startswith(directory):

            log.info('Rolling back module: %s' % module)
            del sys.modules[moduleName]


def resetNotifies():
    """
    Removes all notifications from the notify function set.

    :rtype: None
    """

    from dcc import fnnotify
    fnnotify.FnNotify.clear()


def restart():
    """
    Restarts the entire DCC package.
    This method should only be used by developers when iterating on changes.

    :rtype: None
    """

    resetNotifies()
    rollback()
