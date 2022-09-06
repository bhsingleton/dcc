from operator import itemgetter
from itertools import groupby


def consecutivePairs(iterable):
    """
    Returns a generator that yields consecutive pairs from the supplied iterable.

    :type iterable: List[int]
    :rtype: iter
    """

    for (i, grouper) in groupby(enumerate(sorted(iterable)), lambda x: x[0] - x[1]):

        group = (map(itemgetter(1), grouper))
        group = list(map(int, group))

        yield group[0], group[-1]
