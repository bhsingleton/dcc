import os

from collections import namedtuple
from . import fbxasset, fbxexportset, fbxreferencedasset, fbxexportrange
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
FBX_REFERENCED_ASSET_KEY = 'fbxReferencedAssets'
FBX_SEQUENCERS_KEY = 'fbxSequencers'  # Deprecated!


AssetCache = namedtuple('AssetCache', ['item', 'lastModified'])
ReferencedAssetCache = namedtuple('ReferencedAssetCache', ['items', 'lastModified'])


class FbxIO(singleton.Singleton):
    """
    Singleton class that interfaces with fbx assets and sequencers.
    The class also provides methods for changing the function set constructor for references.
    This is useful for pipelines with custom reference systems.
    """

    # region Dunderscores
    __slots__ = ('_scene', '_assets', '_referencedAssets')

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
        self._referencedAssets = {}
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
    def referencedAssets(self):
        """
        Getter method that returns the sequencer cache.

        :rtype: Dict[int, SequencerCache]
        """

        return self._referencedAssets
    # endregion

    # region Methods
    def getCachedAsset(self, filePath, referenced=False):
        """
        Returns a cached asset using the supplied file's iNode id.

        :type filePath: str
        :type referenced: bool
        :rtype: Union[fbxasset.FbxAsset, None]
        """

        # Check if file exists
        #
        if not os.path.isfile(filePath):

            return None

        # Evaluate which asset type to return
        #
        stats = os.stat(filePath)
        fileId = stats.st_ino

        if referenced:

            # Check if cache exists
            #
            cache = self.referencedAssets.get(fileId, None)

            if stringutils.isNullOrEmpty(cache):

                return []

            # Check if cache is up-to-date
            #
            if stats.st_mtime == cache.lastModified:

                return cache.items

            else:

                return []

        else:

            # Check if cache exists
            #
            cache = self.assets.get(fileId, None)

            if not isinstance(cache, AssetCache):

                return None

            # Check if cache is up-to-date
            #
            if stats.st_mtime == cache.lastModified:

                return cache.item

            else:

                return None

    def loadAsset(self):
        """
        Returns an asset from the scene file.

        :rtype: Union[fbxasset.FbxAsset, None]
        """

        # Check if this is a new scene
        #
        if self.scene.isNewScene():

            return None

        # Check if asset has been cached
        #
        filePath = self.scene.currentFilePath()
        asset = self.getCachedAsset(filePath)

        if isinstance(asset, fbxasset.FbxAsset):

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

    def loadAssetFromReference(self, reference):
        """
        Returns an asset from a referenced scene file.

        :type reference: fnreference.FnReference
        :rtype: Union[fbxasset.FbxAsset, None]
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

    def loadReferencedAssets(self):
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
        referencedAssets = self.getCachedAsset(scenePath, referenced=True)

        if not stringutils.isNullOrEmpty(referencedAssets):

            return referencedAssets

        # Inspect file properties for asset
        #
        sceneProperties = self.scene.fileProperties()
        defaultString = sceneProperties.get(FBX_SEQUENCERS_KEY, '')
        jsonString = sceneProperties.get(FBX_REFERENCED_ASSET_KEY, defaultString)

        referencedAssets = jsonutils.loads(jsonString, default=[])

        if not stringutils.isNullOrEmpty(referencedAssets):

            stats = os.stat(scenePath)
            self.assets[stats.st_ino] = ReferencedAssetCache(items=referencedAssets, lastModified=stats.st_mtime)

        return referencedAssets

    def saveReferencedAssets(self, referencedAssets):
        """
        Commits any changes made to the scene sequencers.

        :type referencedAssets: List[fbxreferencedasset.FbxReferencedAsset]
        :rtype: None
        """

        jsonString = jsonutils.dumps(referencedAssets)

        self.scene.setFileProperty(FBX_REFERENCED_ASSET_KEY, jsonString)
        self.scene.deleteFileProperty(FBX_SEQUENCERS_KEY)
        self.scene.markDirty()

    def saveReferencedAssetsAs(self, referencedAssets, filePath):
        """
        Commits any sequencer changes to the specified file path.

        :type referencedAssets: List[fbxsequencer.FbxSequencer]
        :type filePath: str
        :rtype: None
        """

        jsonutils.dump(filePath, referencedAssets)

    def exportAnimationFromReferences(self, directory='', checkout=False):
        """
        Tries to export any animation from referenced files.

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
            sequencer = fbxreferencedasset.FbxReferencedAsset(guid=guid, exportRanges=[exportRange])

            if not sequencer.isValid():

                log.warning(f'Cannot locate valid asset from reference: {guid}')
                reference.next()

                continue

            # Export range and go to next reference
            #
            exportRange.export(checkout=checkout)
            reference.next()

    def exportAnimation(self, directory='', checkout=False):
        """
        Exports animation from any referenced assets.
        If the scene contains no assets then the scene references are used instead!

        :type directory: str
        :type checkout: bool
        :rtype: None
        """

        # Check if file contains any referenced assets
        # If not, try and guess export from scene references
        #
        referencedAssets = self.loadReferencedAssets()
        numReferencedAssets = len(referencedAssets)

        if numReferencedAssets == 0:

            return self.exportAnimationFromReferences(directory=directory, checkout=checkout)

        # Iterate through sequencers
        #
        for referencedAsset in referencedAssets:

            # Iterate through export-ranges
            #
            for exportRange in referencedAsset.exportRanges:

                # Check if directory has been overridden
                #
                if not stringutils.isNullOrEmpty(directory):

                    exportRange.directory = directory

                # Export range
                #
                exportRange.export(checkout=checkout)
    # endregion
