from dcc.fbx import fbxbase, fbxexportset, FbxFileType, FbxFileVersion
from dcc.collections import notifylist

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxAsset(fbxbase.FbxBase):
    """
    Overload of FbxBase that interfaces with fbx export set data.
    """

    # region Dunderscores
    __slots__ = (
        '_directory',
        '_frameRate',
        '_fileType',
        '_fileVersion',
        '_exportSets'
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(FbxAsset, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._directory = kwargs.get('directory', '')
        self._frameRate = kwargs.get('frameRate', 30)
        self._fileType = kwargs.get('fileType', FbxFileType.Binary)
        self._fileVersion = kwargs.get('fileVersion', FbxFileVersion.FBX201600)
        self._exportSets = notifylist.NotifyList()

        # Setup notifies
        #
        self._exportSets.addCallback('itemAdded', self.exportSetAdded)
        self._exportSets.addCallback('itemRemoved', self.exportSetRemoved)
    # endregion

    # region Properties
    @property
    def directory(self):
        """
        Getter method that returns the directory for this asset.

        :rtype: str
        """

        return self._directory

    @directory.setter
    def directory(self, directory):
        """
        Setter method that updates the directory for this asset.

        :type directory: str
        :rtype: None
        """

        self._directory = directory

    @property
    def frameRate(self):
        """
        Getter method that returns the frame rate for this asset.

        :rtype: int
        """

        return self._frameRate

    @frameRate.setter
    def frameRate(self, frameRate):
        """
        Setter method that updates the frame rate for this asset.

        :type frameRate: int
        :rtype: None
        """

        self._frameRate = frameRate

    @property
    def fileType(self):
        """
        Getter method that returns the fbx file type for this asset

        :rtype: FbxFileType
        """

        return self._fileType

    @fileType.setter
    def fileType(self, fileType):
        """
        Setter method that updates the fbx file type for this asset

        :type fileType: FbxFileType
        :rtype: None
        """

        self._fileType = FbxFileType(fileType)

    @property
    def fileVersion(self):
        """
        Getter method that returns the fbx file version for this asset

        :rtype: FbxFileVersion
        """

        return self._fileVersion

    @fileVersion.setter
    def fileVersion(self, fileVersion):
        """
        Setter method that updates the fbx file version for this asset

        :type fileVersion: FbxFileVersion
        :rtype: None
        """

        self._fileVersion = FbxFileVersion(fileVersion)

    @property
    def exportSets(self):
        """
        Getter method that returns the fbx export sets for this asset

        :rtype: List[fbxexportset.FbxExportSet]
        """

        return self._exportSets

    @exportSets.setter
    def exportSets(self, exportSets):
        """
        Getter method that returns the fbx export sets for this asset

        :type exportSets: List[fbxexportset.FbxExportSet]
        :rtype: None
        """

        self._exportSets.clear()
        self._exportSets.extend(exportSets)
    # endregion

    # region Methods
    def initializeSequences(self):

        self.reference.guid()

    def save(self):
        """
        Saves any changes made to this asset.

        :rtype: None
        """

        if self.reference.isValid():

            pass

        else:

            pass

    # endregion

    # region Callbacks
    def exportSetAdded(self, index, exportSet):
        """
        Adds a reference of this asset to the supplied export set.

        :type index: int
        :type exportSet: fbxexportset.FbxExportSet
        :rtype: None
        """

        exportSet._asset = self.weakReference()

    def exportSetRemoved(self, exportSet):
        """
        Removes the reference of this asset from the supplied export set.

        :type exportSet: fbxexportset.FbxExportSet
        :rtype: None
        """

        exportSet._asset = self.nullWeakReference
    # endregion
