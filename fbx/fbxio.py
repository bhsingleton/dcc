import os

from collections import namedtuple
from . import fbxasset
from .. import fnscene
from ..abstract import singleton
from ..json import jsonutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


FBX_ASSET_KEY = 'fbxAsset'
FBX_SEQUENCER_KEY = 'fbxSequencer'


Cache = namedtuple('Cache', ['item', 'lastModified'])


class FbxIO(singleton.Singleton):
    """
    Singleton class that interfaces with fbx assets.
    """

    # region Dunderscores
    __slots__ = ('_scene', '_assets')

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

        :rtype: Dict[int, Cache]
        """

        return self._assets
    # endregion

    # region Methods
    def getCachedAsset(self, filePath):
        """
        Returns a cached asset using the supplied file's iNode id.

        :type filePath: str
        :rtype: fbxasset.FbxAsset
        """

        # Check if cache exists
        #
        stats = os.stat(filePath)
        fileId = stats.st_ino

        cache = self.assets.get(fileId)

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
            self.assets[stats.st_ino] = Cache(item=asset, lastModified=stats.st_mtime)

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
    # endregion
