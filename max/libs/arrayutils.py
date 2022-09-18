import pymxs

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__convert_bitarray__ = pymxs.runtime.execute('fn bitArrayToArray bits = ( bits as array );')


def convertBitArray(bits):
    """
    Returns an array of elements from the supplied bit array.

    :type bits: pymxs.runtime.BitArray
    :rtype: pymxs.runtime.Array
    """

    return __convert_bitarray__(bits)


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

    :type bits: pymxs.runtime.BitArray
    :rtype: iter
    """

    elements = convertBitArray(bits)
    return iterElements(elements)
