from abc import ABCMeta, abstractmethod
from six import with_metaclass
from collections import deque
from dcc.abstract import afnbase

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnObject(with_metaclass(ABCMeta, afnbase.AFnBase)):
    """
    Overload of AFnBase that outlines parent/child interfaces.
    """

    __slots__ = ()

    @abstractmethod
    def name(self):
        """
        Returns the name of this object.

        :rtype: str
        """

        pass

    @abstractmethod
    def setName(self, name):
        """
        Updates the name of this object.

        :type name: str
        :rtype: None
        """

        pass

    @abstractmethod
    def namespace(self):
        """
        Returns the namespace for this object.

        :rtype: str
        """

        pass

    @abstractmethod
    def setNamespace(self, namespace):
        """
        Updates the namespace for this object.

        :type namespace: str
        :rtype: None
        """

        pass

    def absoluteName(self):
        """
        Returns the absolute name of this object.

        :rtype: str
        """

        namespace = self.namespace()
        name = self.name()

        if len(namespace) > 0:

            return '{namespace}:{name}'.format(namespace=namespace, name=name)

        else:

            return name

    def dagPath(self):
        """
        Returns a dag path to this object.
        This uses pipes to delimit a break between two object.

        :rtype: str
        """

        return '|'.join([self.__class__(x).absoluteName() for x in self.trace()])

    @abstractmethod
    def parent(self):
        """
        Returns the parent of this object.

        :rtype: object
        """

        pass

    def iterParents(self):
        """
        Returns a generator that yields all the parents of this object.

        :rtype: iter
        """

        # Initialize function set
        #
        fnObj = self.__class__()
        fnObj.setObject(self.object())

        # Iterate through parents
        #
        parent = fnObj.parent()

        while parent is not None:

            yield parent

            fnObj.setObject(parent)
            parent = fnObj.parent()

    def parents(self):
        """
        Returns a list of parents starting from closest to furthest away.

        :rtype: list[object]
        """

        return list(self.iterParents())

    def topLevelParent(self):
        """
        Returns the top level parent of this object.

        :rtype: object
        """

        parents = self.parents()
        numParents = len(parents)

        if numParents > 0:

            return parents[-1]

        else:

            return None

    def hasParent(self):
        """
        Evaluates whether this object has a parent.

        :rtype: bool
        """

        return self.parent() is not None

    @abstractmethod
    def setParent(self, parent):
        """
        Updates the parent of this object.

        :type parent: object
        :rtype: None
        """

        pass

    def trace(self):
        """
        Returns a generator that yields all the objects from the top-level parent to this object.

        :rtype: iter
        """

        for parent in reversed(list(self.iterParents())):

            yield parent

        yield self.object()

    @abstractmethod
    def iterChildren(self):
        """
        Returns a generator that yields all the children from this object.

        :rtype: iter
        """

        pass

    def children(self):
        """
        Returns a list of children from this object.

        :rtype: List[object]
        """

        return list(self.iterChildren())

    def iterDescendants(self):
        """
        Returns a generator that yields all the descendants from this object.

        :rtype: iter
        """

        queue = deque(self.children())
        fnNode = self.__class__()

        while len(queue) > 0:

            node = queue.popleft()
            yield node

            fnNode.setObject(node)
            queue.extend(fnNode.children())

    def descendants(self):
        """
        Returns a list of all the descendants from this object.

        :rtype: List[object]
        """

        return list(self.iterDescendants())
