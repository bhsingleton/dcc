import os
import sys
import pymxs

from ...python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def isNewScene():
    """
    Evaluates whether this is an untitled scene file.

    :rtype: bool
    """

    return stringutils.isNullOrEmpty(pymxs.runtime.maxFileName)


def newScene():
    """
    Creates a new scene file.

    :rtype: None
    """

    pymxs.runtime.resetMaxFile(pymxs.runtime.Name('noPrompt'))


def isSaveRequired():
    """
    Evaluates whether the open scene file has changes that need to be saved.

    :rtype: bool
    """

    return pymxs.runtime.getSaveRequired()


def saveScene(version=None):
    """
    Saves any changes made to the open scene file.

    :rtype: None
    """

    # Check if this is a new scene file
    #
    if isNewScene():

        return

    # Save changes to current scene file
    #
    filePath = currentFilePath()
    saveSceneAs(filePath, version=version)


def saveSceneAs(filePath, version=None):
    """
    Saves the open scene file in a difference location.

    :type filePath: str
    :type version: Union[int, None]
    :rtype: None
    """

    if isinstance(version, int):

        pymxs.runtime.saveMaxFile(filePath, version=version, quiet=True)

    else:

        pymxs.runtime.saveMaxFile(filePath, quiet=True)


def openScene(filePath):
    """
    Opens the supplied scene file.

    :rtype: bool
    """

    return pymxs.runtime.loadMaxFile(filePath, useFileUnits=True, quiet=True)


def currentFilename():
    """
    Returns the name of the open scene file.

    :rtype: str
    """

    if not isNewScene():

        return os.path.normpath(pymxs.runtime.maxFileName)

    else:

        return ''


def currentDirectory():
    """
    Returns the directory of the open scene file.

    :rtype: str
    """

    if not isNewScene():

        return os.path.normpath(pymxs.runtime.maxFilePath)

    else:

        return ''


def currentFilePath():
    """
    Returns the path of the open scene file.

    :rtype: str
    """

    if not isNewScene():

        return os.path.join(currentDirectory(), currentFilename())

    else:

        return ''


def isBatchMode():
    """
    Evaluates if max is running in batch mode.

    :rtype: bool
    """

    return os.path.split(sys.executable)[-1] == '3dsmaxbatch.exe'


def expandPaths(*args):
    """
    Returns a generator that yields expanded paths.

    :type args: tuple[str]
    :rtype: iter
    """

    # Iterate through arguments
    #
    for arg in args:

        # Check if path is relative
        #
        isAbsolute = pymxs.runtime.PathConfig.isAbsolutePath(arg)

        if not isAbsolute:

            arg = pymxs.runtime.PathConfig.convertPathToAbsolute(arg)

        # Normalize path and yield it
        #
        yield os.path.normpath(arg)


def iterSessionPaths(maps=False, xrefs=False):
    """
    Returns a generator that yields session paths.
    These are temporary paths that do not persist between sessions.

    :type maps: bool
    :type xrefs: bool
    :rtype: iter
    """

    if maps:

        name = pymxs.runtime.Name('map')
        count = pymxs.runtime.sessionPaths.count(name)

        for i in range(1, count + 1, 1):

            yield pymxs.runtime.sessionPaths.get(name, i)

    if xrefs:

        name = pymxs.runtime.Name('xref')
        count = pymxs.runtime.sessionPaths.count(name)

        for i in range(1, count + 1, 1):

            yield pymxs.runtime.sessionPaths.get(name, i)


def iterXRefPaths(expand=False):
    """
    Returns a generator that yields xref paths.
    Expanding paths will resolve any relative paths to their project root.

    :type expand: bool
    :rtype: iter
    """

    # Iterate through bitmap paths
    #
    numPaths = pymxs.runtime.xrefPaths.count()

    for i in range(1, numPaths + 1, 1):

        # Check if path is relative
        #
        path = pymxs.runtime.xrefPaths.get(i)
        isAbsolute = pymxs.runtime.PathConfig.isAbsolutePath(path)

        if not isAbsolute and expand:

            path = pymxs.runtime.PathConfig.convertPathToAbsolute(path)

        # Yield normalized path
        #
        yield os.path.normpath(path)


def iterBitmapPaths(expand=False):
    """
    Returns a generator that yields bitmap paths.
    Expanding paths will resolve any relative paths to their project root.

    :type expand: bool
    :rtype: iter
    """

    # Iterate through bitmap paths
    #
    numPaths = pymxs.runtime.mapPaths.count()

    for i in range(1, numPaths + 1, 1):

        # Check if path is relative
        #
        path = pymxs.runtime.mapPaths.get(i)
        isAbsolute = pymxs.runtime.PathConfig.isAbsolutePath(path)

        if not isAbsolute and expand:

            path = pymxs.runtime.PathConfig.convertPathToAbsolute(path)

        # Yield normalized path
        #
        yield os.path.normpath(path)


def cleanXRefPaths():
    """
    Removes any xref paths that no longer exist.

    :rtype: None
    """

    paths = list(iterXRefPaths(expand=True))

    for (i, path) in reversed(list(enumerate(paths))):

        if not os.path.exists(path):

            pymxs.runtime.xrefPaths.delete(i + 1)


