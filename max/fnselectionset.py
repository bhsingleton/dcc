import pymxs

from six import string_types, integer_types
from . import fnnode
from ..abstract import afnselectionset

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnSelectionSet(afnselectionset.AFnSelectionSet):
    """
    Overload of AFnBase that outlines the function set behaviour for selection sets.
    """

    __slots__ = ()

    def object(self):
        """
        Returns the object assigned to this function set.

        :rtype: Union[pymxs.MXSWrapperBase, None]
        """

        # Call parent method
        #
        name = super(FnSelectionSet, self).object()

        if isinstance(name, string_types):

            return pymxs.runtime.SelectionSets[name]

        else:

            return None

    def setObject(self, obj):
        """
        Assigns an object to this function set for manipulation.
        If the object is not compatible then raise a type error.

        :type obj: Union[str, int, pymxs.MXSWrapperBase]
        :rtype: None
        """

        if isinstance(obj, string_types):

            # Check if name exists
            #
            selectionSet = pymxs.runtime.SelectionSets[obj]

            if selectionSet is not None:

                return self.setObject(selectionSet)

            else:

                raise TypeError('setObject() name does not exist!')

        elif isinstance(obj, integer_types):

            # Check if index is in range
            #
            numSelectionSets = pymxs.runtime.SelectionSets.count

            if 0 <= obj < numSelectionSets:

                return self.setObject(pymxs.runtime.SelectionSets[obj])

            else:

                raise TypeError('setObject() index out of range!')

        elif isinstance(obj, pymxs.MXSWrapperBase):

            # Verify this is a selection set
            #
            if pymxs.runtime.isKindOf(obj, pymxs.runtime.SelectionSet):

                return super(FnSelectionSet, self).setObject(obj.name)

            else:

                raise TypeError('setObject() expects a SelectionSet (%s given)' % pymxs.runtime.classOf(obj))

        else:

            raise TypeError('setObject() expects a str or MXSWrapper (%s given)!' % type(obj).__name__)

    def name(self):
        """
        Returns the name of this object.

        :rtype: str
        """

        return self.object().name

    def setName(self, name):
        """
        Updates the name of this object.

        :type name: str
        :rtype: None
        """

        self.object().name = name

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

        selectionSet = self.object()
        numNodes = selectionSet.count

        for i in range(numNodes):

            yield selectionSet[i]

    def containsNode(self, obj):
        """
        Evaluates if this selection set contains the specified node.

        :type obj: Any
        :rtype: bool
        """

        selectionSet = self.object()

        node = fnnode.FnNode()
        success = node.trySetObject(obj)

        if success:

            return pymxs.runtime.findItem(selectionSet, node.object()) > 0

        else:

            return False

    def addNodes(self, *nodes):
        """
        Adds the supplied nodes to this layer.

        :type nodes: Sequence[object]
        :rtype: None
        """

        selectionSet = self.object()

        node = fnnode.FnNode()
        node.setQueue(nodes)

        while not node.isDone():

            pymxs.runtime.appendIfUnique(selectionSet, node.object())
            node.next()

    def removeNodes(self, *nodes):
        """
        Removes the supplied nodes from this layer.

        :type nodes: Sequence[object]
        :rtype: None
        """

        selectionSet = self.object()

        node = fnnode.FnNode()
        node.setQueue(nodes)

        while not node.isDone():

            index = pymxs.runtime.findItem(selectionSet, node.object())

            if index > 0:

                pymxs.runtime.deleteItem(selectionSet, index)

            else:

                node.next()
                continue
