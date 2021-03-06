from abc import abstractmethod
from enum import IntEnum
from dcc import fnnode, fnlayer
from dcc.fbx import fbxobject

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxNode(fbxobject.FbxObject):
    """
    Overload of FbxObject used to outline a node interface.
    """

    # region Dunderscores
    __slots__ = ('_fnNode',)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(FbxNode, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._fnNode = fnnode.FnNode()
    # endregion

    # region Properties
    @property
    def fnNode(self):
        """
        Getter method that returns the function set for this node.

        :rtype: fnnode.FnNode
        """

        return self._fnNode
    # endregion

    # region Methods
    def niceName(self):
        """
        Method used to retrieve a string name without any pipe or colon characters.

        :rtype: str
        """

        return self.name.split('|')[-1].split(':')[-1]

    @abstractmethod
    def icon(self):
        """
        Returns the icon resource for this node.

        :rtype: str
        """

        pass

    def exists(self):
        """
        Method used to check if this weak-reference exists in the scene file.

        :rtype: bool
        """

        return self.fnNode.isValid()

    def select(self):
        """
        Selects the associated node from the scene file.

        :rtype: None
        """

        if self.fnNode.isValid():

            log.info('Selecting %s node.' % self.name)
            self.fnNode.select(replace=False)

        else:

            log.warning('Unable to select %s node!' % self.name)

    def delete(self):
        """
        Deletes this node from the export set.

        :rtype: None
        """

        if self.parent is not None:

            self.parent.children.remove(self)
    # endregion

    # region Callbacks
    def nameChanged(self, oldName, newName):
        """
        Callback to whenever the name of this object changes.

        :type oldName: str
        :type newName: str
        :rtype: None
        """

        self._fnNode.trySetObject(newName)
    # endregion


class FbxSkeleton(FbxNode):
    """
    Overload of FbxNode used to store skeleton properties.
    """

    # region Dunderscores
    __slots__ = (
        '_includeDescendants',
        '_includeJoints',
        '_includeRegex',
        '_excludeJoints',
        '_excludeRegex'
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(FbxSkeleton, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._includeDescendants = kwargs.get('includeDescendants', True)
        self._includeJoints = kwargs.get('includeJoints', [])
        self._includeRegex = kwargs.get('includeRegex', '')
        self._excludeJoints = kwargs.get('excludeJoints', [])
        self._excludeRegex = kwargs.get('excludeRegex', '')
    # endregion

    # region Properties
    @property
    def includeDescendants(self):
        """
        Getter method that returns the include descendants flag.

        :rtype: bool
        """

        return self._includeDescendants

    @includeDescendants.setter
    def includeDescendants(self, includeDescendants):
        """
        Setter method that updates the include descendants flag.

        :type includeDescendants: bool
        :rtype: None
        """

        self._includeDescendants = includeDescendants

    @property
    def includeJoints(self):
        """
        Getter method that returns the include joints for this skeleton.

        :rtype: List[str]
        """

        return self._includeJoints

    @includeJoints.setter
    def includeJoints(self, includeJoints):
        """
        Setter method that updates the include joints for this skeleton.

        :type includeJoints: List[str]
        :rtype: None
        """

        self._includeJoints = includeJoints

    @property
    def includeRegex(self):
        """
        Getter method that returns the include regex pattern for this skeleton.

        :rtype: str
        """

        return self._includeRegex

    @includeRegex.setter
    def includeRegex(self, includeRegex):
        """
        Setter method that updates the include regex pattern for this skeleton.

        :type includeRegex: str
        :rtype: None
        """

        self._includeRegex = includeRegex

    @property
    def excludeJoints(self):
        """
        Getter method that returns the exclude joints for this skeleton.

        :rtype: List[str]
        """

        return self._excludeJoints

    @excludeJoints.setter
    def excludeJoints(self, excludeJoints):
        """
        Setter method that updates the exclude joints for this skeleton.

        :type excludeJoints: List[str]
        :rtype: None
        """

        self._excludeJoints = excludeJoints

    @property
    def excludeRegex(self):
        """
        Getter method that returns the exclude regex pattern for this skeleton.

        :rtype: str
        """

        return self._excludeRegex

    @excludeRegex.setter
    def excludeRegex(self, excludeRegex):
        """
        Setter method that updates the exclude regex pattern for this skeleton.

        :type excludeRegex: str
        :rtype: None
        """

        self._excludeRegex = excludeRegex
    # endregion

    # region Methods
    def icon(self):
        """
        Returns the icon resource for this node.

        :rtype: str
        """

        return ':dcc/icons/skeleton'

    def select(self):
        """
        Selects the associated node from the scene file.

        :rtype: None
        """

        # Call parent method
        #
        super(FbxSkeleton, self).select()

        # Evaluate extended selections
        #
        self.selectIncludeJoints()
        self.selectIncludeRegex()
        self.deselectExcludeJoints()
        self.deselectExcludeRegex()

    def selectIncludeJoints(self):
        """
        Selects the associated nodes from the scene file.

        :rtype: None
        """

        fnNode = fnnode.FnNode()

        for jointName in self.includeJoints:

            success = fnNode.trySetObject(jointName)

            if success:

                fnNode.select(replace=False)

            else:

                log.warning('Unable to include: %s' % jointName)
                continue

    def selectIncludeRegex(self):
        """
        Selects the associated nodes from the scene file.

        :rtype: None
        """

        fnNode = fnnode.FnNode()

        for node in fnNode.iterInstancesByRegex(self.includeRegex):

            fnNode.setObject(node)
            fnNode.select(replace=False)

    def deselectExcludeJoints(self):
        """
        Deselects the associated nodes from the scene file.

        :rtype: None
        """

        fnNode = fnnode.FnNode()

        for jointName in self.excludeJoints:

            success = fnNode.trySetObject(jointName)

            if success:

                fnNode.deselect()

            else:

                log.warning('Unable to exclude: %s' % jointName)
                continue

    def deselectExcludeRegex(self):
        """
        Deselects the associated nodes from the scene file.

        :rtype: None
        """

        fnNode = fnnode.FnNode()

        for node in fnNode.iterInstancesByRegex(self.excludeRegex):

            fnNode.setObject(node)
            fnNode.deselect()

    def acceptsChild(self, obj):
        """
        Evaluates whether the supplied object can be parented to this instance.
        For functionality purposes this has been disabled.
        Please refer to the include/exclude arrays for extending skeleton building.

        :type obj: fbxobject.FbxObject
        :rtype: bool
        """

        return False
    # endregion


class FbxCamera(FbxNode):
    """
    Overload of FbxNode used to store camera properties.
    """

    # region Dunderscores
    __slots__ = ()

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(FbxCamera, self).__init__(*args, **kwargs)
    # endregion

    # region Methods
    def icon(self):
        """
        Returns the icon resource for this node.

        :rtype: str
        """

        return ':dcc/icons/camera.png'

    def acceptsChild(self, obj):
        """
        Evaluates whether the supplied object can be parented to this instance.
        For functionality purposes this has been disabled.

        :type obj: fbxobject.FbxObject
        :rtype: bool
        """

        return False
    # endregion


class FbxMeshComponent(IntEnum):

    Unknown = -1
    Vertex = 0
    Edge = 1
    Polygon = 3


class FbxMesh(FbxNode):
    """
    Overload of FbxNode used to store mesh properties.
    """

    # region Dunderscores
    __slots__ = ('_extract', '_extractType', '_extractElements')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(FbxMesh, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._extract = kwargs.get('extract', False)
        self._extractType = kwargs.get('extractType', FbxMeshComponent.Polygon)
        self._extractElements = kwargs.get('extractElements', [])
    # endregion

    # region Properties
    @property
    def extract(self):
        """
        Getter method that returns the extract flag.

        :rtype: bool
        """

        return self._extract

    @extract.setter
    def extract(self, extract):
        """
        Setter method that updates the extract flag.

        :type extract: bool
        :rtype: None
        """

        self._extract = extract

    @property
    def extractType(self):
        """
        Getter method that returns the extraction type.

        :rtype: FbxMeshComponent
        """

        return self._extractType

    @extractType.setter
    def extractType(self, extractType):
        """
        Setter method that updates the extraction type.

        :type extractType: FbxMeshComponent
        :rtype: None
        """

        self._extractType = extractType

    @property
    def extractElements(self):
        """
        Getter method that returns the mesh extraction elements.

        :rtype: List[int]
        """

        return self._extractElements

    @extractElements.setter
    def extractElements(self, extractElements):
        """
        Setter method that updates the mesh extraction elements.

        :type extractElements: List[int]
        :rtype: None
        """

        self._extractElements = extractElements
    # endregion

    # region Methods
    def icon(self):
        """
        Returns the icon resource for this node.

        :rtype: str
        """

        return ':dcc/icons/mesh.png'

    def acceptsChild(self, obj):
        """
        Evaluates whether the supplied object can be parented to this instance.
        For functionality purposes this has been disabled.

        :type obj: fbxobject.FbxObject
        :rtype: bool
        """

        return False
    # endregion


class FbxMaterialSlot(FbxNode):
    """
    Overload of FbxNode used to store material slot properties.
    """

    # region Dunderscores
    __slots__ = ()

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(FbxMaterialSlot, self).__init__(*args, **kwargs)
    # endregion

    # region Methods
    def slot(self):
        """
        Returns the slot index for this material.
        It's a bit nasty looking but it at least takes into consideration siblings of the same type.

        :rtype: int
        """

        return [x for x in self.parent.children if isinstance(x, FbxMaterialSlot)].index(self)

    def icon(self):
        """
        Returns the icon resource for this node.

        :rtype: str
        """

        return ':dcc/icons/material.png'

    def acceptsChild(self, obj):
        """
        Evaluates whether the supplied object can be parented to this instance.

        :type obj: fbxobject.FbxObject
        :rtype: bool
        """

        return isinstance(obj, FbxMesh)
    # endregion


def createFbxNode(typeName, **kwargs):
    """
    Method used to construct an fbx data wrapper using the supplied type name.
    Additional keyword arguments can be supplied to the class constructor.

    :type typeName: str
    :rtype: FbxNode
    """

    # Locate constructor from module
    #
    cls = globals().get(typeName)

    if cls is None:

        log.warning('Unable to locate fbx type: %s' % typeName)
        return None

    # Construct new instance
    #
    return cls(**kwargs)
