def inclusiveRange(*args, **kwargs):
    """
    Generator method used to yield an inclusive range for use with plug elements.

    :rtype: Iterator[int]
    """

    # Inspect supplied arguments
    #
    start = None
    end = None
    step = None

    numArgs = len(args)

    if numArgs == 1:

        start = 0
        end = args[0]
        step = 1 if start <= end else -1

    elif numArgs == 2:

        start, end = args
        step = 1 if start <= end else -1

    elif numArgs == 3:

        start, end, step = args

    else:

        raise TypeError('inclusiveRange() expects 1 to 3 argument(s) (%s given)!' % numArgs)

    # Yield integer values
    #
    index = start

    if start <= end and step > 0:

        while index <= end:

            yield index
            index += step

    elif end <= start and step < 0:

        while index >= end:

            yield index
            index += step

    else:

        return iter([])
