from abc import ABCMeta, abstractmethod
from six import with_metaclass

from dcc.decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnBase(with_metaclass(ABCMeta, object)):
    """
    Base class for all DCC function sets.
    """

    __slots__ = ('_object',)
    __arrayoffset__ = 0

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

    @classproperty
    def arrayOffset(cls):
        """
        Getter method that returns the array offset for this dcc.

        :rtype: int
        """

        return cls.__arrayoffset__

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

    def trySetObject(self, obj):
        """
        Attempts to assign an object to this function set for manipulation.
        A boolean will be returned that dictates if the operation was a success.

        :type obj: Any
        :rtype: bool
        """

        try:

            self.setObject(obj)
            return True

        except TypeError as exception:

            log.debug(exception)
            return False

    def resetObject(self):
        """
        Resets the object back to its default value.

        :rtype: None
        """

        self._object = None

    def hasObject(self):
        """
        Evaluates whether or not this function set has an assigned object.

        :rtype: bool
        """

        return self._object is not None

    def acceptsObject(self, obj):
        """
        Evaluates whether the supplied object is supported by this function set.

        :type obj: Any
        :rtype: bool
        """

        return True
