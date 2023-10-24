import pymxs

from six import string_types, integer_types
from dcc.abstract import afnnode, ArrayIndexType
from dcc.max.libs import nodeutils, propertyutils, attributeutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnNode(afnnode.AFnNode):
    """
    Overload of AFnNode that implements the function set behavior for 3ds Max scene nodes.
    """

    __slots__ = ()
    __array_index_type__ = ArrayIndexType.OneBased

    def object(self):
        """
        Returns the object assigned to this function set.

        :rtype: pymxs.MXSWrapperBase
        """

        # Call parent method
        #
        handle = super(FnNode, self).object()

        # Inspect handle type
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

        # Get node handle
        #
        obj = self.getMXSWrapper(obj)
        handle = int(pymxs.runtime.getHandleByAnim(obj))  # In older versions of Max this would return a float!

        # Call parent method
        #
        super(FnNode, self).setObject(handle)

    def acceptsObject(self, obj):
        """
        Evaluates whether the supplied object is supported by this function set.

        :type obj: Any
        :rtype: bool
        """

        return isinstance(obj, (str, pymxs.MXSWrapperBase))

    def baseObject(self):
        """
        Returns the base object assigned to this function set.
        If there is no base then itself is returned!

        :rtype: pymxs.MXSWrapperBase
        """

        obj = self.object()

        if pymxs.runtime.isProperty(obj, 'baseObject'):

            return obj.baseObject

        else:

            return obj

    def name(self):
        """
        Returns the name of this node.

        :rtype: str
        """

        obj = self.object()

        if pymxs.runtime.isProperty(obj, 'name'):

            return obj.name

        else:

            return ''

    def setName(self, name):
        """
        Updates the name of this node.

        :type name: str
        :rtype: None
        """

        obj = self.object()

        if pymxs.runtime.isProperty(obj, 'name'):

            obj.name = name

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

        # Check if object has property
        #
        obj = self.object()

        if pymxs.runtime.isProperty(obj, 'parent'):

            return obj.parent

        else:

            return None

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

    def iterChildren(self):
        """
        Returns a generator that yields all the children from this node.

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

    def handle(self):
        """
        Returns the handle for this node.

        :rtype: int
        """

        return int(pymxs.runtime.getHandleByAnim(self.object()))

    def isTransform(self):
        """
        Evaluates if this node represents a transform.

        :rtype: bool
        """

        return pymxs.runtime.isProperty(self.object(), 'transform')

    def isJoint(self):
        """
        Evaluates if this node represents an influence object.
        In 3ds Max all transform nodes can be used as joints!

        :rtype: bool
        """

        return self.isTransform()

    def isMesh(self):
        """
        Evaluates if this node represents a mesh.

        :rtype: bool
        """

        return pymxs.runtime.classOf(self.object()) in (pymxs.runtime.PolyMeshObject, pymxs.runtime.Editable_Poly, pymxs.runtime.Editable_Mesh)

    def getAttr(self, name):
        """
        Returns the specified attribute value.

        :type name: str
        :rtype: Any
        """

        obj = self.object()
        attributeHolder = obj.modifiers[pymxs.runtime.Name('attributeHolder')]

        if pymxs.runtime.isProperty(obj, name):

            return pymxs.runtime.getProperty(obj, name)

        elif pymxs.runtime.isProperty(attributeHolder, name):

            return pymxs.runtime.getProperty(attributeHolder, name)

        else:

            raise AttributeError('getAttr() "%s" object has no attribute "%s"' % (obj, name))

    def hasAttr(self, name):
        """
        Evaluates if this node has the specified attribute.

        :type name: str
        :rtype: bool
        """

        obj = self.object()
        attributeHolder = obj.modifiers[pymxs.runtime.Name('attributeHolder')]

        return pymxs.runtime.isProperty(obj, name) or pymxs.runtime.isProperty(attributeHolder, name)

    def setAttr(self, name, value):
        """
        Updates the specified attribute value.

        :type name: str
        :type value: Any
        :rtype: None
        """

        obj = self.object()
        attributeHolder = obj.modifiers[pymxs.runtime.Name('attributeHolder')]

        if pymxs.runtime.isProperty(obj, name):

            pymxs.runtime.setProperty(obj, name, value)

        elif pymxs.runtime.isProperty(attributeHolder, name):

            pymxs.runtime.setProperty(attributeHolder, name, value)

        else:

            raise AttributeError('setAttr() "%s" object has no attribute "%s"' % (obj, name))

    def iterAttr(self):
        """
        Returns a generator that yields attribute names.

        :rtype: iter
        """

        for (key, value) in propertyutils.iterStaticProperties(self.object()):

            yield key

    def userProperties(self):
        """
        Returns the user properties.

        :rtype: dict
        """

        buffer = pymxs.runtime.getUserPropBuffer(self.object())  # type: str
        keys = [line.split('=')[0].lstrip().rstrip() for line in buffer.splitlines() if '=' in line]

        return {key: pymxs.runtime.getUserPropValue(self.object(), key, asString=False) for key in keys}

    def getAssociatedReference(self):
        """
        Returns the reference this node is associated with.

        :rtype: om.MObject
        """

        return pymxs.runtime.objXRefMgr.IsNodeXRefed(self.object())

    def getModifiersByType(self, T):
        """
        Returns a list of modifiers from the specified type.

        :type T: class
        :rtype: list
        """

        obj = self.object()

        if pymxs.runtime.isProperty(obj, 'modifiers'):

            return [x for x in obj.modifiers if pymxs.runtime.classOf(x) == T]

        else:

            return []

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

        return pymxs.runtime.getNodeByName(name, exact=False, ignoreCase=True, all=False)

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
    def getNodesByAttribute(cls, name):
        """
        Returns a list of nodes with the given attribute name.

        :type name: str
        :rtype: List[object]
        """

        return attributeutils.getNodesWithParameter(name)

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

            raise TypeError('getMXSWrapper() expects a str or int (%s given)!' % type(value).__name__)

    @classmethod
    def iterInstances(cls):
        """
        Returns a generator that yields node instances.

        :rtype: iter
        """

        return iter(pymxs.runtime.objects)
