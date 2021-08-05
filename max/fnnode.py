import pymxs

from six import string_types, integer_types
from collections import deque

from ..abstract import afnnode

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnNode(afnnode.AFnNode):
    """
    Overload of AFnNode that outlines function set behaviour for interfacing with 3ds Max nodes.
    """

    __slots__ = ()

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.
        """

        # Call parent method
        #
        super(FnNode, self).__init__(*args, **kwargs)

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

        :type obj: Union[str, pymxs.MXSWrapperBase]
        :rtype: None
        """

        # Check object type
        #
        if isinstance(obj, integer_types):

            super(FnNode, self).setObject(obj)

        elif isinstance(obj, pymxs.MXSWrapperBase):

            return self.setObject(pymxs.runtime.getHandleByAnim(obj))

        elif isinstance(obj, string_types):

            return self.setObject(self.getNodeByName(obj))

        else:

            raise TypeError('setObject() expects an MObject (%s given)!' % type(obj).__name__)

    def handle(self):
        """
        Returns the handle for this node.

        :rtype: int
        """

        return int(pymxs.runtime.getHandleByAnim(self.object()))

    def name(self):
        """
        Returns the name of this node.

        :rtype: str
        """

        if self.isValid():

            return self.object().name

    def setName(self, name):
        """
        Updates the name of this node.

        :type name: str
        :rtype: None
        """

        if self.isValid():

            self.object().name = name

    def parent(self):
        """
        Returns the parent of this node.

        :rtype: om.MObject
        """

        if self.isValid():

            return self.object().parent

    def iterParents(self):
        """
        Returns a generator that yields all of the parents for this node.

        :rtype: iter
        """

        parent = self.object().parent

        while parent is not None:

            yield parent
            parent = parent.parent

    def setParent(self, parent):
        """
        Updates the parent of this node.

        :type parent: om.MObject
        :rtype: None
        """

        self.object().parent = parent

    def iterChildren(self):
        """
        Returns a generator that yields all of the children for this node.

        :rtype: iter
        """

        # Check if node is valid
        #
        if not self.isValid():

            return

        # Iterate through children
        #
        children = self.object().children

        for i in range(1, children.count + 1, 1):

            yield children[i]

    def iterDescendants(self):
        """
        Returns a generator that yields all of the descendants for this node.

        :rtype: iter
        """

        # Iterate through children
        #
        queue = deque(self.children())

        while len(queue):

            # Pop item from queue
            #
            currentNode = queue.popleft()
            yield currentNode

            # Get children from item
            #
            children = currentNode.children
            childCount = children.count

            if childCount > 0:

                queue.extend([children[i] for i in range(1, childCount + 1, 1)])

            else:

                continue

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
    def getActiveSelection(cls):
        """
        Returns the active selection.

        :rtype: list[pymxs.MXSWrapperBase]
        """

        selection = pymxs.runtime.selection
        return [selection[x] for x in range(1, selection.count + 1, 1)]
