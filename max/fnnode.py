import pymxs

from six import string_types, integer_types
from dcc.abstract import afnnode, ArrayIndexType
from dcc.decorators.validator import validator

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnNode(afnnode.AFnNode):
    """
    Overload of AFnNode that implements the node interface for 3ds Max.
    """

    __slots__ = ()
    __arrayindextype__ = ArrayIndexType.OneBased

    def object(self):
        """
        Returns the object assigned to this function set.

        :rtype: pymxs.MXSWrapperBase
        """

        # Call parent method
        #
        handle = super(FnNode, self).object()

        # Inspect object type
        #
        if isinstance(handle, integer_types):

            return self.getNodeByHandle(handle)

        else:

            return None

    def setObject(self, obj):
        """
        Assigns an object to this function set for manipulation.

        :type obj: Union[str, int, pymxs.MXSWrapperBase]
        :rtype: None
        """

        # Get maxscript wrapper
        #
        obj = self.getMXSWrapper(obj)
        handle = pymxs.runtime.getHandleByAnim(obj)

        # Assign anim handle
        #
        super(FnNode, self).setObject(handle)

    def acceptsObject(self, obj):
        """
        Evaluates whether the supplied object is supported by this function set.

        :type obj: Any
        :rtype: bool
        """

        return isinstance(obj, (str, pymxs.MXSWrapperBase))

    @validator
    def handle(self):
        """
        Returns the handle for this node.

        :rtype: int
        """

        return int(pymxs.runtime.getHandleByAnim(self.object()))

    @validator
    def name(self):
        """
        Returns the name of this node.

        :rtype: str
        """

        return self.object().name

    @validator
    def setName(self, name):
        """
        Updates the name of this node.

        :type name: str
        :rtype: None
        """

        self.object().name = name

    @validator
    def isTransform(self):
        """
        Evaluates if this node represents a transform.

        :rtype: bool
        """

        return pymxs.runtime.isProperty(self.object(), 'transform')

    @validator
    def isJoint(self):
        """
        Evaluates if this node represents an influence object.
        In 3ds Max all transform nodes can be used as joints!

        :rtype: bool
        """

        return self.isTransform()

    @validator
    def isMesh(self):
        """
        Evaluates if this node represents a mesh.

        :rtype: bool
        """

        return pymxs.runtime.classOf(self.object()) in (pymxs.runtime.PolyMeshObject, pymxs.runtime.Editable_Poly, pymxs.runtime.Editable_Mesh)

    @validator
    def parent(self):
        """
        Returns the parent of this node.

        :rtype: pymxs.MXSWrapperBase
        """

        # Check if object has property
        #
        obj = self.object()

        if pymxs.runtime.isProperty(obj, 'parent'):

            return obj.parent

        else:

            return None

    @validator
    def setParent(self, parent):
        """
        Updates the parent of this node.

        :type parent: pymxs.MXSWrapperBase
        :rtype: None
        """

        # Check if object has property
        #
        obj = self.object()

        if pymxs.runtime.isProperty(obj, 'parent'):

            obj.parent = parent

    @validator
    def iterChildren(self):
        """
        Returns a generator that yields all of the children for this node.

        :rtype: iter
        """

        # Check if object has property
        #
        obj = self.object()

        if not pymxs.runtime.isProperty(obj, 'children'):

            return

        # Iterate through children
        #
        children = obj.children

        for i in range(children.count):

            yield children[i]

    @validator
    def getModifiersByType(self, T):
        """
        Returns a list of modifiers from the specified type.

        :type T: class
        :rtype: list
        """

        return [x for x in self.object().modifiers if pymxs.runtime.classOf(x) == T]

    @classmethod
    def getMXSWrapper(cls, value):
        """
        Returns an MXSWrapper from any given value.

        :type value: Union[str, int, pymxs.MXSWrapperBase]
        :rtype: pymxs.MXSWrapperBase
        """

        # Check object type
        #
        if isinstance(value, pymxs.MXSWrapperBase):

            return value

        elif isinstance(value, integer_types):

            return cls.getNodeByHandle(value)

        elif isinstance(value, string_types):

            return cls.getNodeByName(value)

        else:

            raise TypeError('setObject() expects a str or int (%s given)!' % type(value).__name__)

    @classmethod
    def doesNodeExist(cls, name):
        """
        Evaluates whether a node exists with the given name.

        :type name: str
        :rtype: bool
        """

        return cls.getNodeByName(name) is not None

    @classmethod
    def getNodeByName(cls, name):
        """
        Returns a node with the given name.
        If no node associated with this name then none is returned.

        :type name: str
        :rtype: pymxs.MXSWrapperBase
        """

        return pymxs.runtime.getNodeByName(name, exact=True, ignoreCase=True, all=False)

    @classmethod
    def getNodeByHandle(cls, handle):
        """
        Returns a node with the given handle.
        If no node is associated with this handle then none is returned.

        :type handle: int
        :rtype: pymxs.MXSWrapperBase
        """

        return pymxs.runtime.getAnimByHandle(handle)

    @classmethod
    def iterSceneNodes(cls):
        """
        Returns a generator that yields all nodes from the scene.

        :rtype: iter
        """

        objectCount = pymxs.runtime.objects.count

        for i in range(objectCount):

            yield pymxs.runtime.objects[i]

    @classmethod
    def getActiveSelection(cls):
        """
        Returns the active selection.

        :rtype: list[pymxs.MXSWrapperBase]
        """

        selection = pymxs.runtime.selection
        return [selection[x] for x in range(selection.count)]

    @classmethod
    def setActiveSelection(cls, selection, replace=True):
        """
        Updates the active selection.

        :type selection: list
        :type replace: bool
        :rtype: None
        """

        # Check if selection should be replaced
        #
        if replace:

            pymxs.runtime.select(selection)

        else:

            pymxs.runtime.selectMore(selection)

    @classmethod
    def clearActiveSelection(cls):
        """
        Clears the active selection.

        :rtype: None
        """

        pymxs.runtime.clearSelection()
