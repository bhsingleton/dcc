import os

from enum import IntEnum
from . import fbxbase, fbxskeleton, fbxmesh, fbxcamera, fbxscript
from ..interop import fbxfile
from ... import fnscene, fnfbx

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxExportStatus(IntEnum):

    Pending = 0
    Pre = 1
    Post = 2
    Complete = 2


class FbxExportSet(fbxbase.FbxBase):
    """
    Overload of FbxObject that outlines fbx export set data.
    """

    # region Dunderscores
    __slots__ = (
        '_scene',
        '_fbx',
        '_asset',
        '_directory',
        '_scale',
        '_moveToOrigin',
        '_removeDisplayLayers',
        '_removeContainers',
        '_skeleton',
        '_mesh',
        '_camera',
        '_customScripts'
    )

    __exporting__ = None
    __status__ = FbxExportStatus.Pending

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Declare private variables
        #
        self._scene = fnscene.FnScene()
        self._fbx = fnfbx.FnFbx()
        self._asset = self.nullWeakReference
        self._directory = kwargs.get('directory', '')
        self._scale = kwargs.get('scale', 1.0)
        self._moveToOrigin = kwargs.get('moveToOrigin', False)
        self._removeDisplayLayers = kwargs.get('removeDisplayLayers', True)
        self._removeContainers = kwargs.get('removeContainers', True)
        self._camera = kwargs.get('camera', fbxcamera.FbxCamera())
        self._skeleton = kwargs.get('skeleton', fbxskeleton.FbxSkeleton())
        self._mesh = kwargs.get('mesh', fbxmesh.FbxMesh())
        self._customScripts = []

        # Call parent method
        #
        super(FbxExportSet, self).__init__(*args, **kwargs)
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
    def fbx(self):
        """
        Getter method that returns the fbx interface.

        :rtype: fnfbx.FnFbx
        """

        return self._fbx

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

        # Check if directory is relative to cwd
        #
        cwd = self.cwd(expandVars=True)

        if self.scene.isPathRelativeTo(directory, cwd):

            directory = self.scene.makePathRelativeTo(directory, cwd)

        self._directory = directory

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
    def removeDisplayLayers(self):
        """
        Getter method that returns the remove display layers flag for this export set.

        :rtype: bool
        """

        return self._removeDisplayLayers

    @removeDisplayLayers.setter
    def removeDisplayLayers(self, removeDisplayLayers):
        """
        Setter method that updates the remove display layers flag for this export set.

        :type removeDisplayLayers: bool
        :rtype: None
        """

        self._removeDisplayLayers = removeDisplayLayers

    @property
    def removeContainers(self):
        """
        Getter method that returns the remove containers flag for this export set.

        :rtype: bool
        """

        return self._removeContainers

    @removeContainers.setter
    def removeContainers(self, removeContainers):
        """
        Setter method that updates the remove containers flag for this export set.

        :type removeContainers: bool
        :rtype: None
        """

        self._removeContainers = removeContainers

    @property
    def camera(self):
        """
        Getter method that returns the camera settings for this export set.

        :rtype: fbxcamera.FbxCamera
        """

        return self._camera

    @camera.setter
    def camera(self, camera):
        """
        Setter method that updates the camera settings for this export set.

        :type camera: fbxcamera.FbxCamera
        :rtype: None
        """

        self._camera = camera

    @property
    def skeleton(self):
        """
        Getter method that returns the skeleton settings for this export set.

        :rtype: fbxskeleton.FbxSkeleton
        """

        return self._skeleton

    @skeleton.setter
    def skeleton(self, skeleton):
        """
        Setter method that updates the skeleton settings for this export set.

        :type skeleton: fbxskeleton.FbxSkeleton
        :rtype: None
        """

        self._skeleton = skeleton

    @property
    def mesh(self):
        """
        Getter method that returns the mesh settings for this export set.

        :rtype: fbxmesh.FbxMesh
        """

        return self._mesh

    @mesh.setter
    def mesh(self, mesh):
        """
        Setter method that updates the mesh settings for this export set.

        :type mesh: fbxmesh.FbxMesh
        :rtype: None
        """

        self._mesh = mesh

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
    # endregion

    # region Methods
    def cwd(self, expandVars=False):
        """
        Returns the current working directory from the parent asset.

        :type expandVars: bool
        :rtype: str
        """

        # Check if asset exists
        #
        if self.asset is None:

            return ''

        # Check if variables should be expanded
        #
        if expandVars:

            return os.path.expandvars(self.asset.directory)

        else:

            return self.asset.directory

    def exportPath(self):
        """
        Returns the export path for this export set.

        :rtype: str
        """

        # Check if asset exists
        #
        fileName = '{name}.fbx'.format(name=self.name)
        path = os.path.join(os.path.expandvars(self.directory), fileName)
        cwd = self.cwd(expandVars=True)

        if not self.scene.isNullOrEmpty(cwd):

            return os.path.join(cwd, path)

        else:

            return path

    def select(self, animationOnly=False, namespace=''):
        """
        Selects the nodes associated with this export set.

        :type animationOnly: bool
        :type namespace: str
        :rtype: None
        """

        # Select skeleton
        #
        self.scene.clearActiveSelection()
        self.skeleton.select(namespace=namespace)

        # Check if meshes should be selected
        #
        if not animationOnly:

            self.mesh.select(namespace=namespace)

        # Select camera
        #
        self.camera.select(namespace=namespace)

    def editExportFile(self, filePath):
        """
        Performs any edits to the associated export file.

        :rtype: None
        """

        # Check if any edits are required
        #
        requiresEdits = any([self.moveToOrigin, self.removeDisplayLayers, self.removeContainers])

        if not requiresEdits or not os.path.exists(filePath):

            return

        # Check if root nodes should be moved to origin
        #
        fbxFile = fbxfile.FbxFile(filePath)

        if self.moveToOrigin:

            fbxFile.moveToOrigin()

        # Check if display layers should be removed
        #
        if self.removeDisplayLayers:

            fbxFile.removeDisplayLayers()

        # Check if containers should be removed
        #
        if self.removeContainers:

            fbxFile.removeContainers()

        # Commit changes to file
        #
        fbxFile.save()

    def preExport(self):
        """
        Executes any pre-export scripts.

        :rtype: None
        """

        # Update export status
        #
        self.updateExportStatus(FbxExportStatus.Pre, self)

        # Execute pre-scripts
        #
        for customScript in self.customScripts:

            customScript.preExport()

    def export(self, namespace=''):
        """
        Outputs this export set to the user defined path.

        :type namespace: str
        :rtype: None
        """

        # Select nodes and execute pre-scripts
        #
        self.select(namespace=namespace)
        self.preExport()

        # Export fbx using selection
        #
        self.fbx.setMeshExportParams(
            version=self.asset.fileVersion,
            asAscii=bool(self.asset.fileType),
            scale=self.scale,
            includeNormals=self.mesh.includeNormals,
            includeSmoothings=self.mesh.includeSmoothings,
            includeTangentsAndBinormals=self.mesh.includeTangentsAndBinormals,
            includeSkins=self.mesh.includeSkins,
            includeBlendshapes=self.mesh.includeBlendshapes
        )

        exportPath = self.exportPath()
        self.fbx.exportSelection(exportPath)

        # Execute post-scripts
        #
        self.editExportFile(exportPath)
        self.postExport()

    def exportAnimation(self, sequence, namespace=''):
        """
        Outputs the supplied sequence to the user defined path.

        :type sequence: fbxsequence.FbxSequence
        :type namespace: str
        :rtype: None
        """

        # Select nodes and execute pre-scripts
        #
        self.select(animationOnly=True, namespace=namespace)
        self.preExport()

        # Export fbx using selection
        #
        self.fbx.setAnimExportParams(
            version=self.asset.fileVersion,
            asAscii=bool(self.asset.fileType),
            scale=self.scale,
            startFrame=sequence.startFrame,
            endFrame=sequence.endFrame,
            step=sequence.step,
        )

        exportPath = sequence.exportPath()
        self.fbx.exportSelection(exportPath)

        # Execute post-scripts
        #
        self.editExportFile(exportPath)
        self.postExport()

    def postExport(self):
        """
        Executes any post-export scripts.

        :rtype: None
        """

        # Update export status
        #
        self.updateExportStatus(FbxExportStatus.Post, self)

        # Execute post-scripts
        #
        for customScript in self.customScripts:

            customScript.postExport()

        # Clear export status
        #
        self.updateExportStatus(FbxExportStatus.Pending, None)

    @classmethod
    def getExportStatus(cls):
        """
        Returns the export set that is currently exporting.

        :rtype: Tuple[FbxExportStatus, FbxExportSet]
        """

        return cls.__status__, cls.__exporting__

    @classmethod
    def updateExportStatus(cls, status, exportSet):
        """
        Returns the export set that is currently exporting.

        :type status: FbxExportStatus
        :type exportSet: Union[FbxExportSet, None]
        :rtype: None
        """

        cls.__status__, cls.__exporting__ = status, exportSet
    # endregion
