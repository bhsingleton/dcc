import os

from collections import namedtuple
from dcc.json import jsonutils
from dcc.fbx import fbxio

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


FBX_ASSET_KEY = 'fbxAsset'
FBX_SEQUENCER_KEY = 'fbxSequencer'


Cache = namedtuple('Cache', ['item', 'lastModified'])


class FbxStructuredStorageIO(fbxio.FbxIO):
    """
    Overload of FbxIO that interfaces with data inside the COM structured storage.
    """

    __slots__ = ()
    __assets__ = {}  # type: Dict[int, Cache]
    __sequencers__ = {}  # type: Dict[int, Cache]

    @classmethod
    def getCachedAsset(cls, filePath):
        """
        Returns a cached asset using the supplied file's iNode id.

        :type filePath: str
        :rtype: fbxasset.FbxAsset
        """

        # Check if cache exists
        #
        stats = os.stat(filePath)
        fileId = stats.st_ino

        cache = cls.__assets__.get(fileId)

        if cache is None:

            return None

        # Check if cache is up-to-date
        #
        if stats.st_mtime != cache.lastModified:

            return cache.item

        else:

            return None

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
        scenePath = self.scene.currentFilePath()
        asset = self.getCachedAsset(scenePath)

        if asset is not None:

            return asset

        # Inspect file properties for asset
        #
        sceneProperties = self.scene.fileProperties()
        jsonString = sceneProperties.get(FBX_ASSET_KEY, '')

        asset = jsonutils.loads(jsonString)

        if asset is not None:

            stats = os.stat(scenePath)
            self.__assets__[stats.st_ino] = Cache(item=asset, lastModified=stats.st_mtime)

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

    def loadSequencers(self):
        """
        Returns a list of sequencers from the scene file.

        :rtype: List[fbxsequencer.FbxSequencer]
        """

        pass

    def saveSequencers(self, sequencers):
        """
        Commits any changes made to the scene sequencers

        :rtype: None
        """

        pass
