from maya.api import OpenMaya as om
from . import fnnode
from .libs import dagutils
from ..abstract import afnselectionset

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnSelectionSet(fnnode.FnNode, afnselectionset.AFnSelectionSet):
    """
    Overload of AFnSelectionSet that outlines the function set behaviour for selection sets.
    """

    __slots__ = ()

    def iterNodes(self):
        """
        Returns a generator that yields nodes from this layer.

        :rtype: iter
        """

        fnSet = om.MFnSet(self.object())
        members = fnSet.getMembers(True)

        numMembers = members.length()

        for i in range(numMembers):

            member = members.getDependNode(i)
            yield member

    def addNodes(self, *nodes):
        """
        Adds the supplied nodes to this layer.

        :type nodes: Sequence[object]
        :rtype: None
        """

        fnSet = om.MFnSet(self.object())

        for node in nodes:

            dependNode = dagutils.getMObject(node)

            if not fnSet.isMember(dependNode):

                fnSet.addMember(dependNode)

            else:

                continue

    def containsNode(self, node):
        """
        Evaluates if this selection set contains the specified node.

        :type node: Any
        :rtype: bool
        """

        dependNode = dagutils.getMObject(node)
        return om.MFnSet(self.object()).isMember(dependNode)

    def removeNodes(self, *nodes):
        """
        Removes the supplied nodes from this layer.

        :type nodes: Sequence[object]
        :rtype: None
        """

        fnSet = om.MFnSet(self.object())

        for node in nodes:

            dependNode = dagutils.getMObject(node)

            if fnSet.isMember(dependNode):

                fnSet.removeMember(dependNode)

            else:

                continue
