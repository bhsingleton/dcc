import json
import pymxs

from . import mxsobjectparser

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def exportScene(savePath):
    """
    Exports the scene contents to the specified path.

    :type savePath: str
    :rtype: None
    """

    # Open file and overwrite contents
    #
    with open(savePath, 'w') as jsonFile:

        json.dump(
            pymxs.runtime.rootScene,
            jsonFile,
            cls=mxsobjectparser.MXSObjectEncoder,
            indent=4,
            skipkeys=True
        )

    log.info('Exporting scene to: %s' % savePath)


def exportSelection(savePath):
    """
    Exports the scene selection to the specified path.

    :type savePath: str
    :rtype: None
    """

    # Open file and overwrite contents
    #
    with open(savePath, 'w') as jsonFile:
        json.dump(
            pymxs.runtime.rootScene,
            jsonFile,
            cls=mxsobjectparser.MXSObjectEncoder,
            indent=4,
            skipChildren=True,
            selection=pymxs.runtime.selection
        )

    log.info('Exporting selection to: %s' % savePath)


def exportAnimation(savePath):
    """
    Exports the scene animation to the specified path.

    :type savePath: str
    :rtype: None
    """

    # Open file and overwrite contents
    #
    with open(savePath, 'w') as jsonFile:
        json.dump(
            pymxs.runtime.rootScene,
            jsonFile,
            cls=mxsobjectparser.MXSObjectEncoder,
            indent=4,
            skipProperties=True,
            skipShapes=True,
            skipLayers=True,
            skipSelectionSets=True,
            skipMaterials=True
        )

    log.info('Exporting animation to: %s' % savePath)
