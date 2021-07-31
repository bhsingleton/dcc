from abc import ABCMeta, abstractmethod

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnBase(object, metaclass=ABCMeta):
    """
    Base class for all DCC function sets.
    """

    __slots__ = ()

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.
        """

        # Call parent method
        #
        super(AFnBase, self).__init__()
