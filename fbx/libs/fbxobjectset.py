from enum import IntEnum
from . import fbxbase
from ... import fnscene, fnnode
from ...generators.uniquify import uniquify

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxObjectSetType(IntEnum):
    """
    Overload of `IntEnum` that lists the types supported by object sets.
    """

    Nodes = 0
    Layers = 1
    SelectionSets = 2
    Regex = 3


class FbxObjectSet(fbxbase.FbxBase):
    """
    Overload of `FbxBase` used to store scene objects.
    """

    # region Dunderscores
    __slots__ = (
        '_scene',
        '_includeType',
        '_includeObjects',
        '_includeChildren',
        '_excludeType',
        '_excludeObjects',
        '_excludeChildren'
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Declare private variables
        #
        self._scene = fnscene.FnScene()
        self._includeType = kwargs.get('includeType', FbxObjectSetType.Nodes)
        self._includeObjects = kwargs.get('includeObjects', [])
        self._includeChildren = kwargs.get('includeChildren', False)
        self._excludeType = kwargs.get('excludeType', FbxObjectSetType.Nodes)
        self._excludeObjects = kwargs.get('excludeObjects', [])
        self._excludeChildren = kwargs.get('excludeChildren', False)

        # Call parent method
        #
        super(FbxObjectSet, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def scene(self):
        """
        Getter method that returns the scene interface.

        :rtype: fnscene.FnScene
        """

        return self._scene

    @property
    def includeType(self):
        """
        Getter method that returns the `include` type.

        :rtype: FbxObjectSetType
        """

        return self._includeType

    @includeType.setter
    def includeType(self, includeType):
        """
        Setter method that updates the `include` type.

        :type includeType: FbxObjectSetType
        :rtype: None
        """

        self._includeType = FbxObjectSetType(includeType)

    @property
    def includeObjects(self):
        """
        Getter method that returns the list of objects to be included.

        :rtype: List[str]
        """

        return self._includeObjects

    @includeObjects.setter
    def includeObjects(self, includeObjects):
        """
        Setter method that updates the list of objects to be included.

        :type includeObjects: List[str]
        :rtype: None
        """

        self._includeObjects.clear()
        self._includeObjects.extend(includeObjects)
    
    @property
    def includeChildren(self):
        """
        Getter method that returns the `includeChildren` flag.

        :rtype: bool
        """

        return self._includeChildren

    @includeChildren.setter
    def includeChildren(self, includeChildren):
        """
        Setter method that updates the `includeChildren` flag.

        :type includeChildren: bool
        :rtype: None
        """

        self._includeChildren = includeChildren

    @property
    def excludeType(self):
        """
        Getter method that returns the `exclude` type.

        :rtype: FbxObjectSetType
        """

        return self._excludeType

    @excludeType.setter
    def excludeType(self, excludeType):
        """
        Setter method that updates the `exclude` type.

        :type excludeType: FbxObjectSetType
        :rtype: None
        """

        self._excludeType = FbxObjectSetType(excludeType)

    @property
    def excludeObjects(self):
        """
        Getter method that returns the list of objects to be excluded.

        :rtype: List[str]
        """

        return self._excludeObjects

    @excludeObjects.setter
    def excludeObjects(self, excludeObjects):
        """
        Setter method that updates the list of objects to be excluded.

        :type excludeObjects: List[str]
        :rtype: None
        """

        self._excludeObjects.clear()
        self._excludeObjects.extend(excludeObjects)

    @property
    def excludeChildren(self):
        """
        Getter method that returns the `excludeChildren` flag.

        :rtype: bool
        """

        return self._excludeChildren

    @excludeChildren.setter
    def excludeChildren(self, excludeChildren):
        """
        Setter method that updates the `excludeChildren` flag.

        :type excludeChildren: bool
        :rtype: None
        """

        self._excludeChildren = excludeChildren
    # endregion

    # region Methods
    def iterIncludeObjects(self, namespace=''):
        """
        Returns a generator that yields objects that should be included.

        :type namespace: str
        :rtype: Iterator[Any]
        """

        if self.includeType == FbxObjectSetType.Nodes:

            return self.iterNodesFromNames(self.name, *self.includeObjects, includeChildren=self.includeChildren, namespace=namespace)

        elif self.includeType == FbxObjectSetType.Layers:

            return self.iterNodesFromLayers(self.name, *self.includeObjects, namespace=namespace)

        elif self.includeType == FbxObjectSetType.SelectionSets:

            return self.iterNodesFromSelectionSets(self.name, *self.includeObjects, namespace=namespace)

        elif self.includeType == FbxObjectSetType.Regex:

            return self.iterNodesFromRegex(self.name, *self.includeObjects, namespace=namespace)

        else:

            raise TypeError(f'iterIncludeObjects() expects a valid set type ({self.includeType} given)!')

    def iterExcludeObjects(self, namespace=''):
        """
        Returns a generator that yields objects that should be excluded.

        :type namespace: str
        :rtype: Iterator[Any]
        """

        if self.excludeType == FbxObjectSetType.Nodes:

            return self.iterNodesFromNames(self.name, *self.excludeObjects, includeChildren=self.excludeChildren, namespace=namespace)

        elif self.excludeType == FbxObjectSetType.Layers:

            return self.iterNodesFromLayers(self.name, *self.excludeObjects, namespace=namespace)

        elif self.excludeType == FbxObjectSetType.SelectionSets:

            return self.iterNodesFromSelectionSets(self.name, *self.excludeObjects, namespace=namespace)

        elif self.excludeType == FbxObjectSetType.Regex:

            return self.iterNodesFromRegex(self.name, *self.excludeObjects, namespace=namespace)

        else:

            raise TypeError(f'iterExcludeObjects() expects a valid set type ({self.excludeType} given)!')

    def getObjects(self, namespace=''):
        """
        Returns a list of objects from this set.

        :type namespace: str
        :rtype: List[Any]
        """

        includeObjects = list(self.iterIncludeObjects(namespace=namespace))
        excludeObjects = list(self.iterExcludeObjects(namespace=namespace))

        return [obj for obj in includeObjects if obj not in excludeObjects]

    def select(self, namespace=''):
        """
        Selects the associated nodes from the scene file.

        :type namespace: str
        :rtype: None
        """

        objects = self.getObjects(namespace=namespace)
        self.scene.setActiveSelection(objects, replace=False)
    # endregion