def cleanBitmapPaths():
    """
    Removes any bitmap paths that no longer exist.

    :rtype: None
    """

    paths = list(iterBitmapPaths(expand=True))

    for (i, path) in reversed(list(enumerate(paths))):

        if not os.path.exists(path):

            pymxs.runtime.mapPaths.delete(i + 1)


def extendSessionPaths(*args, **kwargs):
    """
    Extends the specified sessions paths.

    :key maps: bool
    :key xrefs: bool
    :rtype: None
    """

    # Check if map paths should be extended
    #
    maps = kwargs.get('maps', False)

    if maps:

        mapPaths = list(iterSessionPaths(maps=True))
        name = pymxs.runtime.Name('map')

        for arg in args:

            if arg not in mapPaths:

                log.info('Appending "%s" to bitmap paths!' % arg)
                pymxs.runtime.sessionPaths.add(name, arg)

            else:

                continue

    # Check if xref paths should be extended
    #
    xrefs = kwargs.get('xrefs', False)

    if xrefs:

        xrefPaths = list(iterSessionPaths(xrefs=True))
        name = pymxs.runtime.Name('xref')

        for arg in args:

            if arg not in xrefPaths:

                log.info('Appending "%s" to xref paths!' % arg)
                pymxs.runtime.sessionPaths.add(name, arg)

            else:

                continue


def projectPath():
    """
    Returns the current project path.

    :rtype: str
    """

    return os.path.normpath(pymxs.runtime.PathConfig.getCurrentProjectFolder())


def setProjectPath(directory):
    """
    Updates the current project directory.

    :type directory: str
    :rtype: None
    """

    # Update current project folder
    #
    pathConfig = pymxs.runtime.PathConfig
    pathConfig.setCurrentProjectFolder(directory)

    # Update project subdirectories
    # These should be relative to the project root
    #
    pathConfig.setDir(pymxs.runtime.Name('Animations'), os.path.join('.', 'sceneassets', 'animations'))
    pathConfig.setDir(pymxs.runtime.Name('Archives'), os.path.join('.', 'archives'))
    pathConfig.setDir(pymxs.runtime.Name('AutoBack'), os.path.join('.', 'autoback'))
    pathConfig.setDir(pymxs.runtime.Name('Proxies'), os.path.join('.', 'proxies'))
    pathConfig.setDir(pymxs.runtime.Name('Downloads'), os.path.join('.', 'downloads'))
    pathConfig.setDir(pymxs.runtime.Name('Export'), os.path.join('.', 'export'))
    pathConfig.setDir(pymxs.runtime.Name('Expression'), os.path.join('.', 'express'))
    #pathConfig.setDir(pymxs.runtime.Name('FluidSimulations'), os.path.join('.', 'SimCache'))
    pathConfig.setDir(pymxs.runtime.Name('Image'), os.path.join('.', 'sceneassets', 'images'))
    pathConfig.setDir(pymxs.runtime.Name('Import'), os.path.join('.', 'import'))
    pathConfig.setDir(pymxs.runtime.Name('MatLib'), os.path.join('.', 'materiallibraries'))
    pathConfig.setDir(pymxs.runtime.Name('MaxStart'), os.path.join('.', 'scenes'))
    pathConfig.setDir(pymxs.runtime.Name('Photometric'), os.path.join('.', 'sceneassets', 'photometric'))
    pathConfig.setDir(pymxs.runtime.Name('Preview'), os.path.join('.', 'previews'))
    pathConfig.setDir(pymxs.runtime.Name('RenderAssets'), os.path.join('.', 'sceneassets', 'renderassets'))
    pathConfig.setDir(pymxs.runtime.Name('RenderOutput'), os.path.join('.', 'renderoutput'))
    pathConfig.setDir(pymxs.runtime.Name('RenderPresets'), os.path.join('.', 'renderpresets'))
    pathConfig.setDir(pymxs.runtime.Name('Scene'), os.path.join('.', 'scenes'))
    pathConfig.setDir(pymxs.runtime.Name('Sound'), os.path.join('.', 'sceneassets', 'sounds'))
    pathConfig.setDir(pymxs.runtime.Name('VPost'), os.path.join('.', 'vpost'))

    # Save changes to .mxp file
    # Most maxscript functions don't accept environment variables!
    #
    configPath = os.path.expandvars(os.path.join(directory, '3dsmax.mxp'))

    log.info('Saving project changes to: %s' % configPath)
    pathConfig.saveTo(configPath)


def resetProjectPath():
    """
    Resets the project path back to the original user documents location.

    :rtype: None
    """

    defaultPath = os.path.expandvars(os.path.join('%USERPROFILE%', 'Documents', '3dsMax'))
    setProjectPath(defaultPath)


def iterFileProperties():
    """
    Returns a generator that yields file properties as key-value pairs.

    :rtype: iter
    """

    # Iterate through properties
    #
    category = pymxs.runtime.name('custom')
    numProperties = pymxs.runtime.fileProperties.getNumProperties(category)

    for i in range(numProperties):

        key = pymxs.runtime.fileProperties.getPropertyName(category, i + 1)
        value = pymxs.runtime.fileProperties.getPropertyValue(category, i + 1)

        yield key, value
