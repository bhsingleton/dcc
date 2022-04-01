from six import integer_types
from collections import deque
from dcc.fbx import fbxbase
from dcc.collections import notifylist

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxObject(fbxbase.FbxBase):
    """
    Overload of FbxBase that outlines a parent/child interface.
    """

    # region Dunderscores
    __slots__ = ('_parent', '_children')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(FbxObject, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._parent = self.nullWeakReference
        self._children = notifylist.NotifyList()

        # Setup child notifies
        #
        self._children.addCallback('itemAdded', self.childAdded)
        self._children.addCallback('itemRemoved', self.childRemoved)
    # endregion

    # region Properties
    @property
    def parent(self):
        """
        Getter method that returns the parent of this object.

        :rtype: FbxObject
        """

        return self._parent()

    @property
    def children(self):
        """
        Getter method that returns the children belonging to this object.

        :rtype: List[FbxObject]
        """

        return self._children

    @children.setter
    def children(self, children):
        """
        Setter method that updates the children belonging to this object.

        :type children: List[FbxObject]
        :rtype: None
        """

        self._children.clear()
        self._children.extend(children)
    # endregion

    # region Methods
    def hasParent(self):
        """
        Checks if this object has a parent.

        :rtype: bool
        """

        return self.parent is not None

    def iterParents(self):
        """
        Returns a generator that can iterate over all of the upstream parents.

        :rtype: iter
        """

        # Iterate until we reach the end
        #
        current = self.parent

        while current is not None:

            yield current
            current = current.parent

    def topLevelParent(self):
        """
        Returns the top most parent of this object.

        :rtype: FbxObject
        """

        # Collect all parents
        #
        parents = list(self.iterParents())
        numParents = len(parents)

        if numParents == 0:

            return None

        else:

            return parents[-1]

    def iterSiblings(self):
        """
        Returns a generator that can iterate through this object's siblings.

        :rtype: iter
        """

        # Check if object has a parent
        #
        if not self.hasParent():

            return

        # Iterate through children
        #
        for child in self.parent.children:

            if child is self:

                continue

            else:

                yield child

    def siblings(self):
        """
        Returns a list of siblings belonging to this object.

        :rtype: list[FbxObject]
        """

        return list(self.iterSiblings())

    def walk(self):
        """
        Returns a generator that can walk over the entire hierarchy.

        :rtype: iter
        """

        queue = deque(self.children)

        while len(queue):

            obj = queue.popleft()
            yield obj

            queue.extend(obj.children)
    # endregion

    # region Callbacks
    def childAdded(self, index, child):
        """
        Callback to whenever a child is added to this object.
        This method will add a parent reference to the new child.

        :type index: int
        :type child: FbxObject
        :rtype: None
        """

        # Cleanup old references
        #
        if child.hasParent():

            child.parent.children.remove(child)

        # Assign new reference
        #
        child._parent = self.weakReference()

    def childRemoved(self, child):
        """
        Callback to whenever a child is remove from this object.
        This method will remove the parent reference from the orphaned child.

        :type child: FbxObject
        :rtype: None
        """

        child._parent = self.nullWeakReference
    # endregion
