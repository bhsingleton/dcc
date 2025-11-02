from ..abstract import afnnode

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnNode(afnnode.AFnNode):
    """
    Overload of `AFnNode` that implements the node interface for Blender.
    """

    __slots__ = ()

    def name(self):
        """
        Returns the name of this node.

        :rtype: str
        """

        return ''

    def setName(self, name):
        """
        Updates the name of this node.

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
        Returns the parent of this node.

        :rtype: pymxs.MXSWrapperBase
        """

        return None

    def setParent(self, parent):
        """
        Updates the parent of this node.

        :type parent: pymxs.MXSWrapperBase
        :rtype: None
        """

        pass

    def iterChildren(self):
        """
        Returns a generator that yields all the children from this node.

        :rtype: iter
        """

        return iter([])

    def handle(self):
        """
        Returns the handle for this node.

        :rtype: int
        """

        return 0

    def isTransform(self):
        """
        Evaluates if this node represents a transform.

        :rtype: bool
        """

        return False

    def isJoint(self):
        """
        Evaluates if this node represents an influence object.
        In 3ds Max all transform nodes can be used as joints!

        :rtype: bool
        """

        return False

    def isMesh(self):
        """
        Evaluates if this node represents a mesh.

        :rtype: bool
        """

        return False

    def getAttr(self, name):
        """
        Returns the specified attribute value.

        :type name: str
        :rtype: Any
        """

        return

    def hasAttr(self, name):
        """
        Evaluates if this node has the specified attribute.

        :type name: str
        :rtype: bool
        """

        return False

    def setAttr(self, name, value):
        """
        Updates the specified attribute value.

        :type name: str
        :type value: Any
        :rtype: None
        """

        pass

    def iterAttr(self, userDefined=False):
        """
        Returns a generator that yields attribute names.

        :type userDefined: bool
        :rtype: Iterator[str]
        """

        return iter([])

    def userProperties(self):
        """
        Returns the user properties.

        :rtype: dict
        """

        return {}

    def getAssociatedReference(self):
        """
        Returns the reference this node is associated with.

        :rtype: om.MObject
        """

        return

    @classmethod
    def doesNodeExist(cls, name):
        """
        Evaluates whether a node exists with the given name.

        :type name: str
        :rtype: bool
        """

        return False

    @classmethod
    def getNodeByName(cls, name):
        """
        Returns a node with the given name.
        If no node associated with this name then none is returned.

        :type name: str
        :rtype: pymxs.MXSWrapperBase
        """

        return

    @classmethod
    def getNodeByHandle(cls, handle):
        """
        Returns a node with the given handle.
        If no node is associated with this handle then none is returned.

        :type handle: int
        :rtype: pymxs.MXSWrapperBase
        """

        return

    @classmethod
    def getNodesByAttribute(cls, name):
        """
        Returns a list of nodes with the given attribute name.

        :type name: str
        :rtype: List[object]
        """

        return []

    @classmethod
    def iterInstances(cls):
        """
        Returns a generator that yields node instances.

        :rtype: iter
        """

        return iter([])
