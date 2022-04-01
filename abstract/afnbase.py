import inspect

from abc import ABCMeta, abstractmethod
from six import with_metaclass
from six.moves import collections_abc
from collections import deque
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
    __slots__ = ('_object', '_queue')
    __arrayindextype__ = ArrayIndexType.ZeroBased

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(AFnBase, self).__init__()

        # Declare class variables
        #
        self._object = None
        self._queue = deque()

        # Check if any arguments were supplied
        #
        numArgs = len(args)

        if numArgs == 0:

            pass

        elif numArgs == 1:

            self.setObject(args[0])

        else:

            self.setQueue(args)

    def __getattribute__(self, name):
        """
        Private method that provides attribute access for instances of the class.

        :type name: str
        :rtype: Any
        """

        # Get class definition
        # Evaluate if this is an instance method
        #
        cls = super(AFnBase, self).__getattribute__('__class__')
        obj = getattr(cls, name)

        if not inspect.isfunction(obj) or hasattr(AFnBase, name):

            return super(AFnBase, self).__getattribute__(name)

        # Check if function set is valid
        #
        func = super(AFnBase, self).__getattribute__('isValid')
        isValid = func()

        if isValid:

            return super(AFnBase, self).__getattribute__(name)

        else:

            raise TypeError('__getattribute__() function set object does not exist!')

    def __iter__(self):
        """
        Returns a generator that yields objects from the queue.
        Each object yielded will be automatically attached to this function set.

        :rtype: iter
        """

        while not self.isDone():

            yield self.next()

    def __len__(self):
        """
        Evaluates the number of objects in the queue.

        :rtype: int
        """

        return len(self._queue)
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

        except (RuntimeError, TypeError) as exception:

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
        Evaluates if this function set has an assigned object.
        This does not necessarily mean the object is valid!

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

    def isValid(self):
        """
        Evaluates if the attached object is valid.

        :rtype: bool
        """

        return True

    def queue(self):
        """
        Returns the object queue for this function set.

        :rtype: deque
        """

        return self._queue

    def setQueue(self, queue):
        """
        Updates the object queue for this function set.

        :type queue: Union[List, Iterable]
        :rtype: None
        """

        if isinstance(queue, collections_abc.MutableSequence):

            self._queue = deque(queue)

        elif isinstance(queue, collections_abc.Iterable):

            self._queue = deque(queue)

        else:

            raise TypeError('setQueue() expects a sequence (%s given)!' % type(queue).__name__)

    def isDone(self):
        """
        Evaluates if the queue is empty.

        :rtype: bool
        """

        return len(self._queue) == 0

    def next(self):
        """
        Attaches this function set to the next object in the queue.

        :rtype: object
        """

        # Check if queue is empty
        #
        if self.isDone():

            return

        # Pop next object in queue
        #
        obj = self._queue.popleft()
        success = self.trySetObject(obj)

        if success:

            return obj

        else:

            return self.next()
    # endregion
