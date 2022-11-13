import maya.cmds as mc
import maya.api.OpenMaya as om

from six import integer_types, string_types
from dcc.abstract import afnreference
from dcc.maya import fnnode
from dcc.maya.libs import dagutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnReference(fnnode.FnNode, afnreference.AFnReference):
    """
    Overload of AFnReference that defines the function set behavior for Maya references.
    """

    __slots__ = ()

    def namespace(self):
        """
        Returns the namespace for this node.

        :rtype: str
        """

        return om.MFnReference(self.object()).associatedNamespace(False)

    def setNamespace(self, namespace):
        """
        Updates the namespace for this node.

        :type namespace: str
        :rtype: None
        """

        pass

    def filePath(self):
        """
        Returns the source file path for this reference.

        :rtype: str
        """

        return om.MFnReference(self.object()).fileName(True, False, False)  # includePath variable is inversed???

    def fileProperties(self):
        """
        Returns the file properties from the source file.

        :rtype: dict
        """

        properties = mc.fileInfo(query=True, referenceNode=self.name())
        numProperties = len(properties)

        return {properties[i]: properties[i + 1].encode('ascii').decode('unicode-escape') for i in range(0, numProperties, 2)}

    def uid(self):
        """
        Returns a unique identifier to this reference.

        :rtype: str
        """

        return om.MFnReference(self.object()).uuid().asString()

    def iterReferencedNodes(self):
        """
        Returns a generator that yields all referenced nodes.

        :rtype: iter
        """

        return iter(om.MFnReference(self.object()).nodes())

    @classmethod
    def iterSceneReferences(cls):
        """
        Returns a generator that yields top-level scene references.

        :rtype: iter
        """

        # Iterate through reference nodes
        #
        fnReference = om.MFnReference()

        for dependNode in dagutils.iterNodes(om.MFn.kReference):

            # Check if this is a top-level reference
            #
            try:

                fnReference.setObject(dependNode)
                parent = fnReference.parentReference()

                if parent.isNull():

                    yield dependNode

                else:

                    continue

            except RuntimeError:

                continue  # Reserved for shared reference nodes!

    @classmethod
    def getReferenceByHandle(cls, handle):
        """
        Returns a reference with the given handle.
        If no reference is associated with this handle then none is returned.

        :type handle: Union[str, int]
        :rtype: object
        """

        return cls.getNodeByHandle(handle)

    @classmethod
    def getReferenceByUid(cls, uid, parentReference=None):
        """
        Returns a reference with the given UID.
        If no reference is associated with this UID then none is returned.

        :type uid: Union[int, str]
        :type parentReference: object
        :rtype: object
        """

        # Check uid type
        #
        if isinstance(uid, string_types):

            uid = om.MUuid(uid)

        # Find node by UUID
        #
        found = dagutils.getMObjectByMUuid(uid)

        if isinstance(found, om.MObject):

            return found if not found.isNull() else None

        # Filter nodes by parent reference
        #
        filtered = [x for x in found if dagutils.getAssociatedReferenceNode(x) == parentReference]
        numFiltered = len(filtered)

        if numFiltered == 0:

            return None

        elif numFiltered == 1:

            return filtered[0]

        else:

            raise TypeError('getReferenceByUid() expects a unique UUID (%s given)!' % uid)
