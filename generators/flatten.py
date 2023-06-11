from six.moves import collections_abc
from collections import deque
from ..python import arrayutils


def flatten(*items):
    """
    Returns a generator that flattens the supplied items and yields them.

    :rtype: Iterator[Any]
    """

    queue = deque(items)

    while len(queue) > 0:

        item = queue.popleft()

        if arrayutils.isArrayLike(item):

            queue.extendleft(reversed(item))

        elif arrayutils.isIterable(item):

            queue.extendleft(reversed(list(item)))

        else:

            yield item
