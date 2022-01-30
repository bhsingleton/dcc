import numpy
import math

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


X_AXIS_VECTOR = numpy.array([1.0, 0.0, 0.0])
Y_AXIS_VECTOR = numpy.array([0.0, 1.0, 0.0])
Z_AXIS_VECTOR = numpy.array([0.0, 0.0, 1.0])
ORIGIN = numpy.array([0.0, 0.0, 0.0])


def normalizeVector(vector):
    """
    Returns a normalized vector.

    :type vector: numpy.array
    :rtype: numpy.array
    """

    return vector / numpy.linalg.norm(vector)
