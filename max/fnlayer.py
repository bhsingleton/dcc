import pymxs

from six import string_types
from dcc.abstract import afnlayer
from dcc.max.libs import layerutils
from dcc.decorators.validator import validator

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnLayer(afnlayer.AFnLayer):
    """
    Overload of AFnNode that implements the node interface for 3ds Max.
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

        # Check object type
        #
        if isinstance(obj, string_types):

            super(FnLayer, self).setObject(obj)

        elif isinstance(obj, pymxs.MXSWrapperBase):

            super(FnLayer, self).setObject(obj.name)

        else:

            raise TypeError('setObject() expects a MXSWrapperBase (%s given)!' % type(obj).__name__)

    def acceptsObject(self, obj):
        """
        Evaluates whether the supplied object is supported by this function set.

        :type obj: Any
        :rtype: bool
        """

        return isinstance(obj, (str, pymxs.MXSWrapperBase))

    @validator
    def name(self):
        """
        Returns the name of this layer.

        :rtype: str
        """

        return self.object().name

    @validator
    def setName(self, name):
        """
        Updates the name of this layer.

        :type name: str
        :rtype: None
        """

        self.object().setName(name)

    @validator
    def visibility(self):
        """
        Returns the visibility state of this layer.

        :rtype: bool
        """

        return self.object().visibility

    @validator
    def setVisibility(self, visibility):
        """
        Updates the visibility state of this layer.

        :type visibility: bool
        :rtype: bool
        """

        self.object().visibility = visibility

    @validator
    def iterNodes(self):
        """
        Returns a generator that yields nodes from this layer.

        :rtype: iter
        """

        return layerutils.iterNodesFromLayers(self.object())

    @validator
    def addNodes(self, *nodes):
        """
        Adds the supplied nodes to this layer.

        :type nodes: Sequence[object]
        :rtype: None
        """

        layer = self.object()

        for node in nodes:

            layer.addNode(node)

    @validator
    def removeNodes(self, *nodes):
        """
        Removes the supplied nodes from this layer.

        :type nodes: Sequence[object]
        :rtype: None
        """

        layer = layerutils.defaultLayer()

        for node in nodes:

            layer.addNode(node)
