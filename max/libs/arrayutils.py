import pymxs

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def iterElements(array):
    """
    Returns a generator that yields elements from an array.
    There is a bug in pymxs where elements are cast to float by default.

    :type array: pymxs.runtime.Array
    :rtype: iter
    """

    return map(int, array)


def iterBitArray(bits):
    """
    Returns a generator that yields the elements from a bit array.

    :type bits: pymxs.runtime.MXSWrapperBase
    :rtype: iter
    """

    for i in range(bits.count):

        bit = bits[i]

        if bit:

            yield i + 1

        else:

            continue
