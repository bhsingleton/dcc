import os

from collections import namedtuple
from . import fbxasset, fbxexportset, fbxsequencer, fbxexportrange
from ... import fnscene, fnreference
from ...abstract import singleton
from ...json import jsonutils
from ...python import stringutils
from ...perforce import p4utils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


FBX_ASSET_KEY = 'fbxAsset'
FBX_SEQUENCERS_KEY = 'fbxSequencers'


AssetCache = namedtuple('AssetCache', ['item', 'lastModified'])
SequencerCache = namedtuple('SequencerCache', ['items', 'lastModified'])


class FbxIO(singleton.Singleton):
    """
    Singleton class that interfaces with fbx assets and sequencers.
    The class also provides methods for changing the function set constructor for references.
    This is useful for pipelines with custom reference systems.
    """

    # region Dunderscores
    __slots__ = ('_scene', '_assets', '_sequencers')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(FbxIO, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._scene = fnscene.FnScene()
        self._assets = {}
        self._sequencers = {}
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
    def assets(self):
        """
        Getter method that returns the asset cache.

        :rtype: Dict[int, AssetCache]
        """

        return self._assets

    @property
    def sequencers(self):
        """
        Getter method that returns the sequencer cache.

        :rtype: Dict[int, SequencerCache]
        """

        return self._sequencers
    # endregion

    # region Methods
    def getCachedAsset(self, filePath):
        """
        Returns a cached asset using the supplied file's iNode id.

        :type filePath: str
        :rtype: fbxasset.FbxAsset
        """

        # Check if file exists
        #
        if not os.path.isfile(filePath):

            return None

        # Check if cache exists
        #
        stats = os.stat(filePath)
        fileId = stats.st_ino

        cache = self.assets.get(fileId, None)

        if cache is None:

            return None

        # Check if cache is up-to-date
        #
        if stats.st_mtime == cache.lastModified:

            return cache.item

        else:

            return None

    def loadReferencedAsset(self, reference):
        """
        Returns an asset from a referenced scene file.

        :rtype: fbxasset.FbxAsset
        """

        # Check if reference is valid
        #
        if not reference.isValid():

            return None

        # Check if asset has been cached
        #
        filePath = reference.filePath()
        asset = self.getCachedAsset(filePath)

        if asset is not None:

            return asset

        # Inspect file properties for asset
        #
        sceneProperties = reference.fileProperties()
        jsonString = sceneProperties.get(FBX_ASSET_KEY, '')

        asset = jsonutils.loads(jsonString)

        if asset is not None:

            stats = os.stat(filePath)
            self.assets[stats.st_ino] = AssetCache(item=asset, lastModified=stats.st_mtime)

        return asset

    def loadAsset(self):
        """
        Returns an asset from the scene file.

        :rtype: fbxasset.FbxAsset
        """

        # Check if this is a new scene
        #
        if self.scene.isNewScene():

            return None

        # Check if asset has been cached
        #
        filePath = self.scene.currentFilePath()
        asset = self.getCachedAsset(filePath)

        if asset is not None:

            return asset

        # Inspect file properties for asset
        #
        sceneProperties = self.scene.fileProperties()
        jsonString = sceneProperties.get(FBX_ASSET_KEY, '')

        asset = jsonutils.loads(jsonString)

        if asset is not None:

            stats = os.stat(filePath)
            self.assets[stats.st_ino] = AssetCache(item=asset, lastModified=stats.st_mtime)

        return asset

    def saveAsset(self, asset):
        """
        Commits any changes made to the scene asset.

        :type asset: fbxasset.FbxAsset
        :rtype: None
        """

        jsonString = jsonutils.dumps(asset)

        self.scene.setFileProperty(FBX_ASSET_KEY, jsonString)
        self.scene.markDirty()

    def saveAssetAs(self, asset, filePath):
        """
        Commits any asset changes to the specified file path.

        :type asset: fbxasset.FbxAsset
        :type filePath: str
        :rtype: None
        """

        jsonutils.dump(filePath, asset)

    def importAsset(self, filePath):
        """
        Returns an asset from the specified file path.

        :type filePath: str
        :rtype: fbxasset.FbxAsset
        """

        return jsonutils.load(filePath)

    def exportAsset(self, directory='', checkout=False):
        """
        Exports sets from the asset in the current scene file.

        :type directory: str
        :type checkout: bool
        :rtype: None
        """

        # Iterate through export sets
        #
        asset = self.loadAsset()

        for exportSet in asset.exportSets:

            # Check if directory has been overriden
            #
            if not stringutils.isNullOrEmpty(directory):

                exportSet.directory = directory

            # Export set
            #
            exportSet.export(checkout=checkout)

    def getCachedSequencers(self, filePath):
        """
        Returns a cached asset using the supplied file's ID.

        :type filePath: str
        :rtype: List[fbxsequencer.FbxSequencer]
        """

        # Check if file exists
        #
        if not os.path.isfile(filePath):

            return []

        # Check if cache exists
        #
        stats = os.stat(filePath)
        fileId = stats.st_ino

        cache = self.sequencers.get(fileId, None)

        if cache is None:

            return []

        # Check if cache is up-to-date
        #
        if stats.st_mtime == cache.lastModified:

            return cache.items

        else:

            return []

    def loadSequencers(self):
        """
        Returns the sequencers from the scene file.

        :rtype: List[fbxsequencer.FbxSequencer]
        """

        # Check if this is a new scene
        #
        if self.scene.isNewScene():

            return []

        # Check if asset has been cached
        #
        scenePath = self.scene.currentFilePath()
        sequencers = self.getCachedSequencers(scenePath)

        if not self.scene.isNullOrEmpty(sequencers):

            return sequencers

        # Inspect file properties for asset
        #
        sceneProperties = self.scene.fileProperties()
        jsonString = sceneProperties.get(FBX_SEQUENCERS_KEY, '')

        sequencers = jsonutils.loads(jsonString, default=[])

        if not self.scene.isNullOrEmpty(sequencers):

            stats = os.stat(scenePath)
            self.assets[stats.st_ino] = SequencerCache(items=sequencers, lastModified=stats.st_mtime)

        return sequencers

    def saveSequencers(self, sequencers):
        """
        Commits any changes made to the scene sequencers.

        :type sequencers: List[fbxsequencer.FbxSequencer]
        :rtype: None
        """

        jsonString = jsonutils.dumps(sequencers)

        self.scene.setFileProperty(FBX_SEQUENCERS_KEY, jsonString)
        self.scene.markDirty()

    def saveSequencersAs(self, sequencers, filePath):
        """
        Commits any sequencer changes to the specified file path.

        :type sequencers: List[fbxsequencer.FbxSequencer]
        :type filePath: str
        :rtype: None
        """

        jsonutils.dump(filePath, sequencers)

    def exportReferencedAssets(self, directory='', checkout=False):
        """
        Tries to export animation from the referenced assets in the current scene file.

        :type directory: str
        :type checkout: bool
        :rtype: None
        """

        # Check if scene contains any references
        #
        references = list(fnreference.FnReference.iterSceneReferences())
        numReferences = len(references)

        if numReferences == 0:

            log.warning('Scene contains no referenced assets!')
            return

        # Collect references from scene
        #
        reference = fnreference.FnReference()
        reference.setQueue(references)

        while not reference.isDone():

            # Create export range from scene's animation-range
            #
            name = self.scene.currentName()
            startFrame, endFrame = self.scene.getStartTime(), self.scene.getEndTime()

            exportRange = fbxexportrange.FbxExportRange(name=name, startFrame=startFrame, endFrame=endFrame)

            if not stringutils.isNullOrEmpty(directory):

                exportRange.directory = directory

            else:

                exportRange.directory = self.scene.currentDirectory()

            # Create sequencer from reference's GUID
            #
            guid = reference.guid()
            sequencer = fbxsequencer.FbxSequencer(guid=guid, exportRanges=[exportRange])

            if not sequencer.isValid():

                log.warning(f'Cannot locate valid asset from reference: {guid}')
                reference.next()

                continue

            # Export range and go to next reference
            #
            exportRange.export(checkout=checkout)
            reference.next()

    def exportSequencers(self, directory='', checkout=False):
        """
        Exports animation from the sequencers in the current scene file.

        :type directory: str
        :type checkout: bool
        :rtype: None
        """

        # Check if file contains any sequencers
        #
        sequencers = self.loadSequencers()
        numSequencers = len(sequencers)

        if numSequencers == 0:

            self.exportReferencedAssets(directory=directory, checkout=checkout)

        # Iterate through sequencers
        #
        for sequencer in sequencers:

            # Iterate through export-ranges
            #
            for exportRange in sequencer.exportRanges:

                # Check if directory has been overriden
                #
                if not stringutils.isNullOrEmpty(directory):

                    exportRange.directory = directory

                # Export range
                #
                exportRange.export(checkout=checkout)
    # endregion
