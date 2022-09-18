from . import fbxbase, FbxMeshComponent
from ... import fnscene, fnnode
from ...generators.uniquify import uniquify

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxMesh(fbxbase.FbxBase):
    """
    Overload of FbxBase used to store mesh properties.
    """

    # region Dunderscores
    __slots__ = (
        '_scene',
        '_includeNodes',
        '_includeLayers',
        '_includeSelectionSets',
        '_includeNormals',
        '_includeTangentsAndBinormals',
        '_includeSmoothings',
        '_includeColorSets',
        '_includeSkins',
        '_includeBlendshapes',
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Declare private variables
        #
        self._scene = fnscene.FnScene()
        self._includeNodes = kwargs.get('nodes', [])
        self._includeLayers = kwargs.get('layers', [])
        self._includeSelectionSets = kwargs.get('selectionSets', [])
        self._includeNormals = kwargs.get('includeNormals', True)
        self._includeTangentsAndBinormals = kwargs.get('includeTangentsAndBinormals', True)
        self._includeSmoothings = kwargs.get('includeSmoothings', True)
        self._includeColorSets = kwargs.get('includeColorSets', False)
        self._includeSkins = kwargs.get('includeSkins', False)
        self._includeBlendshapes = kwargs.get('includeBlendshapes', False)

        # Call parent method
        #
        super(FbxMesh, self).__init__(*args, **kwargs)
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
    def includeNodes(self):
        """
        Getter method that returns the list of nodes to be included.

        :rtype: List[str]
        """

        return self._includeNodes

    @includeNodes.setter
    def includeNodes(self, includeNodes):
        """
        Setter method that updates the list of nodes to be included.

        :type includeNodes: List[str]
        :rtype: None
        """

        self._includeNodes.clear()
        self._includeNodes.extend(includeNodes)

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
    def includeNormals(self):
        """
        Getter method that returns the normals flag for this export set.

        :rtype: bool
        """

        return self._includeNormals

    @includeNormals.setter
    def includeNormals(self, includeNormals):
        """
        Setter method that updates the normals flag for this export set.

        :type includeNormals: bool
        :rtype: None
        """

        self._includeNormals = includeNormals

    @property
    def includeTangentsAndBinormals(self):
        """
        Getter method that returns the tangents and binormals flag for this export set.

        :rtype: bool
        """

        return self._includeTangentsAndBinormals

    @includeTangentsAndBinormals.setter
    def includeTangentsAndBinormals(self, includeTangentsAndBinormals):
        """
        Setter method that updates the tangents and binormals flag for this export set.

        :type includeTangentsAndBinormals: bool
        :rtype: None
        """

        self._includeTangentsAndBinormals = includeTangentsAndBinormals

    @property
    def includeSmoothings(self):
        """
        Getter method that returns the smoothings flag for this export set.

        :rtype: bool
        """

        return self._includeSmoothings

    @includeSmoothings.setter
    def includeSmoothings(self, includeSmoothings):
        """
        Setter method that updates the smoothings flag for this export set.

        :type includeSmoothings: bool
        :rtype: None
        """

        self._includeSmoothings = includeSmoothings

    @property
    def includeColorSets(self):
        """
        Getter method that returns the color sets flag for this export set.

        :rtype: bool
        """

        return self._includeColorSets

    @includeColorSets.setter
    def includeColorSets(self, includeColorSets):
        """
        Setter method that updates the color sets flag for this export set.

        :type includeColorSets: bool
        :rtype: None
        """

        self._includeColorSets = includeColorSets

    @property
    def includeSkins(self):
        """
        Getter method that returns the skins flag for this export set.

        :rtype: bool
        """

        return self._includeSkins

    @includeSkins.setter
    def includeSkins(self, includeSkins):
        """
        Setter method that updates the skins flag for this export set.

        :type includeSkins: bool
        :rtype: None
        """

        self._includeSkins = includeSkins

    @property
    def includeBlendshapes(self):
        """
        Getter method that returns the blend shapes flag for this export set.

        :rtype: bool
        """

        return self._includeBlendshapes

    @includeBlendshapes.setter
    def includeBlendshapes(self, includeBlendshapes):
        """
        Setter method that updates the blend shapes flag for this export set.

        :type includeBlendshapes: bool
        :rtype: None
        """

        self._includeBlendshapes = includeBlendshapes
    # endregion

    # region Methods
    def iterIncludeMeshes(self, namespace=''):
        """
        Returns a generator that yields meshes that should be included.

        :type namespace: str
        :rtype: Iterator[Any]
        """

        # Get meshes from collections
        #
        root = self.iterNodesFromNames(self.name, namespace=namespace)
        includeNodes = self.iterNodesFromNames(*self.includeNodes, namespace=namespace)
        includeLayers = self.iterNodesFromLayers(*self.includeLayers, namespace=namespace)
        includeSelectionSets = self.iterNodesFromSelectionSets(*self.includeSelectionSets, namespace=namespace)

        return uniquify(root, includeNodes, includeLayers, includeSelectionSets)

    def getMeshes(self, namespace=''):
        """
        Returns a list of nodes from this mesh.

        :type namespace: str
        :rtype: List[Any]
        """

        return list(self.iterIncludeMeshes(namespace=namespace))

    def select(self, namespace=''):
        """
        Selects the associated node from the scene file.

        :type namespace: str
        :rtype: None
        """

        meshes = self.getMeshes(namespace=namespace)
        self.scene.setActiveSelection(meshes, replace=False)
    # endregion

