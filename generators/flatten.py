from collections import deque
from ..vendor.six import string_types
from ..vendor.six.moves import collections_abc


def flatten(*args, **kwargs):
    """
    Returns a generator that flattens the supplied items and yields them.

    :rtype: Iterator[Any]
    """

    # Iterate through items
    #
    queue = deque(args)

    while len(queue) > 0:

        # Evaluate item type
        #
        item = queue.popleft()

        if isinstance(item, collections_abc.Sequence) and not isinstance(item, string_types):

            queue.extendleft(reversed(item))

        elif isinstance(item, collections_abc.Iterator) and not isinstance(item, string_types):

            queue.extendleft(reversed(list(item)))

        else:

            yield item
