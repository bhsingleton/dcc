from . import fbxbase
from ... import fnscene, fnnode
from ...generators.uniquify import uniquify

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxSkeleton(fbxbase.FbxBase):
    """
    Overload of FbxBase used to store skeleton properties.
    """

    # region Dunderscores
    __slots__ = (
        '_scene',
        '_includeDescendants',
        '_includeJoints',
        '_includeLayers',
        '_includeSelectionSets',
        '_includeRegex',
        '_excludeJoints',
        '_excludeLayers',
        '_excludeSelectionSets',
        '_excludeRegex'
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Declare private variables
        #
        self._scene = fnscene.FnScene()
        self._includeDescendants = kwargs.get('includeDescendants', True)
        self._includeJoints = kwargs.get('includeJoints', [])
        self._includeLayers = kwargs.get('includeLayers', [])
        self._includeSelectionSets = kwargs.get('includeSelectionSets', [])
        self._includeRegex = kwargs.get('includeRegex', '')
        self._excludeJoints = kwargs.get('excludeJoints', [])
        self._excludeLayers = kwargs.get('excludeLayers', [])
        self._excludeSelectionSets = kwargs.get('excludeSelectionSets', [])
        self._excludeRegex = kwargs.get('excludeRegex', '')

        # Call parent method
        #
        super(FbxSkeleton, self).__init__(*args, **kwargs)
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
    def includeDescendants(self):
        """
        Getter method that returns the include-descendants flag.

        :rtype: bool
        """

        return self._includeDescendants

    @includeDescendants.setter
    def includeDescendants(self, includeDescendants):
        """
        Setter method that updates the include-descendants flag.

        :type includeDescendants: bool
        :rtype: None
        """

        self._includeDescendants = includeDescendants

    @property
    def includeJoints(self):
        """
        Getter method that returns the list of joints to be included.

        :rtype: List[str]
        """

        return self._includeJoints

    @includeJoints.setter
    def includeJoints(self, includeJoints):
        """
        Setter method that updates the list of joints to be included.

        :type includeJoints: List[str]
        :rtype: None
        """

        self._includeJoints.clear()
        self._includeJoints.extend(includeJoints)

    @property
    def includeLayers(self):
        """
        Getter method that returns the list of layers to be included.

        :rtype: List[str]
        """

        return self._includeLayers

    @includeLayers.setter
    def includeLayers(self, includeLayers):
        """
        Setter method that updates the list of layers to be included.

        :type includeLayers: List[str]
        :rtype: None
        """

        self._includeLayers.clear()
        self._includeLayers.extend(includeLayers)

    @property
    def includeSelectionSets(self):
        """
        Getter method that returns the list of layers to be included.

        :rtype: List[str]
        """

        return self._includeSelectionSets

    @includeSelectionSets.setter
    def includeSelectionSets(self, includeSelectionSets):
        """
        Setter method that updates the list of layers to be included.

        :type includeSelectionSets: List[str]
        :rtype: None
        """

        self._includeSelectionSets.clear()
        self._includeSelectionSets.extend(includeSelectionSets)

    @property
    def includeRegex(self):
        """
        Getter method that returns the regex pattern for including joints.

        :rtype: str
        """

        return self._includeRegex

    @includeRegex.setter
    def includeRegex(self, includeRegex):
        """
        Setter method that updates the regex pattern for including joints.

        :type includeRegex: str
        :rtype: None
        """

        self._includeRegex = includeRegex
    
    @property
    def excludeJoints(self):
        """
        Getter method that returns the list of joints to be excluded.

        :rtype: List[str]
        """

        return self._excludeJoints

    @excludeJoints.setter
    def excludeJoints(self, excludeJoints):
        """
        Setter method that updates the list of joints to be excluded.

        :type excludeJoints: List[str]
        :rtype: None
        """

        self._excludeJoints.clear()
        self._excludeJoints.extend(excludeJoints)

    @property
    def excludeLayers(self):
        """
        Getter method that returns the list of layers to be excluded.

        :rtype: List[str]
        """

        return self._excludeLayers

    @excludeLayers.setter
    def excludeLayers(self, excludeLayers):
        """
        Setter method that updates the list of layers to be excluded.

        :type excludeLayers: List[str]
        :rtype: None
        """

        self._excludeLayers.clear()
        self._excludeLayers.extend(excludeLayers)

    @property
    def excludeSelectionSets(self):
        """
        Getter method that returns the list of layers to be excluded.

        :rtype: List[str]
        """

        return self._excludeSelectionSets

    @excludeSelectionSets.setter
    def excludeSelectionSets(self, excludeSelectionSets):
        """
        Setter method that updates the list of layers to be excluded.

        :type excludeSelectionSets: List[str]
        :rtype: None
        """

        self._excludeSelectionSets.clear()
        self._excludeSelectionSets.extend(excludeSelectionSets)

    @property
    def excludeRegex(self):
        """
        Getter method that returns the regex pattern for including joints.

        :rtype: str
        """

        return self._excludeRegex

    @excludeRegex.setter
    def excludeRegex(self, excludeRegex):
        """
        Setter method that updates the regex pattern for including joints.

        :type excludeRegex: str
        :rtype: None
        """

        self._excludeRegex = excludeRegex
    # endregion

    # region Methods
    def iterIncludeJoints(self, namespace=''):
        """
        Returns a generator that yields joints that should be included.

        :type namespace: str
        :rtype: Iterator[Any]
        """

        # Get root joint
        #
        root = self.iterNodesFromNames(self.name, namespace=namespace)
        descendants = []

        if self.includeDescendants:

            descendants = self.iterDescendantsFromName(self.name, namespace=namespace)

        # Get joints from sets
        #
        includeJoints = self.iterNodesFromNames(*self.includeJoints, namespace=namespace)
        includeLayers = self.iterNodesFromLayers(*self.includeLayers, namespace=namespace)
        includeSelectionSets = self.iterNodesFromSelectionSets(*self.includeSelectionSets, namespace=namespace)
        includeRegex = self.iterNodesFromRegex(self.includeRegex, namespace=namespace)

        return uniquify(root, descendants, includeJoints, includeLayers, includeSelectionSets, includeRegex)

    def iterExcludeJoints(self, namespace=''):
        """
        Returns a generator that yields joints that should be excluded.

        :type namespace: str
        :rtype: Iterator[Any]
        """

        return self.iterNodesFromLayers(*self.excludeJoints, namespace=namespace)

    def getJoints(self, namespace=''):
        """
        Returns a list of joints from this skeleton.

        :type namespace: str
        :rtype: List[Any]
        """

        includeJoints = list(self.iterIncludeJoints(namespace=namespace))
        excludeJoints = list(self.iterExcludeJoints(namespace=namespace))

        return [joint for joint in includeJoints if joint not in excludeJoints]

    def select(self, namespace=''):
        """
        Selects the associated nodes from the scene file.

        :type namespace: str
        :rtype: None
        """

        joints = self.getJoints(namespace=namespace)
        self.scene.setActiveSelection(joints, replace=False)
    # endregion
