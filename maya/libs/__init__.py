def iterEnumMembers(obj, prefix='k'):
    """
    Returns a generator that yields enum pairs from the supplied enum class.

    :type obj: Any
    :type prefix: str
    :rtype: iter
    """

    for (key, value) in obj.__dict__.items():

        if key.startswith(prefix) and isinstance(value, int):

            yield key, value

        else:

            continue
