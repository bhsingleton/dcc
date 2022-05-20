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
    Evaluates the number of node/modifier/controller types from the current scene file.

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
        for controller in controllerutils.walkControllers(node):

            className = str(pymxs.runtime.classOf(controller))
            controllers[className] += 1

            if controllerutils.isScriptController(controller):

                scripts[node.name].append(controller.script)

            elif controllerutils.isWireParameter(controller):

                expressions[node.name].extend([controller.getExprText(i) for i in inclusiveRange(1, controller.numWires, 1)])

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


def crawlPerforce(search, savePath):
    """
    Generates a scene inspection report by crawling perforce for scenes.

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
    scenes = [None] * numResults

    for (i, result) in enumerate(results):

        # Map depot file to client view
        # If the user does not have the file then sync it!
        #
        depotPath = result['depotFile']
        filePath = client.mapToView(depotPath)

        if not os.path.exists(filePath):

            cmds.sync(filePath)

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
