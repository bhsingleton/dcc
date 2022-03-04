from abc import ABCMeta, abstractmethod
from six import with_metaclass

from dcc.abstract import ArrayIndexType
from dcc.decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnBase(with_metaclass(ABCMeta, object)):
    """
    Base class for all DCC function sets.
    """

    # region Dunderscores
    __slots__ = ('_object',)
    __arrayindextype__ = ArrayIndexType.ZeroBased

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
    # endregion

    # region Properties
    @classproperty
    def arrayIndexType(cls):
        """
        Getter method that returns the array index type for the associated dcc.

        :rtype: int
        """

        return cls.__arrayindextype__
    # endregion

    # region Methods
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
    # endregion
