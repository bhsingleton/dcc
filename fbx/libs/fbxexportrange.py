import os

from enum import Enum, IntEnum
from . import fbxbase, fbxscript, fbxserializer
from ... import fnfbx, fnscene
from ...python import stringutils
from ...ui import qdirectoryedit, qtimespinbox
from ...perforce import p4utils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxExportRange(fbxbase.FbxBase):
    """
    Overload of `FbxBase` that implements FBX export-range data.
    """

    # region Dunderscores
    __slots__ = (
        '_scene',
        '_fbx',
        '_sequencer',
        '_directory',
        '_startFrame',
        '_endFrame',
        '_step',
        '_useTimeline',
        '_moveToOrigin',
        '_exportSetId',
        '_customScripts'
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(FbxExportRange, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._scene = fnscene.FnScene()
        self._fbx = fnfbx.FnFbx()
        self._sequencer = self.nullWeakReference
        self._directory = ''
        self._startFrame = 0
        self._endFrame = 1
        self._step = 1
        self._useTimeline = True
        self._moveToOrigin = False
        self._exportSetId = 0
        self._customScripts = []
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
    def sequencer(self):
        """
        Getter method that returns the associated sequencer.

        :rtype: fbxsequencer.FbxSequencer
        """

        return self._sequencer()

    @property
    def directory(self):
        """
        Getter method that returns the export directory.

        :rtype: str
        """

        return self._directory

    @directory.setter
    def directory(self, directory):
        """
        Setter method that updates the export directory.

        :type directory: str
        :rtype: None
        """

        # Check if directory is relative to cwd
        #
        cwd = self.cwd(expandVars=True)

        if self.scene.isPathAbsolute(directory) and self.scene.isPathRelativeTo(directory, cwd):

            directory = self.scene.makePathRelativeTo(directory, cwd)

        self._directory = directory

    @property
    def startFrame(self):
        """
        Getter method that returns the start frame.

        :rtype: int
        """

        return self._startFrame

    @startFrame.setter
    def startFrame(self, startFrame):
        """
        Setter method that updates the start frame.

        :type startFrame: int
        :rtype: None
        """

        self._startFrame = startFrame

    @property
    def endFrame(self):
        """
        Getter method that returns the end frame.

        :rtype: int
        """

        return self._endFrame

    @endFrame.setter
    def endFrame(self, endFrame):
        """
        Setter method that updates the end frame.

        :type endFrame: int
        :rtype: None
        """

        self._endFrame = endFrame

    @property
    def step(self):
        """
        Getter method that returns the frame step.

        :rtype: float
        """

        return self._step

    @step.setter
    def step(self, step):
        """
        Setter method that updates the frame step.

        :type step: float
        :rtype: None
        """

        if isinstance(step, int):

            self._step = step

        elif isinstance(step, float):

            quotient, remainder = divmod(step, 1)
            self._step = int(quotient) if (remainder == 0.0) else step

        else:

            raise TypeError(f'step.setter() expects a number ({type(step).__name__} given)!')

    @property
    def useTimeline(self):
        """
        Getter method that returns the `useTimeline` flag.

        :rtype: bool
        """

        return self._useTimeline

    @useTimeline.setter
    def useTimeline(self, useTimeline):
        """
        Setter method that updates the `useTimeline` flag.

        :type useTimeline: bool
        :rtype: None
        """

        self._useTimeline = useTimeline

    @property
    def moveToOrigin(self):
        """
        Getter method that returns the `moveToOrigin` flag.

        :rtype: bool
        """

        return self._moveToOrigin

    @moveToOrigin.setter
    def moveToOrigin(self, moveToOrigin):
        """
        Setter method that updates the `moveToOrigin` flag.

        :type moveToOrigin: bool
        :rtype: None
        """

        self._moveToOrigin = moveToOrigin

    @property
    def exportSetId(self):
        """
        Getter method that returns the export set ID.

        :rtype: int
        """

        return self._exportSetId

    @exportSetId.setter
    def exportSetId(self, exportSetId):
        """
        Setter method that updates the export set ID.

        :type exportSetId: int
        :rtype: None
        """

        self._exportSetId = exportSetId

    @property
    def customScripts(self):
        """
        Getter method that returns the custom scripts.

        :rtype: List[fbxscript.FbxScript]
        """

        return self._customScripts

    @customScripts.setter
    def customScripts(self, customScripts):
        """
        Setter method that updates the custom scripts.

        :type customScripts: List[fbxscript.FbxScript]
        :rtype: None
        """

        self._customScripts = customScripts
    # endregion

    # region Methods
    @classmethod
    def createEditor(cls, name, parent=None):
        """
        Returns a Qt editor for the specified property.

        :type name: str
        :type parent: Union[QtWidgets.QWidget, None]
        :rtype: Union[QtWidgets.QWidget, None]
        """

        if name == 'directory':

            return qdirectoryedit.QDirectoryEdit(parent=parent)

        elif name == 'startFrame':

            return qtimespinbox.QTimeSpinBox(defaultType=qtimespinbox.DefaultType.START_TIME, parent=parent)

        elif name == 'endFrame':

            return qtimespinbox.QTimeSpinBox(defaultType=qtimespinbox.DefaultType.END_TIME, parent=parent)

        else:

            return super(FbxExportRange, cls).createEditor(name, parent=parent)

    def isValid(self):
        """
        Evaluates if this export range is valid.

        :rtype: bool
        """

        return self.exportSet() is not None

    def timeRange(self):
        """
        Returns the time range.

        :rtype: Tuple[int, int]
        """

        if self.useTimeline:

            return self.scene.getStartTime(), self.scene.getEndTime()

        else:

            return self.startFrame, self.endFrame

    def asset(self):
        """
        Returns the asset associated with this export range.

        :rtype: fbxasset.FbxAsset
        """

        if self.sequencer is not None:

            return self.sequencer.asset

        else:

            return None

    def cwd(self, expandVars=False):
        """
        Returns the current working directory from the parent asset.

        :type expandVars: bool
        :rtype: str
        """

        # Check if asset exists
        #
        asset = self.asset()

        if asset is None:

            return ''

        # Check if variables should be expanded
        #
        if expandVars:

            return os.path.expandvars(asset.directory)

        else:

            return asset.directory

    def exportPath(self):
        """
        Returns the export path for this export set.

        :rtype: str
        """

        # Check if CWD exists
        #
        fileName = '{name}.fbx'.format(name=self.name)
        path = os.path.join(self.directory, fileName)
        cwd = self.cwd(expandVars=True)

        if not stringutils.isNullOrEmpty(cwd) and self.scene.isPathRelative(path):

            return os.path.normpath(os.path.join(cwd, path))

        else:

            return os.path.normpath(path)

    def exportSet(self):
        """
        Returns the export set associated with this export range.

        :rtype: fbxexportset.FbxExportSet
        """

        # Check if asset is valid
        #
        asset = self.asset()

        if asset is None:

            return None

        # Check if export set is in range
        #
        numExportSets = len(asset.exportSets)

        if 0 <= self.exportSetId < numExportSets:

            return asset.exportSets[self.exportSetId]

        else:

            return None

    def builtinExport(self):
        """
        Exports this range using the builtin serializer.

        :rtype: str
        """

        # Check if export range is valid
        #
        if not self.isValid():

            log.error(f'Cannot find asset associated with "{self.name}" range!')
            return False

        # Select nodes and execute pre-scripts
        #
        asset = self.asset()
        exportSet = self.exportSet()
        namespace = self.sequencer.namespace()

        exportSet.select(animationOnly=True, namespace=namespace)
        exportSet.preExport()

        # Export fbx using selection
        #
        self.fbx.setAnimExportParams(
            version=asset.fileVersion,
            asAscii=bool(asset.fileType),
            scale=exportSet.scale,
            startFrame=self.startFrame,
            endFrame=self.endFrame,
            step=self.step,
        )

        exportPath = self.exportPath()
        self.scene.ensureDirectory(exportPath)
        self.scene.ensureWritable(exportPath)

        success = self.fbx.exportSelection(exportPath)

        if not success:

            log.warning(f'Unable to export FBX: {exportPath}')
            return ''

        # Execute post-scripts
        #
        exportSet.editExportFile(exportPath)
        exportSet.postExport()

        return exportPath

    def customExport(self):
        """
        Exports this range using a custom serializer.

        :rtype: str
        """

        # Check if export range is valid
        #
        if not self.isValid():

            log.error(f'Cannot find asset associated with "{self.name}" range!')
            return False

        # Serialize this export range
        #
        namespace = self.sequencer.namespace()
        serializer = fbxserializer.FbxSerializer(namespace=namespace)
        asAscii = bool(self.asset().fileType)

        return serializer.serializeExportRange(self, asAscii=asAscii)

    def export(self, checkout=False):
        """
        Exports this range to the user defined path.

        :type checkout: bool
        :rtype: str
        """

        # Check if export range is valid
        #
        if not self.isValid():

            log.error(f'Cannot find asset associated with "{self.name}" range!')
            return False

        # Check which serializer to use
        # Don't forget to ensure all child references are loaded before serializing!
        #
        asset = self.asset()
        self.sequencer.reference.ensureLoaded()

        if asset.useBuiltinSerializer:

            exportPath = self.builtinExport()

        else:

            exportPath = self.customExport()

        # Check if file requires adding
        #
        isValidPath = not stringutils.isNullOrEmpty(exportPath)
        hasPerforce = p4utils.isInstalled()
        
        if isValidPath and (checkout and hasPerforce):

            p4utils.smartCheckout(exportPath)

        return exportPath

    def refresh(self):
        """
        Updates the return type for the export set ID property.
        This allows the `QPSONItemModel` to display a list of valid export sets.

        :rtype: None
        """

        # Check if asset exists
        #
        asset = self.asset()

        if asset is not None:

            # Update return type
            #
            names = [exportSet.name for exportSet in asset.exportSets]
            options = {name: index for (index, name) in enumerate(names)}
            enum = Enum('ExportSetIds', options, type=IntEnum)

            self.__class__.exportSetId.fget.__annotations__['return'] = enum

        else:

            # Reset return type
            #
            self.__class__.exportSetId.fget.__annotations__['return'] = int
    # endregion
