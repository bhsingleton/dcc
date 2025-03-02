from abc import ABCMeta, abstractmethod
from . import afnobject
from ..vendor.six import with_metaclass

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnLayer(with_metaclass(ABCMeta, afnobject.AFnObject)):
    """
    Overload of AFnBase that outlines the function set behaviour for layers.
    """

    __slots__ = ()

    @abstractmethod
    def visibility(self):
        """
        Returns the visibility state of this layer.

        :rtype: bool
        """

        pass

    @abstractmethod
    def setVisibility(self, visibility):
        """
        Updates the visibility state of this layer.

        :type visibility: bool
        :rtype: bool
        """

        pass

    def show(self):
        """
        Sets this layer to visible.

        :rtype: None
        """

        self.setVisibility(True)

    def hide(self):
        """
        Sets this layer as hidden.

        :rtype: None
        """

        self.setVisibility(False)

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
