import os
import json
import pymxs

from collections import defaultdict
from ..libs import nodeutils, controllerutils, transformutils
from ...generators.inclusiverange import inclusiveRange
from ...perforce import searchutils, clientutils, cmds

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def inspectScene():
    """
    Evaluates the contents of the open scene file.

    :rtype: dict
    """

    # Iterate through nodes
    #
    nodes = defaultdict(int)
    modifiers = defaultdict(int)
    controllers = defaultdict(int)
    nonOrthogonals = []
    expressions = defaultdict(list)
    scripts = defaultdict(list)

    for node in nodeutils.iterDescendants(pymxs.runtime.rootNode):

        # Increment node class
        #
        className = str(pymxs.runtime.classOf(node))
        nodes[className] += 1

        if not transformutils.isOrthogonal(node.transform):

            nonOrthogonals.append(node.name)

        # Iterate through modifiers
        #
        for modifier in node.modifiers:

            className = str(pymxs.runtime.classOf(modifier))
            modifiers[className] += 1

        # Iterate through controllers
        #
        for controller in controllerutils.walkTransformControllers(node):

            className = str(pymxs.runtime.classOf(controller))
            controllers[className] += 1

            if controllerutils.isScriptController(controller):

                scripts[node.name].append(controller.script)

            elif controllerutils.isWire(controller):

                numWires = 1 if controllerutils.isInstancedController(controller.slaveAnimation) else int(controller.numWires)
                expressions[node.name].extend([controller.getExprText(i) for i in inclusiveRange(1, numWires, 1)])

            else:

                continue

    return {
        'filePath': os.path.join(os.path.normpath(pymxs.runtime.maxFilePath), os.path.normpath(pymxs.runtime.maxFilename)),
        'nodes': nodes,
        'modifiers': modifiers,
        'controllers': controllers,
        'nonOrthogonals': nonOrthogonals,
        'expressions': expressions,
        'scripts': scripts
    }


def crawlFiles(filePaths, savePath):
    """
    Generates a scene inspection report for the supplied files.

    :type filePaths: List[str]
    :type savePath: str
    :rtype: None
    """

    # Iterate through results
    #
    numScenes = len(filePaths)
    scenes = [None] * numScenes

    for (i, filePath) in enumerate(filePaths):

        # Open scene file and inspect
        #
        pymxs.runtime.loadMaxFile(filePath, useFileUnits=True, quiet=True)
        scenes[i] = inspectScene()

    # Save inspections
    #
    with open(savePath, 'w') as jsonFile:

        json.dump(
            scenes,
            jsonFile,
            indent=4
        )

    log.info('Saving scene reports to: %s' % savePath)


def crawlPerforce(search, savePath):
    """
    Generates a scene inspection report by crawling perforce for scene files.

    :type search: str
    :type savePath: str
    :rtype: None
    """

    # Search perforce for scenes
    #
    client = clientutils.getCurrentClient()

    results = searchutils.findFile(search, client=client)
    numResults = len(results)

    # Iterate through results
    #
    filePaths = [None] * numResults

    for (i, result) in enumerate(results):

        # Map depot file to client view
        # If the user does not have the file then sync it!
        #
        depotPath = result['depotFile']
        filePath = client.mapToView(depotPath)

        if not os.path.exists(filePath):

            cmds.sync(filePath)

        # Add file path to list
        #
        filePaths[i] = filePath

    # Generate report from files
    #
    crawlFiles(filePaths, savePath)


def crawlScene(savePath=None):
    """
    Generates a scene inspection report for the current scene files.
    If no save path is supplied then the report is saved to the scene directory.

    :type savePath: str
    :rtype: None
    """

    # Check if a save path was supplied
    #
    filePath = os.path.join(pymxs.runtime.maxFilePath, pymxs.runtime.maxFilename)

    if savePath is None:

        directory, filename = os.path.split(filePath)
        name, ext = os.path.splitext(filename)

        savePath = os.path.join(directory, '{name}.json'.format(name=name))

    # Generate report from file
    #
    crawlFiles([filePath], savePath)
