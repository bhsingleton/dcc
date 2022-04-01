import maya.cmds as mc
import maya.api.OpenMaya as om

from dcc.maya import fnnode
from dcc.abstract import afnlayer
from dcc.maya.libs import layerutils, plugutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnLayer(fnnode.FnNode, afnlayer.AFnLayer):
    """
    Overload of AFnLayer that defines the function set behavior for Maya layers.
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
