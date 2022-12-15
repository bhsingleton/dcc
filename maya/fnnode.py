import maya.cmds as mc
import maya.api.OpenMaya as om

from six import integer_types
from dcc.abstract import afnnode
from dcc.maya.libs import dagutils, attributeutils, plugutils, plugmutators

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnNode(afnnode.AFnNode):
    """
    Overload of AFnNode that implements the function set behavior for Maya scene nodes.
    """

    __slots__ = ()
    __handles__ = {}

    def object(self):
        """
        Returns the object assigned to this function set.

        :rtype: om.MObject
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

        :type obj: Union[str, om.MObject, om.MDagPath]
        :rtype: None
        """

        # Get object
        #
        dependNode = dagutils.getMObject(obj)

        if not dependNode.isNull():

            # Get object handle
            #
            handle = om.MObjectHandle(dependNode)
            self.__handles__[handle.hashCode()] = handle

            # Assign node handle
            #
            super(FnNode, self).setObject(handle.hashCode())

        else:

            raise TypeError('setObject() expects a valid object (%s given)!' % obj)

    def acceptsObject(self, obj):
        """
        Evaluates whether the supplied object is supported by this function set.

        :type obj: Any
        :rtype: bool
        """

        return isinstance(obj, (str, om.MObject, om.MDagPath, om.MObjectHandle))

    def name(self):
        """
        Returns the name of this node.

        :rtype: str
        """

        absoluteName = om.MFnDependencyNode(self.object()).name()
        return dagutils.stripNamespace(absoluteName)

    def setName(self, name):
        """
        Updates the name of this node.

        :type name: str
        :rtype: None
        """

        om.MFnDependencyNode(self.object()).setName(name)

    def namespace(self):
        """
        Returns the namespace for this node.

        :rtype: str
        """

        return om.MFnDependencyNode(self.object()).namespace

    def setNamespace(self, namespace):
        """
        Updates the namespace for this node.

        :type namespace: str
        :rtype: None
        """

        om.MFnDependencyNode(self.object()).namespace = namespace

    def parent(self):
        """
        Returns the parent of this node.

        :rtype: om.MObject
        """

        # Check if this is a dag node
        #
        obj = self.object()

        if not obj.hasFn(om.MFn.kDagNode):

            return None

        # Check if this node has a parent
        #
        fnDagNode = om.MFnDagNode(obj)
        parent = fnDagNode.parent(0)

        if not parent.hasFn(om.MFn.kWorld):

            return parent

        else:

            return None

    def setParent(self, parent):
        """
        Updates the parent of this node.

        :type parent: om.MObject
        :rtype: None
        """

        obj = self.object()

        if obj.hasFn(om.MFn.kDagNode):

            dagModifer = om.MDagModifier()
            dagModifer.reparentNode(obj, parent)
            dagModifer.doIt()

    def iterChildren(self, apiType=om.MFn.kTransform):
        """
        Returns a generator that yields all the children from this node.

        :type apiType: int
        :rtype: iter
        """

        # Check if this is a dag node
        #
        obj = self.object()

        if not obj.hasFn(om.MFn.kDagNode):

            return

        # Iterate through children
        # We purposely exclude shape nodes since these are DCC agnostic
        #
        fnDagNode = om.MFnDagNode(obj)
        childCount = fnDagNode.childCount()

        for i in range(childCount):

            child = fnDagNode.child(i)

            if child.hasFn(apiType):

                yield fnDagNode.child(i)

            else:

                continue

    def iterShapes(self):
        """
        Returns an iterator that yields all shapes from this node.

        :rtype: iter
        """

        fnDagNode = om.MFnDagNode()

        for obj in self.iterChildren(apiType=om.MFn.kShape):

            fnDagNode.setObject(obj)

            if not fnDagNode.isIntermediateObject:

                yield obj

            else:

                continue

    def shapes(self):
        """
        Returns a list of shapes from this node.

        :rtype: List[om.MObject]
        """

        return list(self.iterShapes())

    @property
    def isIntermediateObject(self):
        """
        Evaluates whether this is an intermediate object.

        :rtype: bool
        """

        # Check if object is valid
        #
        if not self.isValid():

            return False

        # Check if this is a dag node
        #
        obj = self.object()

        if obj.hasFn(om.MFn.kDagNode):

            return om.MFnDagNode(self.object()).isIntermediateObject

        else:

            return False

    def iterIntermediateObjects(self):
        """
        Returns an iterator that yields all intermediate objects from this node.

        :rtype: iter
        """

        fnDagNode = om.MFnDagNode()

        for obj in self.iterChildren(apiType=om.MFn.kShape):

            fnDagNode.setObject(obj)

            if fnDagNode.isIntermediateObject:

                yield obj

            else:

                continue

    def intermediateObjects(self):
        """
        Returns a list of intermediate objects from this node.

        :rtype: List[om.MObject]
        """

        return list(self.iterIntermediateObjects())

    def handle(self):
        """
        Returns the handle for this node.

        :rtype: int
        """

        return om.MObjectHandle(self.object()).hashCode()

    def getAttr(self, name):
        """
        Returns the specified attribute value.

        :type name: str
        :rtype: Any
        """

        plug = plugutils.findPlug(self.object(), name)
        return plugmutators.getValue(plug)

    def hasAttr(self, name):
        """
        Evaluates if this node has the specified attribute.

        :type name: str
        :rtype: bool
        """

        return om.MFnDependencyNode(self.object()).hasAttribute(name)

    def setAttr(self, name, value):
        """
        Updates the specified attribute value.

        :type name: str
        :type value: Any
        :rtype: None
        """

        plug = plugutils.findPlug(self.object(), name)
        plugmutators.setValue(plug, value)

    def iterAttr(self):
        """
        Returns a generator that yields attribute names.

        :rtype: iter
        """

        return attributeutils.iterAttributeNames(self.object())

    def isTransform(self):
        """
        Evaluates if this node represents a transform.

        :rtype: bool
        """

        return self.object().hasFn(om.MFn.kTransform)

    def isJoint(self):
        """
        Evaluates if this node represents an influence object.

        :rtype: bool
        """

        return self.object().hasFn(om.MFn.kJoint)

    def isMesh(self):
        """
        Evaluates if this node represents a mesh.

        :rtype: bool
        """

        return self.object().hasFn(om.MFn.kMesh)

    def getAssociatedReference(self):
        """
        Returns the reference this node is associated with.

        :rtype: om.MObject
        """

        return dagutils.getAssociatedReferenceNode(self.object())

    def userPropertyBuffer(self):
        """
        Returns the user property buffer.

        :rtype: str
        """

        fnDependNode = om.MFnDependencyNode(self.object())
        hasAttribute = fnDependNode.hasAttribute('notes')

        if hasAttribute:

            plug = plugutils.findPlug(self.object(), 'notes')
            return plug.asString()

        else:

            return ''

    def userProperties(self):
        """
        Returns the user properties.

        :rtype: dict
        """

        return {}

    def dependsOn(self, apiType=om.MFn.kDependencyNode):
        """
        Returns a list of nodes that this object is dependent on.

        :rtype: List[om.MObject]
        """

        return dagutils.dependsOn(self.object(), apiType=apiType)

    def dependents(self, apiType=om.MFn.kDependencyNode):
        """
        Returns a list of nodes that are dependent on this object.

        :return: List[om.MObject]
        """

        return dagutils.dependents(self.object(), apiType=apiType)

    @classmethod
    def doesNodeExist(cls, name):
        """
        Evaluates whether a node exists with the given name.

        :type name: str
        :rtype: bool
        """

        return mc.objExists(name)

    @classmethod
    def getNodeByName(cls, name):
        """
        Returns a node with the given name.
        If no node associated with this name then none is returned.

        :type name: str
        :rtype: om.MObject
        """

        node = dagutils.getMObjectByName(name)
        return node if not node.isNull() else None

    @classmethod
    def getNodeByHandle(cls, handle):
        """
        Returns a node with the given handle.
        If no node is associated with this handle then none is returned.

        :type handle: Union[str, int]
        :rtype: Any
        """

        handle = cls.__handles__.get(handle, om.MObjectHandle())

        if handle.isAlive():

            return handle.object()

        else:

            return None

    @classmethod
    def getNodesByAttribute(cls, name):
        """
        Returns a list of nodes with the given attribute name.

        :type name: str
        :rtype: List[object]
        """

        try:

            selection = om.MSelectionList()
            selection.add('*.{name}'.format(name=name))

            return [selection.getDependNode(i) for i in range(selection.length())]

        except RuntimeError:

            return []

    @classmethod
    def iterInstances(cls, apiType=om.MFn.kDependencyNode):
        """
        Returns a generator that yields texture instances.

        :type apiType: int
        :rtype: iter
        """

        return dagutils.iterNodes(apiType)
