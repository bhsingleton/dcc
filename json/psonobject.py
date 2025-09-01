import inspect
import weakref

from typing import Any, Union, Tuple, List, Dict
from copy import copy, deepcopy
from . import pabcmeta
from ..python import annotationutils, stringutils, arrayutils
from ..decorators.classproperty import classproperty
from ..vendor.six import with_metaclass, string_types
from ..vendor.six.moves import collections_abc
from ..vendor.Qt import QtGui

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PSONObject(collections_abc.MutableMapping, metaclass=pabcmeta.PABCMeta):
    """
    Overload of `MutableMapping` that uses python properties as form of mapping.
    """

    # region Dunderscores
    __slots__ = ()

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(PSONObject, self).__init__()

    def __post_init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Check if argument is valid
        #
        numArgs = len(args)
        arg = args[0] if (numArgs == 1) else None

        if isinstance(arg, (collections_abc.MutableSequence, collections_abc.MutableMapping)):

            self.update(arg)

        else:

            self.update(kwargs)

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

        return self.keys()

    def __len__(self):
        """
        Private method that evaluates the number of items belonging to this collection.

        :rtype: int
        """

        return len(list(self.items()))

    def __getstate__(self):
        """
        Private method that returns a pickled object from this collection.

        :rtype: dict
        """

        # Iterate through properties
        # Be sure to only collect the writable properties
        #
        state = {'__class__': self.className, '__module__': self.moduleName}

        for (name, func) in self.iterProperties():

            # Inspect return type
            # If it doesn't have a return hint then ignore it
            #
            annotations = annotationutils.getAnnotations(func.fget)
            returnType = annotations.get('return', None)

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
        Private method that inherits the contents of the pickled object.

        :type state: dict
        :rtype: None
        """

        return self.update(state)

    def __copy__(self):
        """
        Private method that returns a shallow copy of this instance.

        :rtype: PSONObject
        """

        return self.copy()

    def __deepcopy__(self, memodict={}):
        """
        Private method that returns a deep copy of this instance.

        :rtype: PSONObject
        """

        return self.copy(deep=True)
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

    @classproperty
    def nullWeakReference(self):
        """
        Getter method that returns a null weak reference.

        :rtype: weakref.ref
        """

        return lambda: None
    # endregion

    # region Methods
    @staticmethod
    def isNullOrEmpty(value):
        """
        Evaluates if the supplied value is null or empty.

        :type value: Any
        :rtype: bool
        """

        return stringutils.isNullOrEmpty(value)

    @classmethod
    def isJsonCompatible(cls, T):
        """
        Evaluates whether the given type is json compatible.

        :type T: Union[Callable, Tuple[Callable]]
        :rtype: bool
        """

        if annotationutils.isParameterizedAlias(T):

            origin, parameters = annotationutils.decomposeAlias(T)
            return all([cls.isJsonCompatible(parameter) for parameter in parameters])

        else:

            return annotationutils.isBuiltinType(T) or hasattr(T, '__getstate__')

    @classmethod
    def iterBases(cls):
        """
        Returns a generator that yields the subclasses from this class.

        :rtype: Iterator[Callable]
        """

        return reversed(inspect.getmro(cls))

    @classmethod
    def iterProperties(cls, readable=False, writable=True, deletable=False):
        """
        Returns a generator that yields the properties from this class.

        :type readable: bool
        :type writable: bool
        :type deletable: bool
        :rtype: Iterator[str, property]
        """

        # Iterate through subclasses
        #
        for base in cls.iterBases():

            # Iterate through members
            #
            for (name, member) in base.__dict__.items():

                # Inspect member
                #
                if not isinstance(member, property):

                    continue

                # Check if property is readable
                #
                if readable and callable(member.fget):

                    yield name, member
                    continue

                # Check if property is writable
                #
                if writable and callable(member.fset):

                    yield name, member
                    continue

                # Check if property is deletable
                #
                if deletable and callable(member.fdel):

                    yield name, member
                    continue

    @classmethod
    def getProperties(cls, readable=False, writable=True, deletable=False):
        """
        Returns a dictionary of properties from this class.

        :type readable: bool
        :type writable: bool
        :type deletable: bool
        :rtype: Dict[str, property]
        """

        return dict(cls.iterProperties(readable=readable, writable=writable, deletable=deletable))

    @classmethod
    def createEditor(cls, name, parent=None):
        """
        Returns a Qt editor for the specified property.

        :type name: str
        :type parent: Union[QtWidgets.QWidget, None]
        :rtype: Union[QtWidgets.QWidget, None]
        """

        return None

    @classmethod
    def icon(cls):
        """
        Returns a Qt icon for this class.

        :rtype: Union[QtGui.QIcon, None]
        """

        return QtGui.QIcon(':data/icons/dict.svg')

    def weakReference(self):
        """
        Returns a weak reference to this object.

        :rtype: weakref.ref
        """

        return weakref.ref(self)

    def keys(self, readable=False, writable=True, deletable=False):
        """
        Returns a key view for this collection.

        :type readable: bool
        :type writable: bool
        :type deletable: bool
        :rtype: collections_abc.KeysView
        """

        for (name, obj) in self.iterProperties(readable=readable, writable=writable, deletable=deletable):

            yield name

    def values(self, readable=False, writable=True, deletable=False):
        """
        Returns a values view for this collection.

        :type readable: bool
        :type writable: bool
        :type deletable: bool
        :rtype: collections_abc.ValuesView
        """

        for (name, obj) in self.iterProperties(readable=readable, writable=writable, deletable=deletable):

            yield obj.fget(self)

    def items(self, readable=False, writable=True, deletable=False):
        """
        Returns an items view for this collection.

        :type readable: bool
        :type writable: bool
        :type deletable: bool
        :rtype: collections_abc.ItemsView
        """

        for (name, obj) in self.iterProperties(readable=readable, writable=writable, deletable=deletable):

            yield name, obj.fget(self)

    def get(self, key, default=None):
        """
        Returns the value from the associated key.
        If no key exists then the default value is returned instead!

        :type key: str
        :type default: Any
        :rtype: Any
        """

        return getattr(self, key, default)

    def update(self, obj):
        """
        Copies any items from the supplied dictionary to this collection.

        :type obj: Dict[str, Any]
        :rtype: None
        """

        # Evaluate supplied object
        #
        if not isinstance(obj, (collections_abc.MutableSequence, collections_abc.MutableMapping)):

            raise TypeError(f'update() expects a dict ({type(obj).__name__} given)!')

        # Iterate through key-value pairs
        #
        iterator = obj.items() if isinstance(obj, collections_abc.MutableMapping) else iter(obj)

        for pair in iterator:

            # Evaluate key-value pair
            #
            numItems = len(pair) if isinstance(pair, collections_abc.Sequence) else 0

            if numItems != 2:

                continue

            # Check if key exists
            #
            key, value = pair
            hasMember = hasattr(self.__class__, key)

            if not hasMember:

                continue

            # Check if key is associated with a property
            #
            member = getattr(self.__class__, key)
            isProperty = isinstance(member, property)

            if not isProperty:

                continue

            # Check if property is mutable
            #
            isMutable = callable(member.fset)

            if isMutable:

                member.fset(self, value)

            else:

                continue

    def copy(self, deep=False):
        """
        Returns a copy of this instance.

        :type deep: bool
        :rtype: PSONObject
        """

        # Create new instance
        # Iterate through writable properties
        #
        instance = self.__class__()
        func = deepcopy if deep else copy

        for (name, prop) in self.iterProperties():

            # Inspect property value
            #
            value = prop.fget(self)

            isArray = arrayutils.isArray(value)
            isMap = arrayutils.isHashMap(value)

            if isArray:

                # Check if a deep copy is required
                #
                if deep:

                    cls = type(value)
                    setattr(instance, name, cls(map(func, value)))

                else:

                    continue

            elif isMap:

                # Check if a deep copy is required
                #
                if deep:

                    cls = type(value)
                    setattr(instance, name, cls({key: func(value) for (key, value) in value.items()}))

                else:

                    continue

            else:

                setattr(instance, name, value)

        return instance
    # endregion
