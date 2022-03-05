import math

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def isClose(a, b, rel_tol=1e-03, abs_tol=1e-03):
    """
    Evaluates if the two numbers of relatively close.
    Sadly this function doesn't exist in the math module until Python 3.5

    :type a: float
    :type b: float
    :type rel_tol: float
    :type abs_tol: float
    :rtype: bool
    """

    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)