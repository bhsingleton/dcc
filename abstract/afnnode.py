import re
import fnmatch

from abc import ABCMeta, abstractmethod
from six import with_metaclass
from dcc.abstract import afnobject

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnNode(with_metaclass(ABCMeta, afnobject.AFnObject)):
    """
    Overload of AFnObject that outlines scene node interfaces.
    Any overloads should take care of internally storing the node handle for faster lookups.
    If the DCC has no means of looking up nodes via handles then the developer must use an alternative method.
    """

    __slots__ = ()

    @abstractmethod
    def handle(self):
        """
        Returns the handle for this node.

        :rtype: int
        """

        pass

    def isValid(self):
        """
        Evaluates if this function set is valid.

        :rtype: bool
        """

        return self.object() is not None

    @abstractmethod
    def name(self):
        """
        Returns the name of this node.

        :rtype: str
        """

        pass

    @abstractmethod
    def setName(self, name):
        """
        Updates the name of this node.

        :type name: str
        :rtype: None
        """

        pass

    def dagPath(self):
        """
        Returns a dag path to this node.
        This uses pipes to delimit a break between two nodes.

        :rtype: str
        """

        return '|'.join([self.__class__(x).name() for x in self.trace()])

    @abstractmethod
    def getAttr(self, name):
        """
        Returns the specified attribute value.

        :type name: str
        :rtype: Any
        """

        pass

    @abstractmethod
    def hasAttr(self, name):
        """
        Evaluates if this node has the specified attribute.

        :type name: str
        :rtype: bool
        """

        pass

    @abstractmethod
    def setAttr(self, name, value):
        """
        Updates the specified attribute value.

        :type name: str
        :type value: Any
        :rtype: None
        """

        pass

    def select(self, replace=True):
        """
        Selects the node associated with this function set.

        :type replace: bool
        :rtype: None
        """

        self.setActiveSelection([self.object()], replace=replace)

    def deselect(self):
        """
        Deselects the node associated with this function set.

        :rtype: None
        """

        activeSelection = self.getActiveSelection()
        obj = self.object()

        if obj in activeSelection:

            activeSelection.remove(obj)
            self.setActiveSelection(activeSelection, replace=True)

    def isSelected(self):
        """
        Evaluates if this node is selected.

        :rtype: bool
        """

        return self.object() in self.getActiveSelection()

    def isPartiallySelected(self):
        """
        Evaluates if this node is partially selected.
        Useful for things like deformers or modifiers.

        :rtype: bool
        """

        return self.isSelected()

    def isIsolated(self):
        """
        Evaluates if this is the only node selected.

        :rtype: bool
        """

        selection = self.getActiveSelection()
        selectionCount = len(selection)

        return selectionCount == 1 and self.isPartiallySelected()

    @abstractmethod
    def isTransform(self):
        """
        Evaluates if this node represents a transform.

        :rtype: bool
        """

        pass

    @abstractmethod
    def isJoint(self):
        """
        Evaluates if this node represents an influence object.

        :rtype: bool
        """

        pass

    @abstractmethod
    def isMesh(self):
        """
        Evaluates if this node represents a mesh.

        :rtype: bool
        """

        pass

    @abstractmethod
    def getAssociatedReference(self):
        """
        Returns the reference this node is associated with.

        :rtype: object
        """

        pass

    @classmethod
    @abstractmethod
    def doesNodeExist(cls, name):
        """
        Evaluates whether a node exists with the given name.

        :type name: str
        :rtype: bool
        """

        pass

    @classmethod
    @abstractmethod
    def getNodeByName(cls, name):
        """
        Returns a node with the given name.
        If no node associated with this name then none is returned.

        :type name: str
        :rtype: Any
        """

        pass

    @classmethod
    @abstractmethod
    def getNodeByHandle(cls, handle):
        """
        Returns a node with the given handle.
        If no node is associated with this handle then none is returned.

        :type handle: int
        :rtype: Any
        """

        pass

    @classmethod
    @abstractmethod
    def getNodesWithAttribute(cls, name):
        """
        Returns a list of nodes with the given attribute name.

        :type name: str
        :rtype: List[object]
        """

        pass

    @classmethod
    @abstractmethod
    def iterSceneNodes(cls):
        """
        Returns a generator that yields all nodes from the scene.

        :rtype: iter
        """

        pass

    @classmethod
    def iterNodesByPattern(cls, pattern):
        """
        Returns a generator that yields nodes that match the given pattern.

        :type pattern: str
        :rtype: iter
        """

        fnNode = cls()

        for node in cls.iterSceneNodes():

            fnNode.setObject(node)

            if fnmatch.fnmatch(fnNode.name(), pattern):

                yield node

            else:

                continue

    @classmethod
    def iterNodesByRegex(cls, pattern):
        """
        Returns a generator that yields nodes that match the given regex expression.

        :type pattern: str
        :rtype: iter
        """

        fnNode = cls()
        regex = re.compile(pattern)

        for node in cls.iterSceneNodes():

            fnNode.setObject(node)

            if regex.match(fnNode.name()):

                yield node

            else:

                continue

    @classmethod
    @abstractmethod
    def getActiveSelection(cls):
        """
        Returns the active selection.

        :rtype: list
        """

        pass

    @classmethod
    @abstractmethod
    def setActiveSelection(cls, selection, replace=True):
        """
        Updates the active selection.

        :type selection: list
        :type replace: bool
        :rtype: None
        """

        pass

    @classmethod
    @abstractmethod
    def clearActiveSelection(cls):
        """
        Clears the active selection.

        :rtype: None
        """

        pass
