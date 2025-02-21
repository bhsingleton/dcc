from maya import cmds as mc
from maya import OpenMaya as lom
from maya.api import OpenMaya as om
from . import fnnode
from .libs import dagutils
from ..abstract import afnreference
from ..vendor.six import integer_types, string_types

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnReference(fnnode.FnNode, afnreference.AFnReference):
    """
    Overload of AFnReference that defines the function set behavior for Maya references.
    """

    __slots__ = ()

    def parent(self):
        """
        Returns the parent of this object.

        :rtype: om.MObject
        """

        reference = om.MFnReference(self.object())
        parentReference = reference.parentReference()

        if not parentReference.isNull():

            return parentReference

        else:

            return None

    def iterChildren(self):
        """
        Returns a generator that yields all the children from this object.

        :rtype: Iterator[om.MObject]
        """

        reference = om.MFnReference(self.object())

        child = self.__class__()
        child.setQueue(self.iterSceneReferences(topLevelOnly=False))

        while not child.isDone():

            childNode = child.object()
            isChild = reference.containsNodeExactly(childNode)

            if isChild:

                yield childNode

            child.next()

    def setNamespace(self, namespace):
        """
        Updates the namespace for this node.

        :type namespace: str
        :rtype: None
        """

        pass

    def associatedNamespace(self):
        """
        Returns the namespace associated with the referenced nodes.

        :rtype: str
        """

        return om.MFnReference(self.object()).associatedNamespace(False)

    def uid(self):
        """
        Returns a unique identifier to this reference.

        :rtype: str
        """

        return om.MFnReference(self.object()).uuid().asString()

    def filePath(self):
        """
        Returns the source file path for this reference.

        :rtype: str
        """

        return om.MFnReference(self.object()).fileName(True, False, False)  # `includePath` flag is inversed???

    def fileProperties(self):
        """
        Returns the file properties from the source file.

        :rtype: dict
        """

        referenceNode = f'{self.namespace()}:{self.name()}'

        properties = mc.fileInfo(query=True, referenceNode=referenceNode)
        numProperties = len(properties)

        return {properties[i]: properties[i + 1].encode('ascii').decode('unicode-escape') for i in range(0, numProperties, 2)}

    def isLoaded(self):
        """
        Evaluates if this reference is loaded.

        :rtype: bool
        """

        return om.MFnReference(self.object()).isLoaded()

    def load(self):
        """
        Loads the reference.

        :rtype: None
        """

        isLoaded = self.isLoaded()

        if not isLoaded:

            lom.MFileIO.loadReferenceByNode(dagutils.demoteMObject(self.object()))

    def unload(self):
        """
        Unloads the reference.

        :rtype: None
        """

        isLoaded = self.isLoaded()

        if isLoaded:

            lom.MFileIO.unloadReferenceByNode(dagutils.demoteMObject(self.object()))

    def iterReferencedNodes(self):
        """
        Returns a generator that yields all referenced nodes.

        :rtype: iter
        """

        return iter(om.MFnReference(self.object()).nodes())

    @classmethod
    def iterSceneReferences(cls, topLevelOnly=True):
        """
        Returns a generator that yields top-level scene references.

        :type topLevelOnly: bool
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
                isNested = not parent.isNull()

                if topLevelOnly and isNested:

                    continue

                else:

                    yield dependNode

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
