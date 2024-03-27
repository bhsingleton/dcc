import weakref

from maya.api import OpenMaya as om
from Qt import QtGui
from six import string_types, integer_types
from six.moves import collections_abc
from dcc.maya.libs import attributeutils, plugutils, plugmutators
from dcc.generators.flatten import flatten

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QPlugPath(collections_abc.Sequence):
    """
    Base class used to interface with plug paths from inside the Qt item model.
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
        super(QPlugPath, self).__init__()

        # Declare private methods
        #
        self._model = lambda: None
        self._path = ()

        # Check if an item model was supplied
        #
        model = kwargs.get('model')

        if model is not None:

            self._model = weakref.ref(model)
            self._path = tuple(flatten(*args))

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

            return QPlugPath(self._path[index], model=self.model)

        else:

            raise IndexError('__getitem__() expects an integer (%s given)!' % type(index).__name__)

    def __add__(self, other):
        """
        Private method called whenever addition is performed on this instance.

        :type other: Any
        :rtype: PSONPath
        """

        return QPlugPath(self._path, other, model=self.model)

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

        :rtype: om.MObject
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

        return not self.root.isNull()

    def toString(self):
        """
        Returns a string representation of this path.

        :rtype: str
        """

        string = ''

        for (i, segment) in enumerate(self._path):

            if isinstance(segment, string_types):

                string += f'.{segment}' if (i > 0) else f'{segment}'

            elif isinstance(segment, integer_types):

                string += f'[{segment}]'

            else:

                continue

        return string

    def name(self):
        """
        Returns the name of this plug.

        :rtype: str
        """

        # Redundancy check
        #
        if self.isRoot():

            return ''

        # Evaluate last element
        #
        lastElement = self._path[-1]

        if isinstance(lastElement, integer_types):

            return f'{self._path[-2]}[{lastElement}]'

        else:

            return lastElement

    def isRoot(self):
        """
        Evaluates if this is a root path.

        :rtype: bool
        """

        return len(self) == 0

    def isTopLevel(self):
        """
        Evaluates if this is a top-level path.

        :rtype: bool
        """

        return len(self) == 1

    def hasParent(self):
        """
        Evaluates if this path has a parent.

        :rtype: bool
        """

        return len(self) > 0

    def parent(self):
        """
        Returns the parent path for this instance.
        If this path has no parent then none is returned!

        :rtype: QPlugPath
        """

        # Evaluate path length
        #
        if self.hasParent():

            return self[:-1]

        else:

            return None

    def childCount(self):
        """
        Returns the number of children from this path.

        :rtype: int
        """

        # Check if path is valid
        #
        if not self.isValid():

            return 0

        # Evaluate child count
        #
        if self.isRoot():

            # Evaluate attribute count
            #
            attributes = list(attributeutils.iterTopLevelAttributes(self.root))
            attributeCount = len(attributes)

            return attributeCount

        else:

            # Evaluate plug type
            #
            plug = self.plug()

            if plug.isArray and not plug.isElement:

                return plug.numElements()

            elif plug.isCompound:

                return plug.numChildren()

            else:

                return 0

    def child(self, index):
        """
        Returns an indexed child path.

        :type index: int
        :rtype: QPlugPath
        """

        # Check if path is valid
        #
        if not self.isValid():

            return None

        # Evaluate child count
        #
        if self.isRoot():

            # Check if index is in range
            #
            attributes = list(attributeutils.iterTopLevelAttributes(self.root))
            attributeCount = len(attributes)

            if 0 <= index < attributeCount:

                name = om.MFnAttribute(attributes[index]).name
                return QPlugPath(self._path, name, model=self.model)

            else:

                raise IndexError('child()')

        else:

            # Evaluate plug type
            #
            plug = self.plug()

            if plug.isArray and not plug.isElement:

                return QPlugPath(self._path, index, model=self.model)

            elif plug.isCompound:

                attribute = om.MFnCompoundAttribute(plug.attribute()).child(index)
                name = om.MFnAttribute(attribute).name

                return QPlugPath(self._path, name, model=self.model)

            else:

                return None

    def position(self):
        """
        Returns the position of this path relative to its parent.

        :rtype: int
        """

        if self.isRoot():

            return 0

        else:

            return plugutils.findPlugIndex(self.plug())

    def icon(self):
        """
        Returns the icon associated with this path type.

        :rtype: QtGui.QIcon
        """

        plug = self.plug()

        if plug.isArray and not plug.isElement:

            return QtGui.QIcon(':data/icons/list.svg')

        elif plug.isCompound:

            return QtGui.QIcon(':data/icons/dict.svg')

        elif plugutils.isString(plug):

            return QtGui.QIcon(':data/icons/str.svg')

        else:

            return QtGui.QIcon(':data/icons/float.svg')

    def type(self):
        """
        Returns the attribute type from this path.

        :rtype: int
        """

        return plugutils.getApiType(self.plug())

    def typeName(self):
        """
        Returns the attribute type name from this path.

        :rtype: str
        """

        return attributeutils.getAttributeTypeName(self.plug().attribute())

    def acceptsType(self, otherType):
        """
        Evaluates if this path would accept the given type.

        :type otherType: int
        :rtype: bool
        """

        return self.plug().attribute().hasFn(otherType)

    def plug(self):
        """
        Returns the plug from this path.

        :rtype: om.MPlug
        """

        return self.eval()

    def value(self):
        """
        Returns the value at the end of this path.

        :rtype: Any
        """

        if not self.isRoot():

            return plugmutators.getValue(self.plug())

        else:

            return None

    def setValue(self, value):
        """
        Updates the value at the end of this path.

        :type value: Any
        :rtype: None
        """

        if not self.isRoot():

            plugmutators.setValue(self.plug(), value)

    def isArray(self):
        """
        Evaluates if the path represents an array plug.

        :rtype: bool
        """

        plug = self.plug()

        if not plug.isNull:

            return plug.isArray and not plug.isElement

        else:

            return False

    def isElement(self):
        """
        Evaluates if this path represents an array plug element.

        :rtype: bool
        """

        plug = self.plug()

        if not plug.isNull:

            return plug.isArray and plug.isElement

        else:

            return False

    def isCompound(self):
        """
        Evaluates if the path represents a compound plug.

        :rtype: bool
        """

        plug = self.plug()

        if not plug.isNull:

            return plug.isCompound

        else:

            return False

    def isEditable(self):
        """
        Evaluates if this path is editable.

        :rtype: bool
        """

        # Redundancy check
        #
        plug = self.plug()

        if plug.isNull:

            return False

        # Check if plug is read-only
        #
        isReadOnly = plug.isFreeToChange() == om.MPlug.kNotFreeToChange
        isArray = plug.isArray and not plug.isElement
        isCompound = plug.isCompound

        if isReadOnly or isArray or isCompound:

            return False

        # Evaluate plug's data type
        #
        if plugutils.isNumeric(plug) or plugutils.isString(plug):

            return True

        else:

            return False

    def trace(self, *path):
        """
        Returns a generator that yields the elements from the given path.
        Any additional path segments will perform a relative trace from this path.

        :rtype: Iterator[om.MPlug]
        """

        # Check if node exists
        #
        node = self.root

        if node.isNull():

            return iter([])

        # Iterate through segments
        #
        fnDependNode = om.MFnDependencyNode(node)
        segments = tuple(flatten(self._path, path))

        plug = None

        for (i, segment) in enumerate(segments):

            # Evaluate segment type
            #
            if i == 0:

                # Check if attribute exists
                #
                if fnDependNode.hasAttribute(segment):

                    plug = om.MPlug(node, fnDependNode.attribute(segment))

                else:

                    raise KeyError('trace() attribute does not exist!')

            elif isinstance(segment, string_types):

                # Check if attribute exists
                #
                if fnDependNode.hasAttribute(segment):

                    plug = plug.child(fnDependNode.attribute(segment))

                else:

                    raise KeyError('trace() child attribute does not exist!')

            elif isinstance(segment, integer_types):

                # Check if index is in range
                #
                numElements = plug.numElements()

                if 0 <= segment < numElements:

                    plug = plug.elementByPhysicalIndex(segment)

                else:

                    raise IndexError('trace() index out-of-range!')

            else:

                raise TypeError(f'trace() expects either a str or int ({type(segment).__name__} given)!')

            yield plug

    def eval(self, *path, **kwargs):
        """
        Returns the plug at the end of this path.
        Any additional path segments will perform a relative trace from this path.

        :key default: Any
        :rtype: om.MPlug
        """

        default = kwargs.get('default', om.MPlug())

        try:

            return list(self.trace(*path))[-1]

        except (IndexError, KeyError, TypeError) as exception:

            log.debug(exception)
            return default
    # endregion
