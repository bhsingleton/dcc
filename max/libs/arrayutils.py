import pymxs

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__bits_to_array__ = pymxs.runtime.execute('fn bitArrayToArray bits = ( bits as array );')
__array_to_bits__ = pymxs.runtime.execute('fn arrayToBitArray items = ( items as BitArray );')


def convertBitArray(bits):
    """
    Returns an array of elements from the supplied bit array.

    :type bits: pymxs.runtime.BitArray
    :rtype: pymxs.runtime.Array
    """

    if pymxs.runtime.isKindOf(bits, pymxs.runtime.BitArray):

        return __bits_to_array__(bits)

    else:

        raise TypeError(f'convertBitArray() expects a bit array ({type(bits).__name__} given)!')


def convertToBitArray(indices, count=None):
    """
    Converts the supplied indices into a bit array.

    :type indices: List[int]
    :type count: int
    :rtype: pymxs.runtime.BitArray
    """

    bits = pymxs.runtime.BitArray()
    bits.count = len(indices) if not isinstance(count, int) else count

    for index in indices:

        bits[index] = True

    return bits


def iterElements(array, cls=int):
    """
    Returns a generator that yields elements from an array.
    There is a bug in `pymxs` where elements are cast to float types!

    :type array: pymxs.runtime.Array
    :type cls: Callable
    :rtype: Iterator[int]
    """

    return map(cls, array)


def iterBitArray(bits):
    """
    Returns a generator that yields the elements from a bit array.

    :type bits: pymxs.runtime.BitArray
    :rtype: Iterator[int]
    """

    return iterElements(convertBitArray(bits))


def convert2DArray(points, cls=pymxs.runtime.Point2):
    """
    Returns an array of points from the supplied list.

    :type points: List[Tuple[float, float]]
    :type cls: Callable
    :rtype: pymxs.runtime.Array
    """

    return pymxs.runtime.Array(*tuple(map(lambda point: cls(*point), points)))


def convert3DArray(points, cls=pymxs.runtime.Point3):
    """
    Returns an array of points from the supplied list.

    :type points: List[Tuple[float, float, float]]
    :type cls: Callable
    :rtype: pymxs.runtime.Array
    """

    return pymxs.runtime.Array(*tuple(map(lambda point: cls(*point), points)))
