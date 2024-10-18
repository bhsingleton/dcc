from dataclasses import dataclass, fields, replace
from abc import ABCMeta, abstractmethod
from collections.abc import Mapping, KeysView, ValuesView, ItemsView
from ..decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class ADC(Mapping, metaclass=ABCMeta):
    """
    Overload of `Mapping` used to outline abstract data class behaviour.
    """

    # region Dunderscores
    def __getstate__(self):
        """
        Private method that returns a pickled object from this collection.

        :rtype: dict
        """

        # Iterate through items
        #
        state = {'__name__': self.className, '__module__': self.moduleName}

        for (key, value) in self.items():

            # Check if value is serializable
            #
            if hasattr(value, '__getstate__'):

                state[key] = value.__getstate__()

            else:

                state[key] = value

        return state

    def __setstate__(self, state):
        """
        Private method that inherits the contents of the pickled object.

        :type state: dict
        :rtype: None
        """

        self.update(state)

    def __getitem__(self, key):
        """
        Private method that returns an indexed item.

        :type key: Union[str, int]
        :rtype: Any
        """

        # Evaluate key type
        #
        if isinstance(key, str):

            return getattr(self, key)

        elif isinstance(key, int):

            dataFields = fields(self.__class__)
            numDataFields = len(dataFields)

            if 0 <= key < numDataFields:

                return getattr(self, dataFields[key].name)

            else:

                raise IndexError('__getitem__() index is out of range!')

        elif isinstance(key, slice):

            start = key.start if isinstance(key.start, int) else 0
            stop = key.stop if isinstance(key.stop, int) else len(self)
            step = key.step if isinstance(key.step, int) else 1

            return [self.__getitem__(i) for i in range(start, stop, step)]

        else:

            raise TypeError(f'__getitem__() expects either a str or int ({type(key).__name__} given)!')

    def __setitem__(self, key, value):
        """
        Private method that updates an indexed item.

        :type key: Union[str, int]
        :type value: float
        :rtype: None
        """

        # Evaluate key type
        #
        if isinstance(key, str):

            return setattr(self, key, value)

        elif isinstance(key, int):

            dataFields = fields(self.__class__)
            numDataFields = len(dataFields)

            if 0 <= key < numDataFields:

                return setattr(self, dataFields[key].name, value)

            else:

                raise IndexError('__setitem__() index is out of range!')

        else:

            raise TypeError(f'__setitem__() expects either a str or int ({type(key).__name__} given)!')

    def __contains__(self, item):
        """
        Private method that evaluates if this instance contains the supplied item.

        :type item: Any
        :rtype: bool
        """

        return item in self.keys()

    def __eq__(self, other):
        """
        Private method that implements the not equal operator.

        :type other: Any
        :rtype: bool
        """

        return self is other

    def __ne__(self, other):
        """
        Private method that implements the equal operator.

        :type other: Any
        :rtype: bool
        """

        return self is not other

    def __len__(self):
        """
        Private method that evaluates the size of this instance.

        :rtype: int
        """

        return len(list(self.fields()))

    def __iter__(self):
        """
        Private method that returns a generator that yields keys from this instance.

        :rtype: Iterator[str]
        """

        return self.keys()

    def __copy__(self):
        """
        Private method that returns a shallow copy of this instance.

        :rtype: ADC
        """

        return self.copy()

    def __deepcopy__(self, memodict={}):
        """
        Private method that returns a deep copy of this instance.

        :rtype: ADC
        """

        return self.copy()
    # endregion

    # region Properties
    @classproperty
    def className(cls):
        """
        Getter method that returns the class name.

        :rtype: str
        """

        return cls.__name__

    @classproperty
    def moduleName(cls):
        """
        Getter method that returns the class module.

        :rtype: str
        """

        return cls.__module__
    # endregion

    # region Methods
    @classmethod
    def fields(cls):
        """
        Returns a generator that yields fields from this instance.

        :rtype: Iterator[dataclasses.Field]
        """

        return iter(fields(cls))

    def keys(self):
        """
        Returns a generator that yields keys from this instance.

        :rtype: KeysView
        """

        for field in self.fields():

            yield field.name

    def values(self):
        """
        Returns a generator that yields values from this instance.

        :rtype: ValuesView
        """

        for key in self.keys():

            yield getattr(self, key)

    def items(self):
        """
        Returns a generator that yields items from this instance.

        :rtype: ItemsView
        """

        for key in self.keys():

            yield key, getattr(self, key)

    def get(self, key, default=None):
        """
        Returns indexed item.
        If no item exists then the default value is returned instead.

        :type key: Union[int, str]
        :type default: Any
        :rtype: Any
        """

        return getattr(self, key, default)

    def update(self, obj):
        """
        Copies the values from the supplied object to this instance.

        :type obj: dict
        :rtype: None
        """

        for (key, value) in obj.items():

            setattr(self, key, value)

    def copy(self, **kwargs):
        """
        Returns a copy of this instance.
        Any keyword arguments supplied will be passed to the update method.

        :rtype: ADC
        """

        copy = replace(self)
        copy.update(kwargs)

        return copy
    # endregion
