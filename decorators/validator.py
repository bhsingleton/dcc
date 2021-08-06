def validator(func):
    """
    Decorator used to validate any function set methods.

    :type func: method
    :rtype: method
    """

    # Define wrapper
    #
    def wrapper(*args, **kwargs):

        # Check if instance is valid
        #
        instance = args[0]

        if instance.isValid():

            return func(*args, **kwargs)

        else:

            raise RuntimeError('Object does not exist!')

    return wrapper
