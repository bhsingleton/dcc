import json
import pymxs

from . import mxsobjectparser
from ..libs import nodeutils

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
            pymxs.runtime.RootScene,
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
            pymxs.runtime.RootScene,
            jsonFile,
            cls=mxsobjectparser.MXSObjectEncoder,
            indent=4,
            skipChildren=True,
            selection=pymxs.runtime.Selection
        )

    log.info('Exporting selection to: %s' % savePath)


def exportAnimation(savePath, controls=('*_Ctrl', '*_Anim')):
    """
    Exports the scene animation to the specified path.

    :type savePath: str
    :type controls: Tuple[str]
    :rtype: None
    """

    # Open file and overwrite contents
    #
    selection = list(nodeutils.iterNodesByPattern(*controls, ignoreCase=True))

    with open(savePath, 'w') as jsonFile:

        json.dump(
            pymxs.runtime.RootScene,
            jsonFile,
            cls=mxsobjectparser.MXSObjectEncoder,
            indent=4,
            skipChildren=True,
            skipShapes=True,
            skipSelectionSets=True,
            selection=selection
        )

    log.info('Exporting animation to: %s' % savePath)
