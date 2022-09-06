import weakref

from Qt import QtGui
from collections import deque
from six import string_types, integer_types
from six.moves import collections_abc
from dcc.python import stringutils, annotationutils, funcutils

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
    __editables__ = (bool, int, float, str)

    def __init__(self, *args, **kwargs):
        """
        Private method that is called after a new instance is created.

        :key model: dcc.ui.models.qpsonitemmodel.QPSONItemModel
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

        :rtype: dcc.ui.models.qpsonitemmodel.QPSONItemModel
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

        pathLength = len(self._path)

        if pathLength == 0:

            return True

        elif pathLength == 1:

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

        alias = self.type()
        origin, parameters = annotationutils.decomposeAlias(alias)

        if hasattr(origin, '__name__'):

            return QtGui.QIcon(':data/icons/{type}.svg'.format(type=origin.__name__))

        else:

            return QtGui.QIcon()

    def type(self):
        """
        Returns the value type from this path.

        :rtype: type
        """

        getter, setter = self.accessors()

        if callable(getter):

            return annotationutils.getReturnType(getter)

        else:

            return type(None)

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

        getter, setter = self.accessors()

        if callable(setter):

            return setter(value)

        else:

            return None

    def isArray(self):
        """
        Evaluates if the path represents an array.

        :rtype: bool
        """

        alias = self.type()
        origin, parameters = annotationutils.decomposeAlias(alias)

        return issubclass(origin, collections_abc.Sequence) and not issubclass(origin, string_types)

    def isMapping(self):
        """
        Evaluates if the path represents a mapping object.

        :rtype: bool
        """

        alias = self.type()
        origin, parameters = annotationutils.decomposeAlias(alias)

        return issubclass(origin, collections_abc.Mapping)

    def isElement(self):
        """
        Evaluates if this path represents an array element.

        :rtype: bool
        """

        return isinstance(self._path[-1], integer_types)

    def isResizable(self):
        """
        Evaluates if this path is resizable.

        :rtype: bool
        """

        alias = self.type()
        origin, parameters = annotationutils.decomposeAlias(alias)

        if issubclass(origin, collections_abc.MutableSequence) and len(parameters) == 1:

            return issubclass(parameters[0], self.__editables__)

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

        if issubclass(origin, collections_abc.MutableSequence) and len(parameters) == 1:

            return issubclass(parameters[0], self.__editables__)

        else:

            return issubclass(origin, self.__editables__)

    @classmethod
    def flatten(cls, *items):
        """
        Returns a generator that yields flattened path segments.

        :rtype: iter
        """

        queue = deque(items)

        while len(queue) > 0:

            item = queue.popleft()

            if isinstance(item, collections_abc.Sequence) and not isinstance(item, string_types):

                queue.extendleft(reversed(item))

            elif isinstance(item, integer_types):

                yield item

            elif isinstance(item, string_types) and not stringutils.isNullOrEmpty(item):

                yield item

            else:

                continue

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

        segments = tuple(self.flatten(*self._path, *path))

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

            log.warning(exception)
            return default
    # endregion
