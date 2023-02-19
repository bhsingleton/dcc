def package(counts, items):
    """
    Returns a generator that packages the flattened items based on their associated count.

    :type counts: List[int]
    :type items: List[Any]
    :rtype: Iterator[List[Any]]
    """

    startIndex = 0
    endIndex = 0

    for count in counts:

        startIndex += endIndex
        endIndex = startIndex + count

        yield items[startIndex:endIndex]
