import maya.cmds as mc
import maya.api.OpenMaya as om

from six import string_types, integer_types
from collections import deque

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

        # Check object type
        #
        if isinstance(obj, om.MObjectHandle):

            hashCode = obj.hashCode()
            self.__handles__[hashCode] = obj

            super(FnNode, self).setObject(hashCode)

        elif isinstance(obj, om.MObject):

            return self.setObject(om.MObjectHandle(obj))

        elif isinstance(obj, om.MDagPath):

            return self.setObject(obj.node())

        elif isinstance(obj, string_types):

            return self.setObject(self.getNodeByName(obj))

        elif isinstance(obj, integer_types):

            return self.setObject(self.getNodeByHandle(obj))

        else:

            raise TypeError('setObject() expects an MObject (%s given)!' % type(obj).__name__)

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

    def iterParents(self):
        """
        Returns a generator that yields all of the parents for this node.

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

        # Iterate through parents
        #
        fnDagNode = om.MFnDagNode(self.object())

        while fnDagNode.hasParent():

            parent = fnDagNode.parent(0)
            yield parent

            fnDagNode.setObject(parent)

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

    def iterChildren(self):
        """
        Returns a generator that yields all of the children belonging to this node.

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
        #
        fnDagNode = om.MFnDagNode(obj)
        childCount = fnDagNode.childCount()

        for i in range(childCount):

            yield fnDagNode.child(i)

    def iterDescendants(self):
        """
        Returns a generator that yields all of the descendants for this node.

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
        #
        fnDagNode = om.MFnDagNode(obj)
        queue = deque([fnDagNode.child(i) for i in range(fnDagNode.childCount())])

        while len(queue):

            # Pop item from queue
            #
            currentNode = queue.popleft()
            yield currentNode

            # Get children from item
            #
            fnDagNode.setObject(currentNode)
            queue.extend([fnDagNode.child(i) for i in range(fnDagNode.childCount())])

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
