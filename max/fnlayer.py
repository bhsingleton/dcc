import pymxs

from .libs import layerutils
from ..abstract import afnlayer
from ..vendor.six import string_types

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnLayer(afnlayer.AFnLayer):
    """
    Overload of AFnLayer that defines the function set behavior for 3ds Max layers.
    """

    __slots__ = ()

    def object(self):
        """
        Returns the object assigned to this function set.

        :rtype: pymxs.MXSWrapperBase
        """

        # Call parent method
        #
        name = super(FnLayer, self).object()

        # Inspect object type
        #
        if isinstance(name, string_types):

            return pymxs.runtime.LayerManager.getLayerFromName(name)

        else:

            return None

    def setObject(self, obj):
        """
        Assigns an object to this function set for manipulation.

        :type obj: Union[str, pymxs.MXSWrapperBase]
        :rtype: None
        """

        # Evaluate object type
        #
        if isinstance(obj, pymxs.MXSWrapperBase):

            obj = getattr(obj, 'name', '')

        # Check if layer exists
        #
        layer = pymxs.runtime.LayerManager.getLayerFromName(obj)

        if layer is not None:

            super(FnLayer, self).setObject(obj)

        else:

            raise TypeError('setObject() expects a valid layer (%s given)!' % obj)

    def acceptsObject(self, obj):
        """
        Evaluates whether the supplied object is supported by this function set.

        :type obj: Any
        :rtype: bool
        """

        return isinstance(obj, (str, pymxs.MXSWrapperBase))

    def name(self):
        """
        Returns the name of this layer.

        :rtype: str
        """

        return self.object().name

    def setName(self, name):
        """
        Updates the name of this layer.

        :type name: str
        :rtype: None
        """

        self.object().setName(name)

    def namespace(self):
        """
        Returns the namespace for this object.

        :rtype: str
        """

        return ''

    def setNamespace(self, namespace):
        """
        Updates the namespace for this object.

        :type namespace: str
        :rtype: None
        """

        pass

    def parent(self):
        """
        Returns the parent of this node.

        :rtype: pymxs.MXSWrapperBase
        """

        return self.object().getParent()

    def setParent(self, parent):
        """
        Updates the parent of this node.

        :type parent: pymxs.MXSWrapperBase
        :rtype: None
        """

        self.object().setParent(parent)

    def iterChildren(self):
        """
        Returns a generator that yields all the children from this node.

        :rtype: iter
        """

        # Iterate through children
        #
        obj = self.object()
        numChildren = obj.getNumChildren()

        for i in range(1, numChildren + 1, 1):

            yield obj.getChild(i)

    def visibility(self):
        """
        Returns the visibility state of this layer.

        :rtype: bool
        """

        return self.object().visibility

    def setVisibility(self, visibility):
        """
        Updates the visibility state of this layer.

        :type visibility: bool
        :rtype: bool
        """

        self.object().visibility = visibility

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

        layer = self.object()

        for node in nodes:

            layer.addNode(node)

    def removeNodes(self, *nodes):
        """
        Removes the supplied nodes from this layer.

        :type nodes: Sequence[object]
        :rtype: None
        """

        layer = layerutils.defaultLayer()

        for node in nodes:

            layer.addNode(node)
