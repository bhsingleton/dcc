from abc import ABCMeta, abstractmethod
from six import with_metaclass

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnBase(with_metaclass(ABCMeta, object)):
    """
    Base class for all DCC function sets.
    """

    __slots__ = ('_object',)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.
        """

        # Call parent method
        #
        super(AFnBase, self).__init__()

        # Declare class variables
        #
        self._object = None

        # Check if any arguments were supplied
        #
        numArgs = len(args)

        if numArgs == 1:

            self.setObject(args[0])

    def object(self):
        """
        Returns the object assigned to this function set.

        :rtype: Any
        """

        return self._object

    def setObject(self, obj):
        """
        Assigns an object to this function set for manipulation.
        If the object is not compatible then raise a type error.

        :type obj: Any
        :rtype: None
        """

        self._object = obj
