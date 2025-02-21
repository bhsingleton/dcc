from abc import ABCMeta, abstractmethod
from . import afnobject
from ..vendor.six import with_metaclass

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnSelectionSet(with_metaclass(ABCMeta, afnobject.AFnObject)):
    """
    Overload of AFnBase that outlines the function set behaviour for selection sets.
    """

    __slots__ = ()

    @abstractmethod
    def iterNodes(self):
        """
        Returns a generator that yields nodes from this layer.

        :rtype: iter
        """

        pass

    def nodes(self):
        """
        Returns a list of nodes from this layer.

        :rtype: List[object]
        """

        return list(self.iterNodes())

    @abstractmethod
    def containsNode(self, node):
        """
        Evaluates if this selection set contains the specified node.

        :type node: Any
        :rtype: bool
        """

        pass

    @abstractmethod
    def addNodes(self, *nodes):
        """
        Adds the supplied nodes to this layer.

        :type nodes: Sequence[object]
        :rtype: None
        """

        pass

    @abstractmethod
    def removeNodes(self, *nodes):
        """
        Removes the supplied nodes from this layer.

        :type nodes: Sequence[object]
        :rtype: None
        """
        pass
