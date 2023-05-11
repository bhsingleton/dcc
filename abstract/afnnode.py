import re

from abc import ABCMeta, abstractmethod
from six import with_metaclass
from fnmatch import fnmatch
from dcc.abstract import afnobject
from dcc.decorators.classproperty import classproperty

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
    __scene__ = None

    @classproperty
    def scene(cls):
        """
        Getter method that returns the scene function set.

        :rtype: fnscene.FnScene
        """

        if cls.__scene__ is None:

            from dcc import fnscene
            cls.__scene__ = fnscene.FnScene()

        return cls.__scene__

    def isValid(self):
        """
        Evaluates if this function set is valid.

        :rtype: bool
        """

        return self.object() is not None

    @abstractmethod
    def handle(self):
        """
        Returns the handle for this node.

        :rtype: int
        """

        pass

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

    @abstractmethod
    def iterAttr(self):
        """
        Returns a generator that yields attribute names.

        :rtype: iter
        """

        pass

    def listAttr(self):
        """
        Returns a list of attribute names.

        :rtype: List[str]
        """

        return list(self.iterAttr())

    def select(self, replace=True):
        """
        Selects the node associated with this function set.

        :type replace: bool
        :rtype: None
        """

        self.scene.setActiveSelection([self.object()], replace=replace)

    def ensureSelected(self):
        """
        Ensures this node is selected.

        :rtype: None
        """

        if not self.isSelected():

            self.select(replace=True)

    def deselect(self):
        """
        Deselects the node associated with this function set.

        :rtype: None
        """

        activeSelection = self.scene.getActiveSelection()
        obj = self.object()

        if obj in activeSelection:

            activeSelection.remove(obj)
            self.scene.setActiveSelection(activeSelection, replace=True)

    def isSelected(self):
        """
        Evaluates if this node is selected.

        :rtype: bool
        """

        return self.object() in self.scene.getActiveSelection()

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

        selection = self.scene.getActiveSelection()
        selectionCount = len(selection)

        return selectionCount == 1 and self.isPartiallySelected()

    @abstractmethod
    def userPropertyBuffer(self):
        """
        Returns the user property buffer.

        :rtype: str
        """

        pass

    @abstractmethod
    def userProperties(self):
        """
        Returns the user properties.

        :rtype: dict
        """

        pass

    @abstractmethod
    def getAssociatedReference(self):
        """
        Returns the reference this node is associated with.

        :rtype: object
        """

        pass

    def isReferencedNode(self):
        """
        Evaluates if this is a referenced node.

        :rtype: bool
        """

        return self.getAssociatedReference() is not None

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
    def getNodesByAttribute(cls, name):
        """
        Returns a list of nodes with the given attribute name.

        :type name: str
        :rtype: List[object]
        """

        pass

    @classmethod
    @abstractmethod
    def iterInstances(cls):
        """
        Returns a generator that yields texture instances.

        :rtype: iter
        """

        pass

    @classmethod
    def instances(cls):
        """
        Returns a list of texture instances.

        :rtype: List[object]
        """

        return list(cls.iterInstances())

    @classmethod
    def iterInstancesByPattern(cls, pattern):
        """
        Returns a generator that yields nodes that match the given pattern.

        :type pattern: str
        :rtype: iter
        """

        node = cls()
        node.setQueue(cls.iterInstances())

        while not node.isDone():

            if fnmatch(node.name(), pattern):

                yield node.object()

            else:

                node.next()
                continue

    @classmethod
    def iterInstancesByRegex(cls, pattern):
        """
        Returns a generator that yields nodes that match the given regex expression.

        :type pattern: str
        :rtype: iter
        """

        node = cls()
        node.setQueue(cls.iterInstances())

        regex = re.compile(pattern)

        while not node.isDone():

            if regex.match(node.name()):

                yield node.object()

            else:

                node.next()
                continue
