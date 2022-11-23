from six import string_types
from six.moves import collections_abc
from collections import deque


def flatten(*items):
    """
    Returns a generator that flattens the supplied items and yields them.

    :rtype: Iterator[Any]
    """

    queue = deque(items)

    while len(queue) > 0:

        item = queue.popleft()

        if isinstance(item, collections_abc.Sequence) and not isinstance(item, string_types):

            queue.extendleft(reversed(item))

        elif isinstance(item, collections_abc.Iterator):

            queue.extendleft(reversed(list(item)))

        else:

            yield item
