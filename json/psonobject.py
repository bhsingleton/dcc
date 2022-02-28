import inspect
import weakref
import typing
import copy

from abc import ABCMeta
from six.moves.collections_abc import MutableMapping, MutableSequence
from dcc.decorators import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PSONObject(MutableMapping):
    """
    Overload of MutableMapping used to provide a serialization routine for json.
    """

    # region Dunderscores
    __metaclass__ = ABCMeta
    __slots__ = ('__weakref__',)
    __builtins__ = (bool, int, float, str, MutableSequence, MutableMapping)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.
        """

        # Call parent method
        #
        super(PSONObject, self).__init__()

        # Check for any arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            self.update(args[0])

    def __getitem__(self, key):
        """
        Private method that returns an indexed item.

        :type key: str
        :rtype: object
        """

        return getattr(self, key)

    def __setitem__(self, key, value):
        """
        Private method that updates an indexed item.

        :type key: str
        :type value: object
        :rtype: None
        """

        setattr(self, key, value)

    def __delitem__(self, key):
        """
        Private method that deletes an indexed item.

        :type key: str
        :rtype: None
        """

        delattr(self, key)

    def __iter__(self):
        """
        Private method that returns a generator for this collection.

        :rtype: iter
        """

        return iter(self.properties())

    def __len__(self):
        """
        Private method that evaluates the number of items belonging to this collection.

        :rtype: int
        """

        return len(self.properties())

    def __getstate__(self):
        """
        Private method that returns a screenshot of this collection.

        :rtype: dict
        """

        # Iterate through properties
        # Be sure to only collect the writable properties
        #
        state = {'__name__': self.className, '__module__': self.moduleName}

        for (name, func) in self.iterProperties(readable=True, writable=True):

            # Inspect return type
            # If it doesn't have a return hint then ignore it
            #
            returnType = func.fget.__annotations__.get('return')

            if returnType is None:

                continue

            # Check if return type is json compatible
            #
            if not self.isJsonCompatible(returnType):

                continue

            # Assign item to state object
            #
            state[name] = func.fget(self)

        return state

    def __setstate__(self, state):
        """
        Private method that updates this collection from the supplied screenshot.

        :type state: dict
        :rtype: None
        """

        return self.update(state)

    def __copy__(self):
        """
        Private method that returns a copy of this instance.

        :rtype: PropertyMapping
        """

        # Create new instance
        # Iterate through writable properties
        #
        instance = self.__class__()

        for (name, func) in self.iterProperties(readable=True, writable=True):

            # Inspect property value
            # Mutable sequences will require a deep copy
            #
            value = func.fget(self)

            if isinstance(value, MutableSequence):

                setattr(instance, name, [copy.copy(x) for x in value])

            elif isinstance(value, MutableMapping):

                setattr(instance, name, {key: copy.copy(value) for (key, value) in value.items()})

            else:

                setattr(instance, name, copy.copy(value))

        return instance
    # endregion

    # region Properties
    @classproperty
    def className(cls):
        """
        Getter method used to return the class name.

        :rtype: str
        """

        return cls.__name__

    @classproperty
    def moduleName(cls):
        """
        Getter method used to return the class module.

        :rtype: str
        """

        return cls.__module__

    @classproperty
    def nullWeakReference(self):
        """
        Getter method that returns a null weak reference.

        :rtype: weakref.ref
        """

        return lambda: None
    # endregion

    # region Methods
    @classmethod
    def iterProperties(cls, readable=True, writable=False, deletable=False):
        """
        Returns a generator for iterating over properties derived from this class.

        :type readable: bool
        :type writable: bool
        :type deletable: bool
        :rtype: iter
        """

        # Iterate through members
        #
        members = inspect.getmembers(cls, lambda x: isinstance(x, property))

        for (name, func) in members:

            # Check if property is readable
            #
            if readable and func.fget is None:
                continue

            # Check if property is writable
            #
            if writable and func.fset is None:
                continue

            # Check if property is deletable
            #
            if deletable and func.fdel is None:
                continue

            # Yield property
            #
            yield name, func

    @classmethod
    def properties(cls, readable=True, writable=False, deletable=False):
        """
        Returns a dictionary of properties derived from this class.

        :type readable: bool
        :type writable: bool
        :type deletable: bool
        :rtype: dict[str:property]
        """

        return dict(cls.iterProperties(readable=readable, writable=writable, deletable=deletable))

    @classmethod
    def isBuiltinType(cls, T):
        """
        Evaluates whether the supplied type is derived from a builtin type.

        :type T: type
        :rtype: bool
        """

        return any([issubclass(T, x) for x in cls.__builtins__])

    @classmethod
    def isJsonCompatible(cls, T):
        """
        Evaluates whether the given type is json compatible.

        :type T: Union[class, type]
        :rtype: bool
        """

        # Check if this is a class
        #
        if inspect.isclass(T):

            return cls.isBuiltinType(T)

        elif isinstance(T, typing.Sequence):

            return all([cls.isBuiltinType(x) for x in T.__args__])

        else:

            return False

    def weakReference(self):
        """
        Returns a weak reference to this object.

        :rtype: weakref.ref
        """

        return weakref.ref(self)

    def keys(self):
        """
        Returns a key view for this collection.

        :rtype: collections.abc.KeysView
        """

        return self.__getstate__().keys()

    def values(self):
        """
        Returns a values view for this collection.

        :rtype: collections.abc.ValuesView
        """

        return self.__getstate__().values()

    def items(self):
        """
        Returns an items view for this collection.

        :rtype: collections.abc.ItemsView
        """

        return self.__getstate__().items()

    def update(self, items):
        """
        Copies any items from the supplied dictionary to this collection.

        :type items: dict
        :rtype: None
        """

        # Iterate through items
        #
        for (key, value) in items.items():

            # Check if collection has property
            #
            if hasattr(self, key):

                self.__setitem__(key, value)

            else:

                continue
    # endregion
