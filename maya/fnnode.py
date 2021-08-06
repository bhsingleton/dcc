import maya.cmds as mc
import maya.api.OpenMaya as om

from six import string_types, integer_types

from ..abstract import afnnode

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnNode(afnnode.AFnNode):
    """
    Overload of AFnNode that outlines function set behaviour for interfacing with Maya nodes.
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

        try:

            obj = self.getMObject(obj)
            super(FnNode, self).setObject(om.MObjectHandle(obj).hashCode())

        except TypeError as exception:

            log.error(exception)
            return

    def handle(self):
        """
        Returns the handle for this node.

        :rtype: int
        """

        return om.MObjectHandle(self.object()).hashCode()

    def name(self):
        """
        Returns the name of this node.

        :rtype: str
        """

        return om.MFnDependencyNode(self.object()).name()

    def setName(self, name):
        """
        Updates the name of this node.

        :type name: str
        :rtype: None
        """

        om.MFnDependencyNode(self.object()).setName(name)

    def parent(self):
        """
        Returns the parent of this node.

        :rtype: om.MObject
        """

        # Check if node is valid
        #
        if not self.isValid():

            return

        # Check if this is a dag node
        #
        obj = self.object()

        if obj.hasFn(om.MFn.kDagNode):

            return om.MFnDagNode(obj).parent(0)

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
        Returns a generator that yields all of the children belonging to this node.

        :type apiType: int
        :rtype: iter
        """

        # Check if node is valid
        #
        if not self.isValid():

            return

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

        :rtype: list[om.MObject]
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

        :rtype: list[om.MObject]
        """

        return list(self.iterIntermediateObjects())

    @classmethod
    def iterDependencies(cls, dependNode, apiType, direction=om.MItDependencyGraph.kDownstream, traversal=om.MItDependencyGraph.kDepthFirst):
        """
        Returns a generator that yields dependencies based on the supplied arguments.

        :type dependNode: om.MObject
        :type apiType: int
        :type direction: int
        :type traversal: int
        :rtype: iter
        """

        # Initialize dependency graph iterator
        #
        iterDepGraph = om.MItDependencyGraph(
            dependNode,
            filter=apiType,
            direction=direction,
            traversal=traversal,
            level=om.MItDependencyGraph.kNodeLevel
        )

        while not iterDepGraph.isDone():

            # Get current node
            #
            currentNode = iterDepGraph.currentNode()
            yield currentNode

            # Increment iterator
            #
            iterDepGraph.next()

    def dependsOn(self, apiType=om.MFn.kDependencyNode):
        """
        Returns a list of nodes that this object is dependent on.

        :rtype: list[om.MObject]
        """

        return list(self.iterDependencies(self.object(), apiType, direction=om.MItDependencyGraph.kUpstream))

    def dependents(self, apiType=om.MFn.kDependencyNode):
        """
        Returns a list of nodes that are dependent on this object.

        :return: list[om.MObject]
        """

        return list(self.iterDependencies(self.object(), apiType, direction=om.MItDependencyGraph.kDownstream))

    @classmethod
    def getMObject(cls, value):
        """
        Returns an MObject from any given value.

        :type value: Union[str, int, om.MObject, om.MDagPath, om.MObjectHandle]
        :rtype: om.MObject
        """

        # Check value type
        #
        if isinstance(value, om.MObject):

            handle = om.MObjectHandle(value)
            cls.__handles__[handle.hashCode()] = handle

            return value

        elif isinstance(value, om.MObjectHandle):

            return value.object()

        elif isinstance(value, om.MDagPath):

            return value.node()

        elif isinstance(value, string_types):

            return cls.getNodeByName(value)

        elif isinstance(value, integer_types):

            return cls.getNodeByHandle(value)

        else:

            raise TypeError('getMObject() expects a str or int (%s given)!' % type(value).__name__)

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

        try:

            selection = om.MSelectionList()
            selection.add(name)

            return selection.getDependNode(0)

        except RuntimeError as exception:

            log.debug(exception)
            return None

    @classmethod
    def getNodeByHandle(cls, handle):
        """
        Returns a node with the given handle.
        If no node is associated with this handle then none is returned.

        :type handle: Union[str, int]
        :rtype: Any
        """

        handle = cls.__handles__.get(handle, None)

        if isinstance(handle, om.MObjectHandle):

            return handle.object()

        else:

            return None

    @classmethod
    def getActiveSelection(cls):
        """
        Returns the active selection.

        :rtype: list[om.MObject]
        """

        selection = om.MGlobal.getActiveSelectionList()  # type: om.MSelectionList
        selectionCount = selection.length()

        return [selection.getDependNode(i) for i in range(selectionCount)]
