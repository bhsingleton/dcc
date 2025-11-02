from ..abstract import afnreference

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnReference(afnreference.AFnReference):
    """
    Overload of `AFnReference` that implements the function set behavior for Blender references.
    """

    __slots__ = ()

    def name(self):
        """
        Returns the name of this object.

        :rtype: str
        """

        return ''

    def setName(self, name):
        """
        Updates the name of this object.

        :type name: str
        :rtype: None
        """

        pass

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

    def associatedNamespace(self):
        """
        Returns the namespace associated with the referenced nodes.

        :rtype: str
        """

        return ''

    def parent(self):
        """
        Returns the parent of this node.

        :rtype: Any
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

    def handle(self):
        """
        Returns the handle to this reference.

        :rtype: int
        """

        return 0

    def uid(self):
        """
        Returns a unique identifier to this reference.

        :rtype: str
        """

        return ''

    def filePath(self):
        """
        Returns the source file path for this reference.

        :rtype: str
        """

        return ''

    def fileProperties(self):
        """
        Returns the file properties from the source file.

        :rtype: dict
        """

        return {}

    def isLoaded(self):
        """
        Evaluates if this reference is loaded.

        :rtype: bool
        """

        return False

    def load(self):
        """
        Loads the reference.

        :rtype: None
        """

        pass

    def unload(self):
        """
        Unloads the reference.

        :rtype: None
        """

        pass

    def iterReferencedNodes(self):
        """
        Returns a generator that yields all referenced nodes.

        :rtype: iter
        """

        return iter([])

    @classmethod
    def iterSceneReferences(cls, topLevelOnly=True):
        """
        Returns a generator that yields top-level scene references.

        :type topLevelOnly: bool
        :rtype: iter
        """

        return iter([])

    @classmethod
    def getReferenceByHandle(cls, handle):
        """
        Returns a reference with the given handle.
        If no reference is associated with this handle then none is returned.

        :type handle: Union[str, int]
        :rtype: object
        """

        return

    @classmethod
    def getReferenceByUid(cls, uid, parentReference=None):
        """
        Returns a reference with the given UID.
        If no reference is associated with this UID then none is returned.

        :type uid: Union[int, str]
        :type parentReference: None
        :rtype: object
        """

        return
