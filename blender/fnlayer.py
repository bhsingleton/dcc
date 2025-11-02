from ..abstract import afnlayer

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnLayer(afnlayer.AFnLayer):
    """
    Overload of `AFnLayer` that implements the layer interface for Blender.
    """

    __slots__ = ()

    def visibility(self):
        """
        Returns the visibility state of this layer.

        :rtype: bool
        """

        return False

    def setVisibility(self, visibility):
        """
        Updates the visibility state of this layer.

        :type visibility: bool
        :rtype: bool
        """

        pass

    def iterNodes(self):
        """
        Returns a generator that yields nodes from this layer.

        :rtype: iter
        """

        return iter([])

    def addNodes(self, *nodes):
        """
        Adds the supplied nodes to this layer.

        :type nodes: Sequence[object]
        :rtype: None
        """

        pass

    def removeNodes(self, *nodes):
        """
        Removes the supplied nodes from this layer.

        :type nodes: Sequence[object]
        :rtype: None
        """

        pass
