import time

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def timer(func):
    """
    Returns a timer decorator.
    See logger for info!

    :type func: method
    :rtype: method
    """

    # Define wrapper
    #
    def wrapper(*args, **kwargs):

        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()

        log.info('%s took %s ms.' % (func.__name__, (end - start) * 1000))
        return result

    return wrapper
