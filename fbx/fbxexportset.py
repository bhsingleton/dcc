import os

from . import fbxbase, fbxskeleton, fbxmesh, fbxscript
from dcc import fnfbx, fnnode

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxExportSet(fbxbase.FbxBase):
    """
    Overload of FbxObject that outlines fbx export set data.
    """

    # region Dunderscores
    __slots__ = (
        '_asset',
        '_directory',
        '_skeleton',
        '_meshes',
        '_customScripts',
        '_scale',
        '_moveToOrigin',
        '_includeNormals',
        '_includeTangentsAndBinormals',
        '_includeSmoothings',
        '_includeColorSets',
        '_includeSkins',
        '_includeBlendshapes'
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Declare private variables
        #
        self._asset = self.nullWeakReference
        self._directory = kwargs.get('directory', '')
        self._skeleton = kwargs.get('skeleton', fbxskeleton.FbxSkeleton())
        self._meshes = []
        self._customScripts = []
        self._scale = kwargs.get('scale', 1.0)
        self._moveToOrigin = kwargs.get('moveToOrigin', False)
        self._includeNormals = kwargs.get('includeNormals', True)
        self._includeTangentsAndBinormals = kwargs.get('includeTangentsAndBinormals', True)
        self._includeSmoothings = kwargs.get('includeSmoothings', True)
        self._includeColorSets = kwargs.get('includeColorSets', False)
        self._includeSkins = kwargs.get('includeSkins', False)
        self._includeBlendshapes = kwargs.get('includeBlendshapes', False)

        # Call parent method
        #
        super(FbxExportSet, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def asset(self):
        """
        Getter method that returns the asset associated with this export set.

        :rtype: fbxasset.FbxAsset
        """

        return self._asset()

    @property
    def directory(self):
        """
        Getter method that returns the directory for this export set.

        :rtype: str
        """

        return self._directory

    @directory.setter
    def directory(self, directory):
        """
        Setter method that updates the directory for this export set.

        :type directory: str
        :rtype: None
        """

        self._directory = directory

    @property
    def skeleton(self):
        """
        Getter method that returns the skeleton for this export set.

        :rtype: fbxskeleton.FbxSkeleton
        """

        return self._meshes

    @skeleton.setter
    def skeleton(self, skeleton):
        """
        Setter method that updates the skeleton for this export set.

        :type skeleton: fbxskeleton.FbxSkeleton
        :rtype: None
        """

        self._skeleton = skeleton

    @property
    def meshes(self):
        """
        Getter method that returns the meshes for this export set.

        :rtype: List[fbxmesh.FbxMesh]
        """

        return self._meshes

    @meshes.setter
    def meshes(self, meshes):
        """
        Setter method that updates the meshes for this export set.

        :type meshes: List[fbxmesh.FbxMesh]
        :rtype: None
        """

        self._meshes = meshes

    @property
    def customScripts(self):
        """
        Getter method that returns the custom scripts for this export set.

        :rtype: List[fbxscript.FbxScript]
        """

        return self._customScripts

    @customScripts.setter
    def customScripts(self, customScripts):
        """
        Setter method that updates the custom scripts for this export set.

        :type customScripts: List[fbxscript.FbxScript]
        :rtype: None
        """

        self._customScripts = customScripts

    @property
    def scale(self):
        """
        Getter method that returns the scale for this export set.

        :rtype: float
        """

        return self._scale

    @scale.setter
    def scale(self, scale):
        """
        Setter method that updates the scale for this export set.

        :type scale: float
        :rtype: None
        """

        self._scale = scale

    @property
    def moveToOrigin(self):
        """
        Getter method that returns the move to origin flag for this export set.

        :rtype: bool
        """

        return self._moveToOrigin

    @moveToOrigin.setter
    def moveToOrigin(self, moveToOrigin):
        """
        Setter method that updates the move to origin flag for this export set.

        :type moveToOrigin: bool
        :rtype: None
        """

        self._moveToOrigin = moveToOrigin

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
    def selectNodes(self):
        """
        Serializes the contents of this export set.

        :rtype: fbxfactory.FbxFactory
        """

        self.skeleton.select()

        for mesh in self.meshes:

            pass

    def exportPath(self):
        """
        Returns the export path for this export set.

        :rtype: str
        """

        return os.path.join(
            os.path.expandvars(self.asset.directory),
            self.directory,
            '{name}.fbx'.format(name=self.name)
        )

    def preExport(self):
        """
        Executes any pre-export scripts.

        :rtype: None
        """

        # Execute pre-scripts
        #
        for customScript in self.customScripts:

            customScript.preExport()

    def export(self):
        """
        Outputs this export set to the user defined path.

        :rtype: bool
        """

        # Select nodes and execute pre-scripts
        #
        self.selectNodes()
        self.preExport()

        # Export fbx using selection
        #
        fnFbx = fnfbx.FnFbx()
        fnFbx.setMeshExportParams(**self)
        fnFbx.exportSelection(self.exportPath())

        # Execute post-scripts
        #
        self.postExport()

    def postExport(self):
        """
        Executes any post-export scripts.
        """

        # Execute post-scripts
        #
        for customScript in self.customScripts:

            customScript.postExport()
    # endregion
