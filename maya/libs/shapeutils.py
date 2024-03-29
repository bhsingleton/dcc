import math

from maya import cmds as mc
from maya.api import OpenMaya as om
from enum import IntEnum
from . import dagutils, plugutils
from ...python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ObjectColor(IntEnum):
    """
    Collection of all available object colours.
    """

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

    attributeExists = mc.attributeQuery('lineWidth', node=fullPathName, exists=True)

    if attributeExists:

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
    lineWidth = kwargs.get('lineWidth', None)
    colorIndex = kwargs.get('colorIndex', None)
    colorRGB = kwargs.get('colorRGB', None)
    side = kwargs.get('side', None)

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


def createKnotVector(count, degree, periodic=False):
    """
    Returns a knot vector from the given parameters.
    The minimum number of CVs needed to create a periodic curve is: numCVs >= ( 2 * degree ) + 1
    But all periodic curves must have: numCVs == ( spans + degree )

    :type count: int
    :type degree: int
    :type periodic: bool
    :rtype: Tuple[List[int], int]
    """

    if periodic:

        # Check if there are enough CVs
        #
        minimum = (2 * degree) + 1

        if count == minimum:

            degree -= 1

        elif count < minimum:

            raise TypeError('createKnotVector() expects at least %s CVs (%s given)!' % (minimum, count))

        else:

            pass

        # Generate knots
        #
        numSpans = count - degree
        numKnots = numSpans + (2 * degree) - 1
        knots = [x for x in range(-(degree - 1), (numKnots - (degree - 1)), 1)]

        return knots, degree

    else:

        # Check if there are enough CVs
        # numKnots = count + degree - 1
        #
        if count == degree:

            degree -= 1

        elif count < degree:

            raise TypeError(f'createKnotVector() expects at least {degree} CVs ({count} given)!')

        else:

            pass

        # Generate knots
        #
        knotCount = count + degree - 1
        headSize = degree
        tailSize = knotCount - degree
        tailValue = (float(knotCount) - (degree * 2.0)) + 1.0

        knots = [0] * knotCount

        for i in range(knotCount):

            if 0 <= i < headSize:

                knots[i] = 0.0

            elif headSize <= i < tailSize:

                knots[i] = float(i) - (headSize - 1.0)

            else:

                knots[i] = tailValue

        return knots, degree


def createCurveFromPoints(controlPoints, degree=1, periodic=False, parent=om.MObject.kNullObj):
    """
    Creates a curve data object from the supplied points.

    :type controlPoints: List[om.MVector]
    :type degree: int
    :type periodic: bool
    :type parent: om.MObject
    :rtype: om.MObject
    """

    numControlPoints = len(controlPoints)
    form = om.MFnNurbsCurve.kPeriodic if periodic else om.MFnNurbsCurve.kOpen
    knots, degree = createKnotVector(numControlPoints, degree, periodic=periodic)

    hasParent = not parent.isNull()

    if hasParent:

        fnCurve = om.MFnNurbsCurve()
        curve = fnCurve.create(controlPoints, knots, degree, form, False, True, parent=parent)

        curveName = f'{dagutils.getNodeName(parent)}Shape'
        fnCurve.setName(curveName)

        return curve

    else:

        fnCurveData = om.MFnNurbsCurveData()
        curveData = fnCurveData.create()

        fnCurve = om.MFnNurbsCurve()
        fnCurve.create(controlPoints, knots, degree, form, False, True, parent=curveData)

        return curveData


def createStar(outerRadius, innerRadius, numPoints=5, normal=om.MVector.kXaxisVector, parent=om.MObject.kNullObj):
    """
    Creates a star nurbs curve data object.
    If a parent is supplied then a new shape is created under that object.

    :type outerRadius: float
    :type innerRadius: float
    :type numPoints: int
    :type normal: om.MVector
    :type parent: om.MObject
    :rtype: om.MObject
    """

    # Collect star points
    #
    size = numPoints * 2
    angleFactor = (math.pi * 2.0) / size

    controlPoints = om.MPointArray()

    for i in range(size):  # Skip last point since it's a close curve!

        # Compute point
        #
        isEven = (i % 2) == 0
        angle = float(i) * angleFactor

        x, y = 0.0, 0.0

        if isEven:

            x, y = math.cos(angle) * outerRadius, math.sin(angle) * outerRadius

        else:

            x, y = math.cos(angle) * innerRadius, math.sin(angle) * innerRadius

        # Rotate point into normal space
        #
        quat = om.MVector.kZaxisVector.rotateTo(normal)
        point = om.MVector(x, y, 0.0).rotateBy(quat)

        controlPoints.append(om.MPoint(point))

    # Check if a parent was supplied
    #
    knots, degree = createKnotVector(len(controlPoints), 1, periodic=True)
    hasParent = not parent.isNull()

    if hasParent:

        fnCurve = om.MFnNurbsCurve()
        curve = fnCurve.create(controlPoints, knots, degree, om.MFnNurbsCurve.kClosed, False, True, parent=parent)

        curveName = f'{dagutils.getNodeName(parent)}Shape'
        fnCurve.setName(curveName)

        return curve

    else:

        fnCurveData = om.MFnNurbsCurveData()
        curveData = fnCurveData.create()

        fnCurve = om.MFnNurbsCurve()
        fnCurve.create(controlPoints, knots, degree, om.MFnNurbsCurve.kClosed, False, True, parent=curveData)

        return curveData
