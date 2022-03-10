import pymxs

from six import integer_types, string_types
from dcc import structuredstorage
from dcc.abstract import afnreference, ArrayIndexType

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnReference(afnreference.AFnReference):
    """
    Overload of AFnReference that implements the function set behavior for Maya references.
    """

    __slots__ = ()
    __arrayindextype__ = ArrayIndexType.OneBased

    def object(self):
        """
        Returns the object assigned to this function set.

        :rtype: pymxs.MXSWrapperBase
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

        :type obj: Union[str, int, pymxs.MXSWrapperBase]
        :rtype: None
        """

        # Get maxscript wrapper
        #
        obj = self.getMXSWrapper(obj)
        handle = pymxs.runtime.getHandleByAnim(obj)

        # Assign anim handle
        #
        super(FnReference, self).setObject(handle)

    def namespace(self):
        """
        Returns the namespace for this reference.

        :rtype: str
        """

        return ''

    def parent(self):
        """
        Returns the parent of this node.

        :rtype: Any
        """

        obj = self.object()
        numParents, parents = obj.getParentRecords(pymxs.byref(None))

        if len(numParents) > 0:

            return parents[0]

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

        obj = self.object()
        numChildren, children = obj.getChildRecords(pymxs.byref(None))

        return iter(children)

    def filePath(self):
        """
        Returns the source file path for this reference.

        :rtype: str
        """

        return self.object().srcFileName

    def getFileProperties(self):
        """
        Returns the file properties from the source file.

        :rtype: dict
        """

        if self.exists():

            return structuredstorage.getFileProperties(self.filePath())

        else:

            return {}

    def handle(self):
        """
        Returns the handle to this reference.

        :rtype: int
        """

        return self.object().handle

    def uid(self):
        """
        Returns a unique identifier to this reference.

        :rtype: str
        """

        if self.hasParent():

            parent = self.parent()
            numSiblings, siblings = parent.getChildRecords(pymxs.byref(None))

            return list(siblings).index(self)

        else:

            return list(self.iterSceneReferences()).index(self)

    def iterReferencedNodes(self):
        """
        Returns a generator that yields all referenced nodes.

        :rtype: iter
        """

        nodes = pymxs.runtime.Array()
        nodes = self.object().getNodes(pymxs.byref(nodes))

        return iter(nodes)

    @classmethod
    def getMXSWrapper(cls, value):
        """
        Returns an MXSWrapper from any given value.

        :type value: Union[str, int, pymxs.MXSWrapperBase]
        :rtype: pymxs.MXSWrapperBase
        """

        # Check object type
        #
        if isinstance(value, pymxs.MXSWrapperBase):

            return value

        elif isinstance(value, integer_types):

            return cls.getReferenceByHandle(value)

        else:

            raise TypeError('setObject() expects a str or int (%s given)!' % type(value).__name__)

    @classmethod
    def iterSceneReferences(cls):
        """
        Returns a generator that yields top-level scene references.

        :rtype: iter
        """

        numRecords = pymxs.runtime.objXRefMgr.recordCount

        for i in range(1, numRecords + 1, 1):

            record = pymxs.runtime.objXRefMgr.getRecord(i)

            if not record.nested:

                yield record

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

        return pymxs.runtime.getAnimByHandle(handle)

    @classmethod
    def getReferenceByUid(cls, uid, parentReference=None):
        """
        Returns a reference with the given UID.
        If no reference is associated with this UID then none is returned.

        :type uid: Union[int, str]
        :type parentReference: None
        :rtype: object
        """

        # Check uid type
        #
        if isinstance(uid, string_types):

            uid = int(uid)

        # Check if parent reference was supplied
        #
        if parentReference is not None:

            numChildren, children = parentReference.getChildRecords(pymxs.byref(None))

            if 0 <= uid < numChildren:

                return children[uid]

            else:

                return None

        else:

            records = list(cls.iterSceneReferences())
            numRecords = len(records)

            if 0 < uid < numRecords:

                return records[uid]

            else:

                return None
