from six.moves import collections_abc

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class HashTable(collections_abc.MutableMapping):
    """
    Overload of MutableMapping used as a hash table.
    This collection stores objects via hash code.
    Whereas string keys point to hash codes that way the values are always unique.
    """

    # region Dunderscores
    __slots__ = ('__keys__', '__values__')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(HashTable, self).__init__()

        # Declare class variables
        #
        self.__keys__ = {}
        self.__values__ = {}

        # Check for any arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            self.update(args[0])

    def __str__(self):
        """
        Private method that returns a string representation of this instance.

        :rtype: str
        """

        return str(self.__values__)

    def __getitem__(self, key):
        """
        Private method that returns an indexed item.

        :type key: Union[str, int]
        :rtype: object
        """

        # Check key type
        #
        if isinstance(key, int):

            return self.__values__[key]

        elif isinstance(key, str):

            return self.__values__[self.__keys__[key]]

        else:

            raise IndexError('__getitem__() expects either an int or str (%s given)!' % type(key).__name__)

    def __setitem__(self, key, value):
        """
        Private method that updates an indexed item.

        :type key: Union[str, int]
        :type value: object
        :rtype: None
        """

        # Check key type
        #
        if isinstance(key, int):

            self.__values__[key] = value

        elif isinstance(key, str):

            hashCode = hash(value)

            self.__keys__[key] = hashCode
            self.__values__[hashCode] = value

        else:

            raise IndexError('__setitem__() expects either an int or str (%s given)!' % type(key).__name__)

    def __delitem__(self, key):
        """
        Private method that deletes an indexed item.

        :type key: Union[str, int]
        :rtype: None
        """

        # Check key type
        #
        if isinstance(key, int):

            del self.__values__[key]

        elif isinstance(key, str):

            hashCode = self.__keys__[key]

            del self.__keys__[key]
            del self.__values__[hashCode]

        else:

            raise IndexError('__delitem__() expects either an int or str (%s given)!' % type(key).__name__)

    def __contains__(self, value):
        """
        Private method that evaluates if the supplied item is in this array.

        :type value: object
        :rtype: bool
        """

        return value in self.__values__.values()

    def __iter__(self):
        """
        Private method that returns a generator for this object.

        :rtype: iter
        """

        return iter(self.__values__)

    def __len__(self):
        """
        Private method that evaluates the number of children belonging to this object.

        :rtype: int
        """

        return len(self.__values__)
    # endregion

    # region Methods
    def get(self, key, default=None):
        """
        Returns an indexed item with an optional default in case there's no item.

        :type key: Union[str, int]
        :type default: object
        :rtype: object
        """

        # Check key type
        #
        if isinstance(key, int):

            return self.__values__.get(key, default)

        elif isinstance(key, str):

            return self.__values__.get(self.__keys__.get(key, 0), default)

        else:

            raise IndexError('get() expects either an int or str (%s given)!' % type(key).__name__)

    def update(self, items):
        """
        Copies the items from the supplied dictionary into this table.

        :type items: MutableMapping
        :rtype: None
        """

        for (key, value) in items.items():

            self.__setitem__(key, value)

    def keys(self):
        """
        Returns a list of keys currently in use.

        :rtype: collections.KeysView
        """

        return self.__keys__.keys()

    def hashes(self):
        """
        Returns a list of hashes currently in use.

        :rtype: collections.KeysView
        """

        return self.__values__.keys()

    def values(self):
        """
        Returns a list of values currently in use.

        :rtype: collections.ValuesView
        """

        return self.__values__.values()

    def items(self):
        """
        Returns a list of key-value pairs that make up this sparse array.

        :rtype: collections.ItemsView
        """

        return {key: self.__getitem__(key) for key in self.keys()}.items()
    # endregion
