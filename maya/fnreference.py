import maya.cmds as mc
import maya.api.OpenMaya as om

from six import integer_types, string_types
from dcc.abstract import afnreference
from dcc.maya.libs import dagutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnReference(afnreference.AFnReference):
    """
    Overload of AFnReference that defines the function set behavior for Maya references.
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
        handle = super(FnReference, self).object()

        # Inspect object type
        #
        if isinstance(handle, integer_types):

            return self.getReferenceByHandle(handle)

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
        super(FnReference, self).setObject(handle.hashCode())

    def name(self):
        """
        Returns the name of this reference node.

        :rtype: str
        """

        return om.MFnReference(self.object()).name()

    def namespace(self):
        """
        Returns the namespace for this reference.

        :rtype: str
        """

        return om.MFnReference(self.object()).namespace

    def parent(self):
        """
        Returns the parent of this node.

        :rtype: Any
        """

        fnReference = om.MFnReference(self.object())
        parent = fnReference.parentReference()

        if not parent.isNull():

            return parent

        else:

            return None

    def setParent(self, parent):
        """
        Updates the parent of this object.

        :type parent: object
        :rtype: None
        """

        raise NotImplementedError('setParent() references cannot be re-parented!')

    def iterChildren(self):
        """
        Returns a generator that yields all the children from this object.

        :rtype: iter
        """

        for node in self.iterReferencedNodes():

            if node.hasFn(om.MFn.kReference):

                yield node

            else:

                continue

    def filePath(self):
        """
        Returns the source file path for this reference.

        :rtype: str
        """

        return om.MFnReference(self.object()).fileName(True, True, False)

    def getFileProperties(self):
        """
        Returns the file properties from the source file.

        :rtype: dict
        """

        properties = mc.fileInfo(query=True, referenceNode=self.name())
        numProperties = len(properties)

        return {properties[i]: properties[i + 1].encode('ascii').decode('unicode-escape') for i in range(0, numProperties, 2)}

    def handle(self):
        """
        Returns the handle to this reference.

        :rtype: int
        """

        return om.MObjectHandle(self.object()).hashCode()

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

        fnReference = om.MFnReference()

        for dependNode in dagutils.iterNodes(om.MFn.kReference):

            fnReference.setObject(dependNode)
            parent = fnReference.parentReference()

            if parent.isNull():

                yield dependNode

            else:

                continue

    @classmethod
    def getReferenceByHandle(cls, handle):
        """
        Returns a reference with the given handle.
        If no reference is associated with this handle then none is returned.

        :type handle: Union[str, int]
        :rtype: object
        """

        handle = cls.__handles__.get(handle, om.MObjectHandle())

        if handle.isAlive():

            return handle.object()

        else:

            return None

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

