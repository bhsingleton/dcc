import os
import site
import sys
import inspect

from collections.abc import Sequence
from . import stringutils, pathutils
from ..vendor.six import string_types
from ..vendor.six.moves import reload_module

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


def iterModules(package, reload=False, __locals__=None, __globals__=None):
    """
    Returns a generator that yields modules from the supplied package.
    If the supplied package is not valid then a type error will be raised!

    :type package: [str, module]
    :type reload: bool
    :type __locals__: dict
    :type __globals__: dict
    :rtype: Iterator[module]
    """

    # Evaluate supplied argument
    #
    packagePath = None

    if inspect.ismodule(package):

        # Get path from package
        #
        packagePath = getattr(package, '__file__', '')

        if os.path.isfile(packagePath):

            packagePath = os.path.dirname(packagePath)

        else:

            raise TypeError(f'iterModules() cannot locate package: {package}')

    elif isinstance(package, string_types):

        # Evaluate path type
        #
        if os.path.isfile(package):

            packagePath = os.path.dirname(package)

        elif os.path.isdir(package):

            packagePath = package

        else:

            raise TypeError(f'iterModules() cannot locate package from: {packagePath}')

    else:

        raise TypeError(f'iterModules() expects a str or module ({type(package).__name__} given)!')

    # Evaluate supplied locals and globals
    #
    if __locals__ is None:

        __locals__ = locals()

    if __globals__ is None:

        __globals__ = globals()

    # Iterate through files inside package
    #
    for filename in os.listdir(packagePath):

        # Verify this is a module
        #
        moduleName, extension = os.path.splitext(filename)

        if moduleName == '__init__' or extension != '.py':

            continue

        # Try and import module
        #
        filePath = os.path.join(packagePath, f'{moduleName}.py')

        modulePath = filePathToModulePath(filePath)
        log.info(f'Attempting to import: "{modulePath}" module, from: {filePath}')

        try:

            # Import module and check if it should be reloaded
            # The level flag indicates the import operation: -1: best guess, 0: absolute, 1: relative
            #
            module = __import__(
                modulePath,
                locals=__locals__,
                globals=__globals__,
                fromlist=[filePath],
                level=0
            )

            if reload:

                log.info(f'Reloading "{moduleName}" module...')
                reload_module(module)

            yield module

        except ImportError as exception:

            log.warning(exception)
            continue


def iterClasses(module, classFilter=object, includeAbstract=False):
    """
    Returns a generator that yields all the classes from the supplied module.
    An optional subclass filter can be provided to ignore specific types.

    :type module: module
    :type classFilter: type
    :type includeAbstract: bool
    :rtype: Iterator[type]
    """

    # Iterate through module dictionary
    #
    for (key, item) in module.__dict__.items():

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


def findClass(className, modulePath, __locals__=None, __globals__=None):
    """
    Returns the class associated with the given string.
    To improve the results be sure to provide a class name complete with module path.

    :type className: str
    :type modulePath: str
    :type __locals__: dict
    :type __globals__: dict
    :rtype: class
    """

    # Check if class name is valid
    #
    if stringutils.isNullOrEmpty(className):

        return None

    # Split string using delimiter
    #
    fromlist = modulePath.split('.', 1)
    module = __import__(modulePath, locals=__locals__, globals=__globals__, fromlist=fromlist, level=0)

    return getattr(module, className)


def tryImport(path, default=None, quiet=True, __locals__=None, __globals__=None):
    """
    Tries to import a module from the supplied path.
    If no module exists then the default value is returned instead!

    :type path: str
    :type default: Any
    :type quiet: bool
    :type __locals__: dict
    :type __globals__: dict
    :rtype: module
    """

    # Try and import module from path
    # TODO: Replace `__import__` with `importlib` method
    #
    module = None

    try:

        fromlist = path.split('.', 1)
        module = __import__(
            path,
            locals=__locals__,
            globals=__globals__,
            fromlist=fromlist,
            level=0
        )

    except ImportError as exception:

        if not quiet:

            log.info(exception)

        module = default

    finally:

        return module


def executeFile(filePath, __locals__=None, __globals__=None):
    """
    Executes a python file much like `execfile` in Python2x.
    See the following for details: https://stackoverflow.com/questions/436198/what-alternative-is-there-to-execfile-in-python-3-how-to-include-a-python-fil

    :type filePath: str
    :type __locals__: Union[dict, None]
    :type __globals__: Union[dict, None]
    :rtype: None
    """

    # Update globals with main and file
    #
    if __globals__ is None:

        __globals__ = {}

    __globals__.update(
        {
            "__file__": filePath,
            "__name__": "__main__",
        }
    )

    # Execute python file
    #
    with open(filePath, 'rb') as file:

        exec(compile(file.read(), filePath, 'exec'), __globals__, __locals__)


def iterPaths(paths):
    """
    Returns a generator that yields paths from the supplied object.

    :type paths: Union[str, List[str]]
    :rtype: Iterator[str]
    """

    if isinstance(paths, string_types):

        return filter(lambda path: not stringutils.isNullOrEmpty(path), paths.split(';'))

    elif isinstance(paths, Sequence):

        return filter(lambda path: not stringutils.isNullOrEmpty(path), paths)

    else:

        raise TypeError(f'iterPaths() expects a str or sequence ({type(paths).__name__})!')


def synchronizeSystemPaths():
    """
    Ensures that any paths within the `PYTHONPATH` environment variable have been pushed to system paths.
    Any userSetup.py files will also be executed!

    :rtype: None
    """

    # Iterate through python paths
    #
    pythonPaths = [pathutils.normalizePath(path, sep='\\') for path in iterPaths(os.environ['PYTHONPATH'])]
    systemPaths = [pathutils.normalizePath(path, sep='\\') for path in iterPaths(sys.path)]

    for path in pythonPaths:

        # Check if path is already in the system paths
        #
        if path in systemPaths:

            continue

        # Add site directory
        #
        log.info(f'PYTHONPATH+={path}')
        site.addsitedir(path)

        # Check if user-setup file exists
        #
        userSetupPath = os.path.join(path, 'userSetup.py')

        if os.path.isfile(userSetupPath):

            log.info(f'Executing user-setup: {userSetupPath}')
            executeFile(userSetupPath)
