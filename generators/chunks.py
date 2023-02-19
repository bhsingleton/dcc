def chunks(items, size):
    """
    Returns a generator that groups items by a chunk size.

    :type items: List[Any]
    :type size: int
    :rtype: Iterator[List[Any]]
    """

    numItems = len(items)

    for i in range(0, numItems, size):

        yield items[i:(i + size)]
