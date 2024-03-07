from six.moves import collections_abc
from .weakreflist import WeakRefList

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class NotifyDict(collections_abc.MutableMapping):
    """
    Overload of MutableMapping used to provide callback mechanisms for any dictionary changes.
    At this time there are only 2 callbacks: itemAdded and itemRemoved.
    We can add more as demand needs.
    """

    # region Dunderscores
    __slots__ = ('__items__', '__callbacks__')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key cls: Callable
        :rtype: None
        """

        # Call parent method
        #
        super(NotifyDict, self).__init__()

        # Declare private variables
        #
        self.__items__ = kwargs.get('cls', dict).__call__()
        self.__callbacks__ = {'itemAdded': WeakRefList(), 'itemRemoved': WeakRefList()}

        # Check for any arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            self.update(args[0])

    def __getitem__(self, key):
        """
        Private method that returns a key-value pair.

        :type key: Union[int, str]
        :rtype: Any
        """

        return self.__items__[key]

    def __setitem__(self, key, item):
        """
        Private method that updates a key-value pair.

        :type key: Union[int, str]
        :type item: Any
        :rtype: None
        """

        self.__items__[key] = item
        self.itemAdded(key, item)

    def __delitem__(self, key):
        """
        Private method that removes a key-value pair.

        :type key: Union[int, str]
        :rtype: None
        """

        self.pop(key)

    def __iter__(self):
        """
        Private method that returns a generator for this collection.

        :rtype: iter
        """

        return iter(self.__items__)

    def __len__(self):
        """
        Private method that evaluates the length of this collection.

        :rtype: int
        """

        return len(self.__items__)

    def pop(self, index):
        """
        Removes the key-value pair from this dictionary and returns it.

        :type index: int
        :rtype: FbxObject
        """

        item = self.__items__.pop(index)
        self.itemRemoved(item)

        return item
    # endregion

    # region Methods
    def keys(self):
        """
        Returns a keys view for this dictionary.

        :rtype: collections.abc.KeysView
        """

        return self.__items__.keys()

    def values(self):
        """
        Returns a values view for this dictionary.

        :rtype: collections.abc.ValuesView
        """

        return self.__items__.values()

    def items(self):
        """
        Returns an items view for this dictionary.

        :rtype: collections.abc.ItemsView
        """

        return self.__items__.items()

    def update(self, items):
        """
        Copies the supplied items into this dictionary.

        :rtype: None
        """

        for (key, value) in items.items():

            self.__setitem__(key, value)

    def clear(self):
        """
        Removes all items from this dictionary.

        :rtype: None
        """

        keys = list(self.keys())

        for key in reversed(keys):

            self.pop(key)

    def callbackNames(self):
        """
        Returns a list of callback names that can be used.

        :rtype: list[str]
        """

        return list(self.__callbacks__.keys())

    def addCallback(self, name, func):
        """
        Appends the supplied function to the specified callback group.

        :type name: str
        :type func: function
        :rtype: None
        """

        # Check if function has already been registered
        #
        callbacks = self.__callbacks__[name]

        if func not in callbacks:

            callbacks.append(func)

    def removeCallback(self, name, func):
        """
        Removes the supplied ID from the specified callback group.

        :type name: str
        :type func: function
        :rtype: None
        """

        # Check if function was registered
        #
        callbacks = self.__callbacks__[name]

        if func in callbacks:

            callbacks.remove(func)
    # endregion

    # region Notifies
    def itemAdded(self, index, item):
        """
        Notifies any functions if an item has been added.

        :type index: int
        :type item: Any
        :rtype: None
        """

        for func in self.__callbacks__['itemAdded']:

            func(index, item)

    def itemRemoved(self, item):
        """
        Notifies any functions if an item has been removed.

        :type item: Any
        :rtype: None
        """

        for func in self.__callbacks__['itemRemoved']:

            func(item)
    # endregion
