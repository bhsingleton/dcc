import inspect

from abc import ABCMeta, abstractmethod
from six import with_metaclass, string_types
from six.moves import collections_abc
from collections import deque
from dcc.abstract import ArrayIndexType
from dcc.generators.flatten import flatten
from dcc.decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnBase(with_metaclass(ABCMeta, object)):
    """
    Abstract base class for all DCC function sets.
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

            pass  # Nothing to do here

        elif numArgs == 1:

            # Evaluate argument
            #
            arg = args[0]

            if self.acceptsQueue(arg):

                self.setQueue(arg)

            else:

                self.setObject(arg)

        else:

            # Pass arguments to queue
            #
            self.setQueue(args)

    def __call__(self, obj):
        """
        Private method that is evoked when this instance is called.
        This method will perform an in-place update of the internal object.

        :type obj: Any
        :rtype: self
        """

        self.setObject(obj)
        return self

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

    def __eq__(self, other):
        """
        Private method that evaluates if this object is equivalent to the other object.

        :type other: Any
        :rtype: None
        """

        if isinstance(other, AFnBase):

            return self.object() == other.object()

        else:

            return self.object() == other

    def __ne__(self, other):
        """
        Private method that evaluates if this object is not equivalent to the other object.

        :type other: Any
        :rtype: None
        """

        if isinstance(other, AFnBase):

            return self.object() != other.object()

        else:

            return self.object() != other

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
            self.resetObject()

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

    def acceptsQueue(self, queue):
        """
        Evaluates if the supplied object can be used as a queue.

        :type queue: Any
        :rtype: bool
        """

        return isinstance(queue, (collections_abc.Sequence, collections_abc.Iterator)) and not isinstance(queue, string_types)

    def setQueue(self, queue):
        """
        Updates the object queue for this function set.

        :type queue: Union[List, Iterable]
        :rtype: None
        """

        # Check if queue is valid
        #
        if not self.acceptsQueue(queue):

            raise TypeError('setQueue() expects a sequence (%s given)!' % type(queue).__name__)

        # Update internal queue and go to first item
        #
        self._queue = deque(flatten(queue))
        self.next()

    def isDone(self):
        """
        Evaluates if the queue is empty.

        :rtype: bool
        """

        return len(self._queue) == 0 and not self.isValid()

    def next(self):
        """
        Attaches this function set to the next object in the queue.

        :rtype: object
        """

        # Check if queue is empty
        #
        if self.isDone():

            return

        # Check if queue still has items
        #
        queueCount = len(self._queue)

        if queueCount > 0:

            # Pop item from start of queue
            #
            obj = self._queue.popleft()
            success = self.trySetObject(obj)

            if success:

                return obj

            else:

                return self.next()  # Go to next item

        else:

            # Remove last item from function set
            #
            self.resetObject()
    # endregion
