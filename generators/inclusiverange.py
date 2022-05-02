def inclusiveRange(*args, **kwargs):
    """
    Generator method used to yield an inclusive range for use with plug elements.

    :rtype: iter
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

        start = args[0]
        end = args[1]
        step = 1 if start <= end else -1

    elif numArgs == 3:

        start = args[0]
        end = args[1]
        step = args[2]

    else:

        raise TypeError('inclusiveRange() expects 1 to 3 argument(s) (%s given)!' % numArgs)

    # Yield integer values
    #
    i = start

    while i <= end:

        yield i
        i += step
