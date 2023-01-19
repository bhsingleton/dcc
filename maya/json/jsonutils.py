import json

from . import mattributeparser, mshapeparser, mskinparser
from ..libs import sceneutils, animutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


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
