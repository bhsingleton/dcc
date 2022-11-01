import os

from enum import Enum, IntEnum
from . import fbxbase, fbxserializer
from ... import fnfbx, fnscene
from ...python import stringutils
from ...ui import qdirectoryedit, qtimespinbox

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxSequence(fbxbase.FbxBase):
    """
    Overload of FbxBase that outlines fbx sequence data.
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
        '_exportSetId'
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Declare private variables
        #
        self._scene = fnscene.FnScene()
        self._fbx = fnfbx.FnFbx()
        self._sequencer = self.nullWeakReference
        self._directory = kwargs.get('directory', '')
        self._startFrame = kwargs.get('startFrame', 0)
        self._endFrame = kwargs.get('endFrame', 1)
        self._step = kwargs.get('step', 1)
        self._useTimeline = kwargs.get('useTimeline', True)
        self._exportSetId = kwargs.get('exportSetId', 0)

        # Call parent method
        #
        super(FbxSequence, self).__init__(*args, **kwargs)
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
        Getter method that returns the directory for this sequence.

        :rtype: str
        """

        return self._directory

    @directory.setter
    def directory(self, directory):
        """
        Setter method that updates the directory for this sequence.

        :type directory: str
        :rtype: None
        """

        self._directory = directory

    @property
    def startFrame(self):
        """
        Getter method that returns the start frame for this sequence.

        :rtype: int
        """

        return self._startFrame

    @startFrame.setter
    def startFrame(self, startFrame):
        """
        Setter method that updates the start frame for this sequence.

        :type startFrame: int
        :rtype: None
        """

        self._startFrame = startFrame

    @property
    def endFrame(self):
        """
        Getter method that returns the end frame for this sequence.

        :rtype: int
        """

        return self._endFrame

    @endFrame.setter
    def endFrame(self, endFrame):
        """
        Setter method that updates the end frame for this sequence.

        :type endFrame: int
        :rtype: None
        """

        self._endFrame = endFrame

    @property
    def step(self):
        """
        Getter method that returns the frame step for this sequence.

        :rtype: int
        """

        return self._step

    @step.setter
    def step(self, step):
        """
        Setter method that updates the frame step for this sequence.

        :type step: int
        :rtype: None
        """

        self._step = step

    @property
    def useTimeline(self):
        """
        Getter method that returns the timeline flag for this sequence.

        :rtype: bool
        """

        return self._useTimeline

    @useTimeline.setter
    def useTimeline(self, useTimeline):
        """
        Setter method that updates the timeline flag for this sequence.

        :type useTimeline: bool
        :rtype: None
        """

        self._useTimeline = useTimeline

    @property
    def exportSetId(self):
        """
        Getter method that returns the export set ID for this sequence.

        :rtype: int
        """

        return self._exportSetId

    @exportSetId.setter
    def exportSetId(self, exportSetId):
        """
        Setter method that updates the export set ID for this sequence.

        :type exportSetId: int
        :rtype: None
        """

        self._exportSetId = exportSetId
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

            return qtimespinbox.QTimeSpinBox(defaultType=qtimespinbox.DefaultType.StartTime, parent=parent)

        elif name == 'endFrame':

            return qtimespinbox.QTimeSpinBox(defaultType=qtimespinbox.DefaultType.EndTime, parent=parent)

        else:

            return super(FbxSequence, cls).createEditor(name, parent=parent)

    def isValid(self):
        """
        Evaluates if this sequence is valid.

        :rtype: bool
        """

        return self.exportSet() is not None

    def timeRange(self):
        """
        Returns the time range for this sequence.

        :rtype: Tuple[int, int]
        """

        if self.useTimeline:

            return self.scene.getStartTime(), self.scene.getEndTime()

        else:

            return self.startFrame, self.endFrame

    def asset(self):
        """
        Returns the asset associated with this sequence.

        :rtype: fbxasset.FbxAsset
        """

        if self.sequencer is not None:

            return self.sequencer.asset

        else:

            return None

    def cwd(self):
        """
        Returns the current working directory from the parent asset.

        :rtype: str
        """

        # Check if asset exists
        #
        asset = self.asset()

        if asset is not None:

            return asset.directory

        else:

            return ''

    def exportPath(self):
        """
        Returns the export path for this export set.

        :rtype: str
        """

        # Check if asset exists
        #
        fileName = '{name}.fbx'.format(name=self.name)
        path = os.path.join(os.path.expandvars(self.directory), fileName)
        cwd = self.cwd()

        if not stringutils.isNullOrEmpty(cwd):

            return os.path.join(os.path.expandvars(cwd), path)

        else:

            return path

    def exportSet(self):
        """
        Returns the export set associated with this sequence.

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

    def legacyExport(self):
        """
        Exports this sequences to the user defined path using the legacy serializer.

        :rtype: bool
        """

        # Check if sequence is valid
        #
        if not self.isValid():

            log.error(f'Cannot locate export set from "{self.name}" sequence!')
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
        success = self.fbx.exportSelection(exportPath)

        # Execute post-scripts
        #
        exportSet.editExportFile(exportPath)
        exportSet.postExport()

        return success

    def customExport(self):
        """
        Exports this sequences to the user defined path using the custom serializer.

        :rtype: bool
        """

        # Check if sequence is valid
        #
        if not self.isValid():

            log.error(f'Cannot locate export set from "{self.name}" sequence!')
            return False

        # Serialize this sequence
        #
        namespace = self.sequencer.namespace()
        serializer = fbxserializer.FbxSerializer(namespace=namespace)

        return serializer.serializeSequence(self)

    def export(self):
        """
        Exports this sequences to the user defined path.

        :rtype: bool
        """

        # Check if sequence is valid
        #
        if not self.isValid():

            log.error(f'Cannot locate export set from "{self.name}" sequence!')
            return False

        # Check if legacy serializer should be used
        #
        asset = self.asset()

        if asset.useLegacySerializer:

            return self.legacyExport()

        else:

            return self.customExport()

    def refresh(self):
        """
        Updates the return type for the export set ID property.
        This allows the QPSONItemModel to display a list of valid export sets.

        :rtype: None
        """

        # Check if asset exists
        #
        asset = self.asset()

        if asset is None:

            return

        # Update return type
        #
        names = [exportSet.name for exportSet in asset.exportSets]
        options = {name: index for (index, name) in enumerate(names)}
        enum = Enum('ExportSetIds', options, type=IntEnum)

        self.__class__.exportSetId.fget.__annotations__['return'] = enum
    # endregion
