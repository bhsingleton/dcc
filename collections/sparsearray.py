import types

from six import integer_types
from six.moves import collections_abc

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class SparseArray(collections_abc.MutableSequence):
    """
    Overload of MutableSequence used as a sparse array container.
    Uses an internal sorted dictionary to track items.
    """

    # region Dunderscores
    __slots__ = ('__items__',)

    def __init__(self, *args):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(SparseArray, self).__init__()

        # Declare class variables
        #
        self.__items__ = {}

        # Check for any arguments
        #
        numArgs = len(args)

        if numArgs > 0:

            self.extend(args[0])

    def __str__(self):
        """
        Private method that returns a string representation of this instance.

        :rtype: str
        """

        return str(self.toList())

    def __call__(self, index):
        """
        Private method that returns a physically indexed item.

        :type index: int
        :rtype: Any
        """

        return self.getItemByPhysicalIndex(index)

    def __getitem__(self, index):
        """
        Private method that returns a logically indexed item.

        :type index: int
        :rtype: Any
        """

        return self.getItemByLogicalIndex(index)

    def __setitem__(self, index, item):
        """
        Private method that updates an indexed child.

        :type index: int
        :type item: object
        :rtype: None
        """

        # Check value type
        #
        if not isinstance(index, integer_types):

            raise TypeError('__setitem__() expects an int (%s given)!' % type(index).__name__)

        # Assign item to array
        #
        self.__items__[index] = item

        # Check if array requires re-sorting
        #
        indices = list(self.__items__.keys())
        lastIndex = indices[-1]

        if 0 <= index < lastIndex:

            self.__items__ = dict(sorted(self.__items__.items()))

    def __delitem__(self, index):
        """
        Private method that deletes an indexed child.

        :type index: int
        :rtype: None
        """

        if self.hasIndex(index):

            del self.__items__[index]

        else:

            raise IndexError('__delitem__() array index out of range!')

    def __contains__(self, item):
        """
        Private method that evaluates if the supplied item is in this array.

        :type item: object
        :rtype: bool
        """

        return item in self.__items__.values()

    def __iter__(self):
        """
        Private method that returns a generator for this array.

        :rtype: iter
        """

        return self.__items__.values()

    def __len__(self):
        """
        Private method that evaluates the number of children belonging to this object.

        :rtype: int
        """

        return len(self.__items__)
    # endregion

    # region Methods
    def insert(self, index, item):
        """
        Inserts an item at the specified index.

        :type index: int
        :type item: object
        :rtype: None
        """

        self.__setitem__(index, item)

    def append(self, item):
        """
        Appends an item to the end of this array.

        :type item: object
        :rtype: None
        """

        self.__setitem__(self.nextIndex(), item)

    def appendIfUnique(self, item):
        """
        Appends an items to the end of this array only if it doesn't exist.

        :type item: object
        :rtype: None
        """

        if not self.__contains__(item):

            self.append(item)

    @staticmethod
    def isKeyValuePair(obj):
        """
        Evaluates if the supplied object is a key-value pair.

        :type obj: Any
        :rtype: bool
        """

        # Check object type
        #
        if not isinstance(obj, tuple):

            return False

        # Check number of items
        #
        numArgs = len(obj)

        if numArgs != 2:

            return False

        # Check item types
        #
        key, value = obj

        if isinstance(key, integer_types):

            return True

        else:

            return False

    def extend(self, items):
        """
        Appends the supplied items onto this array.

        :type items: list
        :rtype: None
        """

        # Check items type
        #
        if isinstance(items, collections_abc.MutableSequence):

            # Append items
            #
            for item in items:

                self.append(item)

        elif isinstance(items, types.GeneratorType):

            # Iterate through generator
            #
            for item in items:

                # Check if this is a key-value pair
                #
                if self.isKeyValuePair(item):

                    self.__setitem__(item[0], item[1])

                else:

                    self.append(item)

        else:

            raise TypeError('extend() expects a sequence (%s given)!' % type(items).__name__)

    def pop(self, index, default=None):
        """
        Removes an item from this array and returns it.

        :type index: int
        :type default: Any
        :rtype: Any
        """

        return self.__items__.pop(index, default)

    def remove(self, item):
        """
        Removes the supplied item from this array.

        :type item: object
        :rtype: None
        """

        self.__delitem__(self.index(item))

    def clear(self):
        """
        Removes all items from this array.

        :rtype: None
        """

        self.__items__.clear()

    def index(self, item):
        """
        Returns the index the supplied item is located at.

        :type item: object
        :rtype: int
        """

        try:

            keys = list(self.__items__.keys())
            values = list(self.__items__.values())

            physicalIndex = values.index(item)
            return keys[physicalIndex]

        except ValueError as exception:

            log.debug(exception)
            raise ValueError('index() %s is not in array!' % item)

    def hasIndex(self, index):
        """
        Evaluates if this array contains the given index.

        :type index: int
        :rtype: bool
        """

        return index in self.indices()

    def indices(self):
        """
        Returns a sorted list of indices currently in use.

        :rtype: list[int]
        """

        return self.__items__.keys()

    def firstIndex(self):
        """
        Returns the first known index currently in use.

        :rtype: int
        """

        if self.__len__() > 0:

            return list(self.indices())[0]

        else:

            return None

    def lastIndex(self):
        """
        Returns the last known index currently in use.

        :rtype: int
        """

        if self.__len__() > 0:

            return list(self.indices())[-1]

        else:

            return None

    def values(self):
        """
        Returns a list of values currently in use.

        :rtype: list
        """

        return self.__items__.values()

    def items(self):
        """
        Returns a list of key-value pairs that make up this sparse array.

        :rtype: list
        """

        return self.__items__.items()

    def getItemByLogicalIndex(self, index):
        """
        Returns a logically indexed item from this array.

        :type index: int
        :rtype: Any
        """

        # Check value type
        #
        if not isinstance(index, integer_types):

            raise TypeError('getItemByLogicalIndex() expects an int (%s given)!' % type(index).__name__)

        # Return indexed item
        #
        if self.hasIndex(index):

            return self.__items__[index]

        else:

            raise IndexError('getItemByLogicalIndex() array index out of range!')

    def tryGetItemByLogicalIndex(self, index, default=None):
        """
        Returns a logically indexed item from this array.
        An optional default can be supplied in case this fails.

        :type index: int
        :type default: Any
        :rtype: Any
        """

        try:

            return self.getItemByLogicalIndex(index)

        except (IndexError, TypeError) as exception:

            log.debug(exception)
            return default

    def getItemByPhysicalIndex(self, index):
        """
        Returns a physically indexed item from this array.

        :type index: int
        :rtype: Any
        """

        # Check value type
        #
        if not isinstance(index, integer_types):

            raise TypeError('getItemByPhysicalIndex() expects an int (%s given)!' % type(index).__name__)

        # Check if index is in range
        #
        indices = list(self.indices())
        numIndices = len(indices)

        if 0 <= index < numIndices:

            return self.getItemByLogicalIndex(indices[index])

        else:

            raise IndexError('getItemByPhysicalIndex() array index out of range!')

    def tryGetItemByPhysicalIndex(self, index, default=None):
        """
        Returns a physically indexed item from this array.
        An optional default can be supplied in case this fails.

        :type index: int
        :type default: Any
        :rtype: Any
        """

        try:

            return self.getItemByPhysicalIndex(index)

        except (IndexError, TypeError) as exception:

            log.debug(exception)
            return default

    @property
    def isSequential(self):
        """
        Getter method that evaluates whether the indices are consecutive.

        :rtype: bool
        """

        return list(self.indices()) == list(range(self.__len__()))

    def nextIndex(self):
        """
        Returns the next index at the end of this array.

        :rtype: int
        """

        if self.__len__() > 0:

            return self.lastIndex() + 1

        else:

            return 0

    def nextAvailableIndex(self):
        """
        Returns the next available index in this array.

        :rtype: int
        """

        # Look for a mismatch
        #
        for (physicalIndex, logicalIndex) in enumerate(self.indices()):

            if physicalIndex != logicalIndex:

                return physicalIndex

        # Return next index
        #
        return self.nextIndex()

    def toList(self, **kwargs):
        """
        Converts this sparse array into a list.
        An optional fill value can be supplied to populate missing indices.

        :keyword fill: Any
        :rtype: list[Any]
        """

        # Check if list should be filled
        #
        if 'fill' in kwargs:

            fill = kwargs['fill']
            return [self.tryGetItemByPhysicalIndex(i, default=fill) for i in range(self.lastIndex())]

        else:

            return list(self.values())

    def toDict(self):
        """
        Converts this sparse array into a dictionary.

        :rtype: dict
        """

        return dict(self.items())
    # endregion
