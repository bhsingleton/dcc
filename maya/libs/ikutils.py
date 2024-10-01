import math

from maya.api import OpenMaya as om
from . import transformutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def solve2Bone(origin, goal, lengths, poleVector):
    """
    Solves a 2-bone system using the law of cosines.
    See the following for details: https://www.mathsisfun.com/algebra/trig-solving-sss-triangles.html
    The solution uses the default forward-X and up-Y as the default axes!

    :type origin: om.MVector
    :type goal: om.MVector
    :type lengths: Tuple[float, float]
    :type poleVector: om.MVector
    :rtype: Tuple[om.MMatrix, om.MMatrix, om.MMatrix]
    """

    # Calculate min/max limb length
    #
    startLength, endLength = lengths

    maxDistance = startLength + endLength
    minDistance = abs(endLength - startLength)

    # Calculate aim vector
    #
    aimVector = goal - origin

    forwardVector = aimVector.normal()
    distance = aimVector.length()

    # Calculate angles using law of cosines
    #
    startRadian, endRadian = 0.0, 0.0

    if distance < (minDistance + 1e-3):  # Collapsed

        endRadian = 0.0

    elif distance > (maxDistance - 1e-3):  # Hyper-extended

        endRadian = math.pi

    else:

        startRadian = math.acos((pow(startLength, 2.0) + pow(distance, 2.0) - pow(endLength, 2.0)) / (2.0 * startLength * distance))
        endRadian = math.acos((pow(endLength, 2.0) + pow(startLength, 2.0) - pow(distance, 2.0)) / (2.0 * endLength * startLength))

    # Calculate twist matrix
    #
    xAxis = forwardVector
    zAxis = (xAxis ^ poleVector).normal()
    yAxis = (zAxis ^ xAxis).normal()

    twistMatrix = transformutils.createTransformMatrix(xAxis, yAxis, zAxis, origin)

    # Compose matrices
    #
    startMatrix = transformutils.createRotationMatrix(om.MEulerRotation(0.0, 0.0, startRadian)) * twistMatrix
    midMatrix = transformutils.createRotationMatrix(om.MEulerRotation(0.0, 0.0, -(math.pi - endRadian))) * transformutils.createTranslateMatrix([startLength, 0.0, 0.0]) * startMatrix
    endMatrix = transformutils.createTranslateMatrix([endLength, 0.0, 0.0]) * midMatrix

    return startMatrix, midMatrix, endMatrix
