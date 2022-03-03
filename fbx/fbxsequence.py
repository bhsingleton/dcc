import os

from dcc.fbx import fbxexportset, fbxbase
from dcc import fnfbx

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
        '_asset',
        '_directory',
        '_startFrame',
        '_endFrame',
        '_step',
        '_frameRate',
        '_exportSetId'
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(FbxSequence, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._asset = self.nullWeakReference
        self._directory = kwargs.get('directory', '')
        self._startFrame = kwargs.get('startFrame', 0)
        self._endFrame = kwargs.get('endFrame', 1)
        self._step = kwargs.get('step', 1)
        self._exportSetId = kwargs.get('exportSetId', 0)
    # endregion

    # region Properties
    @property
    def asset(self):
        """
        Returns the asset associated with this sequence.

        :rtype: dcc.fbx.fbxasset.FbxAsset
        """

        return self._asset()

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

        return self._endFrame

    @step.setter
    def step(self, step):
        """
        Setter method that updates the frame step for this sequence.

        :type step: int
        :rtype: None
        """

        self._step = step

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
    def exportSet(self):
        """
        Returns the export set associated with this sequence.

        :rtype: fbxexportset.FbxExportSet
        """

        # Check if export set id is in range
        #
        numExportSets = len(self.asset.exportSets)

        if 0 <= self.exportSetId < numExportSets:

            return self.asset.exportSets[self.exportSetId]

        else:

            return None

    def exportPath(self):
        """
        Returns the export path for this sequence.

        :rtype: str
        """

        return os.path.join(
            os.path.expandvars(self.asset.directory),
            self.filePath,
            '{name}.fbx'.format(name=self.name)
        )

    def export(self):
        """
        Outputs this export set to the user defined path.

        :rtype: bool
        """

        # Check if export set exists
        #
        exportSet = self.exportSet()

        if exportSet is None:

            log.error('%s sequence cannot find associated export set!' % self.name)
            return

        # Select nodes from export set
        #
        exportSet.selectNodes()

        # Export selection
        #
        fnFbx = fnfbx.FnFbx()
        fnFbx.setAnimExportParams(**self)
        fnFbx.exportSelection(self.exportPath())
    # endregion
