import maya.cmds as mc
import maya.api.OpenMaya as om

from six import integer_types

from .libs import dagutils
from ..abstract import afnnode
from ..decorators.validator import validator

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

        # Get maya object
        #
        obj = dagutils.getMObject(obj)
        handle = om.MObjectHandle(obj)

        self.__handles__[handle.hashCode()] = handle

        # Assign node handle
        #
        super(FnNode, self).setObject(handle.hashCode())

    def acceptsObject(self, obj):
        """
        Evaluates whether the supplied object is supported by this function set.

        :type obj: Any
        :rtype: bool
        """

        return isinstance(obj, (str, om.MObject, om.MDagPath, om.MObjectHandle))

    @validator
    def handle(self):
        """
        Returns the handle for this node.

        :rtype: int
        """

        return om.MObjectHandle(self.object()).hashCode()

    @validator
    def name(self):
        """
        Returns the name of this node.

        :rtype: str
        """

        return om.MFnDependencyNode(self.object()).name()

    @validator
    def setName(self, name):
        """
        Updates the name of this node.

        :type name: str
        :rtype: None
        """

        om.MFnDependencyNode(self.object()).setName(name)

    @validator
    def isMesh(self):
        """
        Evaluates if this node represents a mesh.

        :rtype: bool
        """

        return self.object().hasFn(om.MFn.kMesh)

    @validator
    def isJoint(self):
        """
        Evaluates if this node represents a skinnable influence.

        :rtype: bool
        """

        return self.object().hasFn(om.MFn.kJoint)

    @validator
    def parent(self):
        """
        Returns the parent of this node.

        :rtype: om.MObject
        """

        # Check if node is valid
        #
        if not self.isValid():

            return None

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

    @validator
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

    @validator
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

    def dependsOn(self, apiType=om.MFn.kDependencyNode):
        """
        Returns a list of nodes that this object is dependent on.

        :rtype: list[om.MObject]
        """

        return dagutils.dependsOn(self.object(), apiType=apiType)

    def dependents(self, apiType=om.MFn.kDependencyNode):
        """
        Returns a list of nodes that are dependent on this object.

        :return: list[om.MObject]
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

        handle = cls.__handles__.get(handle, om.MObjectHandle())

        if handle.isAlive():

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
        if not replace:

            selection.extend(cls.getActiveSelection())

        # Update selection global
        #
        om.MGlobal.setActiveSelectionList(selection)

    @classmethod
    def clearActiveSelection(cls):
        """
        Clears the active selection.

        :rtype: None
        """

        om.MGlobal.clearSelectionList()

    @classmethod
    def iterActiveComponentSelection(cls):
        """
        Returns a generator that yields all selected components

        :rtype: iter
        """

        # Access the Maya global selection list
        #
        selection = om.MGlobal.getActiveSelectionList()
        numSelected = selection.length()

        if numSelected == 0:

            return

        # Iterate through selection
        #
        iterSelection = om.MItSelectionList(selection, om.MFn.kComponent)

        while not iterSelection.isDone():

            # Check if items are valid
            #
            dagPath, component = iterSelection.getComponent()

            if dagPath.isValid() and not component.isNull():

                yield dagPath, component

            # Go to next selection
            #
            iterSelection.next()
