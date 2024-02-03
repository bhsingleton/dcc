import os
import json

from maya import cmds as mc, OpenMaya as lom
from maya.api import OpenMaya as om
from enum import IntEnum
from . import dagutils
from ..json import mshapeparser
from ...python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ObjectColor(IntEnum):

    ORANGE = 0
    YELLOW = 1
    LIME = 2
    GREEN = 3
    TEAL = 4
    BLUE = 5
    PURPLE = 6
    PINK = 7


COLOR_SIDE_INDEX = {0: ObjectColor.YELLOW, 1: ObjectColor.BLUE, 2: ObjectColor.ORANGE, 3: ObjectColor.YELLOW}
COLOUR_SIDE_RGB = {0: (1.0, 1.0, 0.0), 1: (0.0, 0.0, 1.0), 2: (1.0, 0.0, 0.0), 3: (1.0, 1.0, 0.0)}


def setObjectColorIndex(shape, colorIndex):
    """
    Applies the color index to the supplied shape node.

    :type shape: Union[om.MObject, om.MDagPath]
    :type colorIndex: int
    :rtype: None
    """

    dagPath = dagutils.getMDagPath(shape)
    fullPathName = dagPath.fullPathName()

    mc.setAttr(f'{fullPathName}.useObjectColor', 1)
    mc.setAttr(f'{fullPathName}.objectColor', colorIndex)  # Ranges from 0-7


def setWireColorRGB(shape, colorRGB):
    """
    Applies the color RGB to the supplied shape node.

    :type shape: Union[om.MObject, om.MDagPath]
    :type colorRGB: Tuple[float, float, float]
    :rtype: None
    """

    dagPath = dagutils.getMDagPath(shape)
    fullPathName = dagPath.fullPathName()

    mc.setAttr(f'{fullPathName}.useObjectColor', 2)
    mc.setAttr(f'{fullPathName}.wireColorR', colorRGB[0])
    mc.setAttr(f'{fullPathName}.wireColorG', colorRGB[1])
    mc.setAttr(f'{fullPathName}.wireColorB', colorRGB[2])


def setColorBySide(shape, side):
    """
    Applies the color to the supplied shape node based on the side.

    :type shape: Union[om.MObject, om.MDagPath]
    :type side: Union[int, IntEnum]
    :rtype: None
    """

    setWireColorRGB(shape, COLOUR_SIDE_RGB[side])


def setLineWidth(shape, lineWidth):
    """
    Applies the line width to the supplied shape node.

    :type shape: om.MObject
    :type lineWidth: Union[int, float]
    :rtype: None
    """

    dagPath = dagutils.getMDagPath(shape)
    fullPathName = dagPath.fullPathName()

    mc.setAttr(f'{fullPathName}.lineWidth', lineWidth)


def colorizeShape(*shapes, **kwargs):
    """
    Colorizes the supplied shape node based on the supplied arguments.

    :key colorIndex: int
    :key colorRGB: Tuple[float, float, float]
    :key side: Union[int, IntEnum]
    :rtype: None
    """

    # Iterate through shapes
    #
    colorIndex = kwargs.get('colorIndex', None)
    colorRGB = kwargs.get('colorRGB', None)
    side = kwargs.get('side', None)
    lineWidth = kwargs.get('lineWidth', None)

    for shape in shapes:

        # Check if a line-width was supplied
        #
        if isinstance(lineWidth, (int, float)):

            setLineWidth(shape, lineWidth)

        # Check if a color index was supplied
        #
        if isinstance(colorIndex, int):

            setObjectColorIndex(shape, colorIndex)
            continue

        # Check if a color RGB was supplied
        #
        if not stringutils.isNullOrEmpty(colorRGB):

            setWireColorRGB(shape, colorRGB)
            continue

        # Check if a side was supplied
        #
        if isinstance(side, IntEnum):

            setColorBySide(shape, side)
            continue


def createShapeTemplate(node, filePath):
    """
    Creates a shape template from the supplied transform or shape node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type filePath: str
    :rtype: None
    """

    # Evaluate api type
    #
    node = dagutils.getMObject(node)
    shapes = []

    if node.hasFn(om.MFn.kTransform):

        shapes.extend(list(dagutils.iterShapes(node)))

    elif node.hasFn(om.MFn.kShape):

        shapes.append(node)

    else:

        raise TypeError(f'createShapeTemplate() expects a shape node ({node.apiTypeStr} given)!')

    # Save json file
    #
    with open(filePath, 'w') as jsonFile:

        log.info(f'Saving shape template to: {filePath}')
        json.dump(shapes, jsonFile, cls=mshapeparser.MShapeEncoder, indent=4)


def loadShapeTemplate(filePath, **kwargs):
    """
    Recreates the shapes from the supplied file path.
    This name will be used to lookup the json file from the shapes directory.

    :type filePath: str
    :key size: float
    :key localPosition: Union[om.MVector, Tuple[float, float, float]]
    :key localRotate: Union[om.MVector, Tuple[float, float, float]]
    :key localScale: Union[om.MVector, Tuple[float, float, float]]
    :key lineWidth: float
    :key parent: om.MObject
    :rtype: List[om.MObject]
    """

    # Check if file exists
    #
    if not os.path.exists(filePath):

        log.warning(f'Unable to locate shape template: {filePath}')
        return []

    # Iterate through shape nodes
    #
    with open(filePath, 'r') as jsonFile:

        return json.load(jsonFile, cls=mshapeparser.MShapeDecoder, **kwargs)
