import os

from abc import ABCMeta, abstractmethod
from six import with_metaclass
from dcc.abstract import afnobject

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnReference(with_metaclass(ABCMeta, afnobject.AFnObject)):
    """
    Overload of AFnObject that outlines scene reference interfaces.
    """

    __slots__ = ()

    def isValid(self):
        """
        Evaluates if this function set is valid.

        :rtype: bool
        """

        return self.object() is not None

    @abstractmethod
    def handle(self):
        """
        Returns the handle to this reference.

        :rtype: int
        """

        pass

    @abstractmethod
    def uid(self):
        """
        Returns a unique identifier to this reference.

        :rtype: str
        """

        pass

    def guid(self):
        """
        Returns a global unique identifier to this reference.

        :rtype: str
        """

        fnReference = self.__class__()
        uids = []

        for reference in self.trace():

            fnReference.setObject(reference)
            uids.append(fnReference.uid())

        return ':'.join(uids)

    @abstractmethod
    def filePath(self):
        """
        Returns the source file path for this reference.

        :rtype: str
        """

        pass

    def exists(self):
        """
        Evaluates if the source file exists.

        :rtype: bool
        """

        return os.path.exists(self.filePath())

    @abstractmethod
    def associatedNamespace(self):
        """
        Returns the namespace associated with the referenced nodes.

        :rtype: str
        """

        pass

    @abstractmethod
    def fileProperties(self):
        """
        Returns the file properties from the source file.

        :rtype: dict
        """

        pass

    def getFileProperty(self, key, default=None):
        """
        Returns a file property from the source file.

        :type key: str
        :type default: Any
        :rtype: Any
        """

        return self.getFileProperties().get(key, default)

    @abstractmethod
    def iterReferencedNodes(self):
        """
        Returns a generator that yields all referenced nodes.

        :rtype: iter
        """

        pass

    def referencedNodes(self):
        """
        Returns a list of referenced nodes.

        :rtype: List[object]
        """

        return list(self.iterReferencedNodes())

    @classmethod
    @abstractmethod
    def iterSceneReferences(cls, topLevelOnly=True):
        """
        Returns a generator that yields top-level scene references.

        :type topLevelOnly: bool
        :rtype: iter
        """

        pass

    @classmethod
    @abstractmethod
    def getReferenceByHandle(cls, handle):
        """
        Returns a reference with the given handle.
        If no reference is associated with this handle then none is returned.

        :type handle: Union[str, int]
        :rtype: object
        """

        pass

    @classmethod
    @abstractmethod
    def getReferenceByUid(cls, uid, parentReference=None):
        """
        Returns a reference with the given UID.
        If no reference is associated with this UID then none is returned.

        :type uid: Union[int, str]
        :type parentReference: object
        :rtype: object
        """

        pass

    @classmethod
    def getReferenceByGuid(cls, guid):
        """
        Returns a reference with the given handle.
        If no reference is associated with this GUID then none is returned.

        :type guid: str
        :rtype: object
        """

        uids = guid.split(':')
        parentReference = None

        for uid in uids:

            parentReference = cls.getReferenceByUid(uid, parentReference=parentReference)

        return parentReference
