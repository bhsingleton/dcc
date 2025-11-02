from maya import cmds as mc
from maya.api import OpenMaya as om
from . import fnnode
from .libs import layerutils, plugutils
from ..abstract import afnlayer

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnLayer(fnnode.FnNode, afnlayer.AFnLayer):
    """
    Overload of `AFnLayer` that implements the layer interface for Maya.
    """

    __slots__ = ()

    def visibility(self):
        """
        Returns the visibility state of this layer.

        :rtype: bool
        """

        return self.getAttr('visibility')

    def setVisibility(self, visibility):
        """
        Updates the visibility state of this layer.

        :type visibility: bool
        :rtype: bool
        """

        self.setAttr('visibility', visibility)

    def iterNodes(self):
        """
        Returns a generator that yields nodes from this layer.

        :rtype: iter
        """

        return layerutils.iterNodesFromLayers(self.object())

    def addNodes(self, *nodes):
        """
        Adds the supplied nodes to this layer.

        :type nodes: Sequence[object]
        :rtype: None
        """

        layerutils.addNodesToLayer(self.object(), nodes)

    def removeNodes(self, *nodes):
        """
        Removes the supplied nodes from this layer.

        :type nodes: Sequence[object]
        :rtype: None
        """

        layerutils.removeNodesFromLayer(self.object(), nodes)
