import inspect
import weakref

from Qt import QtGui
from six import string_types, integer_types
from six.moves import collections_abc
from ...python import stringutils, annotationutils, funcutils
from ...generators.flatten import flatten

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QPSONPath(collections_abc.Sequence):
    """
    Base class used to interface with python paths from inside the Qt item model.
    """

    # region Dunderscores
    __slots__ = ('_path', '_model')
    __builtin_types__ = (bool, int, float, str, collections_abc.MutableSequence, collections_abc.MutableMapping)

    def __init__(self, *args, **kwargs):
        """
        Private method that is called after a new instance is created.

        :key model: qpsonitemmodel.QPSONItemModel
        :rtype: None
        """

        # Call parent method
        #
        super(QPSONPath, self).__init__()

        # Declare private methods
        #
        self._model = lambda: None
        self._path = ()

        # Check if an item model was supplied
        #
        model = kwargs.get('model')

        if model is not None:

            self._model = weakref.ref(model)
            self._path = tuple(self.flatten(*args))

    def __hash__(self):
        """
        Private method that returns a hashable representation of this path.

        :rtype: str
        """

        return abs(hash(self._path))

    def __repr__(self):
        """
        Private method that returns a string representation of this object.

        :rtype: str
        """

        return '<{path} path at {identifier}>'.format(path=self.toString(), identifier=hex(id(self)))

    def __getitem__(self, index):
        """
        Private method that returns an indexed segment.

        :type index: int
        :rtype: Union[str, int]
        """

        if isinstance(index, integer_types):

            return self._path[index]

        elif isinstance(index, slice):

            return QPSONPath(self._path[index], model=self.model)

        else:

            raise IndexError('__getitem__() expects an integer (%s given)!' % type(index).__name__)

    def __add__(self, other):
        """
        Private method called whenever addition is performed on this instance.

        :type other: Any
        :rtype: PSONPath
        """

        return QPSONPath(self._path, other, model=self.model)

    def __iter__(self):
        """
        Private method that returns a generator for yielded path segments.

        :rtype: iter
        """

        return iter(self._path)

    def __len__(self):
        """
        Private method that evaluates the length of this path.

        :rtype: int
        """

        return len(self._path)
    # endregion

    # region Properties
    @property
    def model(self):
        """
        Getter method that returns the associated item model.

        :rtype: qpsonitemmodel.QPSONItemModel
        """

        return self._model()

    @property
    def root(self):
        """
        Getter method that returns the root of this path.

        :rtype: object
        """

        if self.model is not None:

            return self.model.invisibleRootItem

        else:

            return None
    # endregion

    # region Methods
    @classmethod
    def flatten(cls, *items):
        """
        Returns a generator that yields flattened path segments.

        :rtype: Iterator[Union[int, str]]
        """

        # Iterate through items
        #
        for item in flatten(*items):

            # Evaluate item type and size
            #
            if isinstance(item, (*integer_types, *string_types)) and not stringutils.isNullOrEmpty(item):

                yield item

            else:

                continue

    def isValid(self):
        """
        Evaluates if this path is valid.

        :rtype: bool
        """

        return self.root is not None

    def toString(self):
        """
        Returns a string representation of this path.

        :rtype: str
        """

        # Evaluate path length
        #
        pathLength = len(self._path)

        if pathLength == 0:

            return ''

        # Evaluate last index type
        #
        lastIndex = self._path[-1]

        if isinstance(lastIndex, integer_types):

            # Check if property can be included
            #
            if pathLength >= 2:

                return '{name}[{index}]'.format(name=self._path[-2], index=lastIndex)

            else:

                return '[{index}]'.format(index=lastIndex)

        elif isinstance(lastIndex, string_types):

            return lastIndex

        else:

            raise TypeError('toString() expects a valid path!')

    def isRoot(self):
        """
        Evaluates if this is a root path.

        :rtype: bool
        """

        # Check if root item is valid
        #
        if self.model.invisibleRootItem is None:

            return False

        # Evaluate path length
        #
        pathLength = len(self._path)

        if pathLength == 0 and stringutils.isNullOrEmpty(self.model.invisibleRootProperty):

            return True

        elif pathLength == 1 and not stringutils.isNullOrEmpty(self.model.invisibleRootProperty):

            return self._path[0] == self.model.invisibleRootProperty

        else:

            return False

    def hasParent(self):
        """
        Evaluates if this path has a parent.

        :rtype: bool
        """

        return len(self) >= 1

    def parent(self):
        """
        Returns the parent path for this instance.
        If this path has no parent then none is returned!

        :rtype: PSONPath
        """

        # Evaluate path length
        #
        if self.hasParent():

            return self[:-1]

        else:

            return None

    def supportsChildren(self):
        """
        Evaluates if this path can support children.

        :rtype: bool
        """

        return self.isArray() or self.isMapping()

    def hasAttr(self, name):
        """
        Evaluates if the associated object has the specified name.

        :type name: str
        :rtype: bool
        """

        return hasattr(self.value(), name)

    def icon(self):
        """
        Returns the icon associated with this path type.

        :rtype: QtGui.QIcon
        """

        # Check if type is valid
        #
        alias = self.type()
        origin, parameters = annotationutils.decomposeAlias(alias)

        if origin is None:

            return QtGui.QIcon()

        # Inspect base classes
        #
        if issubclass(origin, collections_abc.MutableSequence):

            return QtGui.QIcon(':data/icons/list.svg')

        elif issubclass(origin, collections_abc.MutableMapping):

            return QtGui.QIcon(':data/icons/dict.svg')

        else:

            # Check if icon exists
            #
            bases = inspect.getmro(origin)

            for base in bases:

                typeName = getattr(base, '__name__', '')
                icon = QtGui.QIcon(':data/icons/{typeName}.svg'.format(typeName=typeName))

                if not icon.isNull():

                    return icon

                else:

                    continue

            return QtGui.QIcon()

    def type(self, decomposeAliases=False):
        """
        Returns the value type from this path.

        :type decomposeAliases: bool
        :rtype: type
        """

        # Check if getter is valid
        #
        getter, setter = self.accessors()

        if not callable(getter):

            return type(None), tuple() if decomposeAliases else type(None)

        # Check if return type requires decomposing
        #
        returnType = annotationutils.getReturnType(getter)

        if decomposeAliases:
            
            return annotationutils.decomposeAlias(returnType)

        else:

            return returnType

    def acceptsType(self, otherType):
        """
        Evaluates if this path would accept the given type.

        :type otherType: type
        :rtype: bool
        """

        T = self.type()
        return T == otherType and T is not None

    def accessors(self):
        """
        Returns the property accessors from this path.

        :rtype: Tuple[function, function]
        """

        # Get last string item
        #
        strings = [x for x in self._path if isinstance(x, string_types)]
        numStrings = len(strings)

        if numStrings == 0:

            return None, None

        # Evaluate path up to string
        #
        lastString = strings[-1]
        lastIndex = self._path.index(lastString)

        path = QPSONPath(*self._path[:lastIndex], model=self.model)
        obj = path.eval()

        return funcutils.getPropertyAccessors(obj, lastString)

    def value(self):
        """
        Returns the value at the end of this path.

        :rtype: Any
        """

        return self.eval(default=None)

    def setValue(self, value):
        """
        Updates the value at the end of this path.

        :type value: Any
        :rtype: None
        """

        # Check if setter is callable
        #
        getter, setter = self.accessors()

        if not callable(setter):

            log.warning('Unable to set value @ %s' % self)
            return

        # Check if indexer is required
        #
        if self.isElement():

            array = getter()
            index = self._path[-1]

            array[index] = value

        else:

            setter(value)

    def isArray(self):
        """
        Evaluates if the path represents an array.

        :rtype: bool
        """

        alias, parameters = self.type(decomposeAliases=True)
        numParameters = len(parameters)

        if self.isElement() and numParameters == 1:

            return issubclass(parameters[0], collections_abc.MutableSequence) and not issubclass(parameters[0], string_types)

        else:

            return issubclass(alias, collections_abc.MutableSequence) and not issubclass(alias, string_types)

    def isMapping(self):
        """
        Evaluates if the path represents a mapping object.

        :rtype: bool
        """

        alias, parameters = self.type(decomposeAliases=True)
        numParameters = len(parameters)

        if self.isElement() and numParameters == 1:

            return issubclass(parameters[0], collections_abc.MutableMapping)

        else:

            return issubclass(alias, collections_abc.MutableMapping)

    def isElement(self):
        """
        Evaluates if this path represents an array element.

        :rtype: bool
        """

        if len(self._path) > 0:

            return isinstance(self._path[-1], integer_types)

        else:

            return False

    def isResizable(self):
        """
        Evaluates if this path is resizable.

        :rtype: bool
        """

        alias = self.type()
        origin, parameters = annotationutils.decomposeAlias(alias)

        if issubclass(origin, collections_abc.MutableSequence) and len(parameters) == 1:

            return issubclass(parameters[0], self.__builtin_types__)

        else:

            return False

    def isEditable(self):
        """
        Evaluates if this path is editable.

        :rtype: bool
        """

        # Evaluate if setter exists
        #
        getter, setter = self.accessors()

        if not callable(setter):

            return False

        # Evaluate if type is builtin
        #
        alias = annotationutils.getReturnType(getter)
        origin, parameters = annotationutils.decomposeAlias(alias)

        if issubclass(origin, collections_abc.MutableSequence):

            return self.isResizable()

        else:

            return issubclass(origin, self.__builtin_types__)

    def trace(self, *path):
        """
        Returns a generator that yields the elements from the given path.
        Any additional path segments will perform a relative trace from this path.

        :rtype: iter
        """

        # Iterate through segments
        #
        current = self.root
        yield current

        segments = tuple(self.flatten(self._path, path))

        for segment in segments:

            # Inspect segment type
            #
            if isinstance(current, collections_abc.Sequence) and isinstance(segment, integer_types):

                current = current[segment]

            elif isinstance(current, collections_abc.Mapping) and isinstance(segment, string_types):

                current = current[segment]

            else:

                raise TypeError('trace() expects a valid path (%s given)!' % str(segments))

            # Yield current object
            #
            yield current

    def eval(self, *path, **kwargs):
        """
        Returns the value at the end of the path.
        Any additional path segments will perform a relative trace from this path.

        :key default: Any
        :key relative: bool
        :rtype: Any
        """

        default = kwargs.get('default', None)

        try:

            return list(self.trace(*path))[-1]

        except (IndexError, KeyError, TypeError) as exception:

            log.debug(exception)
            return default
    # endregion
