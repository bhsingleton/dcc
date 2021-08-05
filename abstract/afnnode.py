from abc import ABCMeta, abstractmethod
from six import with_metaclass

from . import afnbase

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnNode(with_metaclass(ABCMeta, afnbase.AFnBase)):
    """
    Overload of AFnBase that outlines function set behaviour for interfacing with DCC scene nodes.
    Any overloads should take care of internally storing the node handle.
    If the DCC has no means of looking up nodes via node handle then the developer must store it themself.
    """

    __slots__ = ()

    @abstractmethod
    def handle(self):
        """
        Returns the handle for this node.

        :rtype: Union[str, int]
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

    @abstractmethod
    def parent(self):
        """
        Returns the parent of this node.

        :rtype: Any
        """

        pass

    @abstractmethod
    def iterParents(self):
        """
        Returns a generator that yields all of the parents for this node.

        :rtype: iter
        """

        pass

    def parents(self):
        """
        Returns a list of parents starting from closest to furthest away.

        :rtype: list[Any]
        """

        return list(self.iterParents())

    def topLevelParent(self):
        """
        Returns the top level parent of this node.
        If this node has no parents then itself is returned.

        :rtype: Any
        """

        parents = self.parents()
        numParents = len(parents)

        if numParents > 0:

            return parents[-1]

        else:

            return None

    def hasParent(self):
        """
        Evaluates whether this node has a parent.

        :rtype: bool
        """

        return self.parent() is not None

    @abstractmethod
    def setParent(self, parent):
        """
        Updates the parent of this node.

        :type parent: Any
        :rtype: None
        """

        pass

    @abstractmethod
    def iterChildren(self):
        """
        Returns a generator that yields all of the children for this node.

        :rtype: iter
        """

        pass

    def children(self):
        """
        Returns a list of children belonging to this node.

        :rtype: list[Any]
        """

        return list(self.iterChildren())

    @abstractmethod
    def iterDescendants(self):
        """
        Returns a generator that yields all of the descendants for this node.

        :rtype: iter
        """

        pass

    def descendants(self):
        """
        Returns a list of all the descendants for this node.

        :rtype: list[Any]
        """

        return list(self.iterDescendants())

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
    def getActiveSelection(cls):
        """
        Returns the active selection.

        :rtype: list
        """

        pass
