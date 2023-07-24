def staticInitializer(cls):
    """
    Decorator method that allows you to call a static initializer.

    :type cls: Callable
    :rtype: Callable
    """

    if hasattr(cls, '__static_init__'):

        cls.__static_init__()

    return cls
