from ..abstract import afnselectionset

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnSelectionSet(afnselectionset.AFnSelectionSet):
    """
    Overload of `AFnBase` that implements the selection-set interface for Blender.
    """

    __slots__ = ()

    def name(self):
        """
        Returns the name of this object.

        :rtype: str
        """

        return ''

    def setName(self, name):
        """
        Updates the name of this object.

        :type name: str
        :rtype: None
        """

        pass

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
        Returns the parent of this object.

        :rtype: object
        """

        return None

    def setParent(self, parent):
        """
        Updates the parent of this object.

        :type parent: object
        :rtype: None
        """

        pass

    def iterChildren(self):
        """
        Returns a generator that yields all the children from this object.

        :rtype: iter
        """

        return iter([])

    def iterNodes(self):
        """
        Returns a generator that yields nodes from this layer.

        :rtype: iter
        """

        return iter([])

    def containsNode(self, obj):
        """
        Evaluates if this selection set contains the specified node.

        :type obj: Any
        :rtype: bool
        """

        return False

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
