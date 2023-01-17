import json

from . import manimparser
from ..libs import sceneutils, animutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def exportPose(filePath, nodes):
    """
    Saves the pose for the supplied nodes.

    :type filePath: str
    :type nodes: Union[List[om.MObject], om.MObjectArray, om.MSelectionList]
    :rtype: None
    """

    # Define pose data
    #
    obj = {
        'filePath': sceneutils.currentFilePath(),
        'projectPath': sceneutils.currentProjectDirectory(),
        'units': sceneutils.currentUnits(),
        'animationRange': sceneutils.getAnimationRange(),
        'nodes': nodes,
        'animLayers': [],
        'thumbnail': None
    }

    # Open file and serialze data
    #
    with open(filePath, 'w') as jsonFile:

        json.dump(obj, jsonFile, cls=manimparser.MAnimEncoder, indent=4, skipkeys=True, skipLayers=True)

    log.info('Exporting pose to: %s' % filePath)


def exportAnimation(filePath, nodes):
    """
    Saves the animation from the supplied nodes.

    :type filePath: str
    :type nodes: Union[List[om.MObject], om.MObjectArray, om.MSelectionList]
    :rtype: None
    """

    # Define animation data
    #
    obj = {
        'filePath': sceneutils.currentFilePath(),
        'projectPath': sceneutils.currentProjectDirectory(),
        'units': sceneutils.currentUnits(),
        'animRange': sceneutils.getAnimationRange(),
        'nodes': nodes,
        'animLayers': [animutils.getBaseAnimLayer()],
        'thumbnail': None
    }

    # Open file and serialze data
    #
    with open(filePath, 'w') as jsonFile:

        json.dump(obj, jsonFile, cls=manimparser.MAnimEncoder, indent=4)

    log.info('Exporting animation to: %s' % filePath)


def exportUserAttributes(filePath, node):
    """
    Saves the user attributes from the supplied node.

    :type filePath: str
    :type node: om.MObject
    :rtype: None
    """

    pass


def exportShapes(filePath, node):
    """
    Saves the shapes from the supplied node.

    :type filePath: str
    :type node: om.MObject
    :rtype: None
    """

    pass


def exportSkin(filePath, skin):
    """
    Saves the skin weights from the supplied deformer.

    :type filePath: str
    :type skin: om.MObject
    :rtype: None
    """

    pass
