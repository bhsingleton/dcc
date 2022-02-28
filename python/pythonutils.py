import os
import sys
import inspect

from six import iteritems
from six.moves import reload_module

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def filePathToModulePath(filePath):
    """
    Converts a file path into a module path compatible with import statements.

    :type filePath: str
    :rtype: str
    """

    # Normalize file paths
    #
    pythonPaths = [os.path.normpath(x) for x in sys.path]
    filePath = os.path.normpath(os.path.expandvars(filePath))

    if filePath.endswith('__init__.py') or filePath.endswith('__init__.pyc'):

        filePath = os.path.dirname(filePath)

    elif os.path.isfile(filePath):

        filePath, extension = os.path.splitext(filePath)

    else:

        pass

    # Collect paths that are relative
    #
    found = [x for x in pythonPaths if filePath.startswith(x)]
    numFound = len(found)

    if numFound == 0:

        return ''

    # Join strings using module delimiter
    #
    startPath = max(found)
    relativePath = os.path.relpath(filePath, startPath)

    return '.'.join(relativePath.split(os.sep))


def iterPackage(packagePath, forceReload=False):
    """
    Generator method used to iterate through all of the modules from the given package folder.
    If the supplied path does not exist then a type error will be raised!
    The level flag indicates the import operation: -1: best guess, 0: absolute, 1: relative

    :type packagePath: str
    :type forceReload: bool
    :rtype: iter
    """

    # Verify package exists
    #
    if not os.path.exists(packagePath):

        raise TypeError('Unable to locate package: %s' % packagePath)

    # Check if this is a file
    #
    if os.path.isfile(packagePath):

        packagePath = os.path.split(packagePath)[0]

    # Iterate through module files inside package
    #
    for filename in os.listdir(packagePath):

        # Verify this is a module
        #
        moduleName, extension = os.path.splitext(filename)

        if moduleName == '__init__' or extension != '.py':

            continue

        # Try and import module
        #
        filePath = os.path.join(packagePath, '%s.py' % moduleName)

        modulePath = filePathToModulePath(filePath)
        log.info('Attempting to import: "%s" module, from: %s' % (modulePath, filePath))

        try:

            # Import module and check if it should be reloaded
            #
            module = __import__(modulePath, locals=locals(), globals=globals(), fromlist=[filePath], level=0)

            if forceReload:

                log.info('Reloading module...')
                reload_module(module)

            yield module

        except ImportError as exception:

            log.warning(exception)
            continue


def iterModule(module, includeAbstract=False, classFilter=object):
    """
    Generator method used to iterate through all of the classes inside a module.
    An optional subclass filter can be provided to ignore certain types.

    :type module: module
    :type includeAbstract: bool
    :type classFilter: type
    :rtype: iter
    """

    # Iterate through module dictionary
    #
    for (key, item) in iteritems(module.__dict__):

        # Verify this is a class
        #
        if not inspect.isclass(item):

            continue

        # Check if this is a abstract class
        #
        if inspect.isabstract(item) and not includeAbstract:

            continue

        # Check if this is a subclass of abstract node
        #
        if issubclass(item, classFilter) or item is classFilter:

            yield key, item

        else:

            log.debug('Skipping %s class...' % key)


def findClass(className, modulePath):
    """
    Returns the class associated with the given string.
    To improve the results be sure to provide a class name complete with module path.

    :type className: str
    :type modulePath: str
    :rtype: class
    """

    # Check if string is valid
    #
    if len(className) == 0:

        return None

    # Split string using delimiter
    #
    if len(modulePath) == 0:

        return globals().get(className, None)

    else:

        module = sys.modules.get(modulePath, None)
        root = modulePath.split('.', 1)[0]

        if module is None:

            module = __import__(modulePath, locals=locals(), globals=globals(), fromlist=[root], level=0)

        return module.__dict__.get(className, None)
