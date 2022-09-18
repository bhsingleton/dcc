from .flatten import flatten
from collections import deque


def uniquify(*items):
    """
    Returns a generator that yields unique items from the supplied list.
    This is useful for immutable items that aren't compatible with sets.

    :rtype: Iterator[Any]
    """

    unique = deque()

    for item in flatten(items):

        if item not in unique:

            yield item
            unique.append(item)

        else:

            continue
