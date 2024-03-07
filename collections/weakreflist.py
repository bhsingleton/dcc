import inspect
import weakref

from six.moves import collections_abc

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class WeakRefList(collections_abc.MutableSequence):
    """
    Overload of MutableSequence used to store weak references to objects.
    """

    # region Dunderscores
    __slots__ = ('__weakrefs__',)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(WeakRefList, self).__init__()

        # Declare private variables
        #
        self.__weakrefs__ = []

        # Check for any arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            self.extend(args[0])

    def __getitem__(self, index):
        """
        Private method that returns an indexed item.

        :type index: int
        :rtype: Any
        """

        return self.__weakrefs__[index]()

    def __setitem__(self, index, value):
        """
        Private method that updates an indexed item.

        :type index: int
        :type value: Any
        :rtype: None
        """

        self.__weakrefs__[index] = self.ref(value)

    def __delitem__(self, index):
        """
        Private method that removes an indexed item.

        :type index: int
        :rtype: None
        """

        del self.__weakrefs__[index]

    def __iter__(self):
        """
        Private method that returns a generator for this list.

        :rtype: iter
        """

        for ref in self.__weakrefs__:

            yield ref()

    def __len__(self):
        """
        Private method that evaluates the length of this list.

        :rtype: int
        """

        return len(self.__weakrefs__)

    def __contains__(self, item):
        """
        Private method that evaluates if this list contains the given item.

        :type item: Any
        :rtype: bool
        """

        return item in self.__weakrefs__
    # endregion

    # region Methods
    def append(self, value):
        """
        Appends a value to the end of the list.

        :type value: Any
        :rtype: None
        """

        self.__weakrefs__.append(self.ref(value))

    def insert(self, index, value):
        """
        Inserts a value at the specified index.

        :type index: int
        :type value: Any
        :rtype: None
        """

        self.__weakrefs__.insert(index, self.ref(value))

    def extend(self, values):
        """
        Appends a sequence of values to the end of this list.

        :type values: list[Any]
        :rtype: None
        """

        self.__weakrefs__.extend([self.ref(value) for value in values])

    def index(self, value):
        """
        Returns the index the supplied value is located at.

        :type value: Any
        :rtype: int
        """

        if not isinstance(value, weakref.ref):

            value = weakref.ref(value)

        return self.__weakrefs__.index(value)

    def remove(self, value):
        """
        Removes a value from this list.

        :type value: Any
        :rtype: None
        """

        self.__weakrefs__.remove(value)

    def ref(self, value):
        """
        Returns a ref to the supplied value.

        :type value: Any
        :rtype: weakref.ref
        """

        if inspect.ismethod(value):

            return weakref.WeakMethod(value, self.remove)

        else:

            return weakref.ref(value, self.remove)
    # endregion
