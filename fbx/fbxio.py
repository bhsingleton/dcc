from abc import ABCMeta, abstractmethod
from six import with_metaclass
from dcc import fnscene, fnreference
from dcc.abstract import afnscene, afnreference
from dcc.json import jsonutils
from dcc.decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxIO(with_metaclass(ABCMeta, object)):
    """
    Abstract base class that outlines fbx asset interfaces.
    Different save/load routines can be registered to support a studio's needs.
    """

    # region Dunderscores
    __slots__ = ()
    __scene__ = fnscene.FnScene()
    __reference__ = fnreference.FnReference()

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(FbxIO, self).__init__()
    # endregion

    # region Properties
    @classproperty
    def scene(cls):
        """
        Getter method that returns the scene function set.

        :rtype: fnscene.FnScene
        """

        return cls.__scene__

    @scene.setter
    def scene(cls, scene):
        """
        Setter method that overrides the scene function set.

        :type scene: fnscene.FnScene
        :rtype: None
        """

        if issubclass(scene.__class__, afnscene.AFnScene):

            cls.__scene__ = scene

        else:

            raise TypeError('scene.setter() expects a scene function set (%s given)!' % type(scene).__name__)

    @classproperty
    def reference(cls):
        """
        Getter method that returns the reference function set.

        :rtype: fnreference.FnReference
        """

        return cls.__reference__

    @reference.setter
    def reference(cls, reference):
        """
        Setter method that overrides the reference function set.
        Use this in case you work in a godforsaken program like 3ds Max...

        :type fnReference: fnreference.FnReference
        :rtype: None
        """

        if issubclass(reference.__class__, afnreference.AFnReference):

            cls.__reference__ = reference

        else:

            raise TypeError('reference.setter() expects a reference function set (%s given)!' % type(reference).__name__)
    # endregion

    # region Methods
    @abstractmethod
    def loadAsset(self):
        """
        Returns an asset from the scene file.

        :rtype: fbxasset.FbxAsset
        """

        pass

    @abstractmethod
    def saveAsset(self, asset):
        """
        Commits any changes made to the scene asset.

        :type asset: fbxasset.FbxAsset
        :rtype: None
        """

        pass

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

    @abstractmethod
    def loadSequencers(self):
        """
        Returns a list of sequencers from the scene file.

        :rtype: List[fbxsequencer.FbxSequencer]
        """

        pass

    @abstractmethod
    def saveSequencers(self, sequencers):
        """
        Commits any changes made to the scene sequencers

        :type sequencers: List[fbxsequencer.FbxSequencer]
        :rtype: None
        """

        pass
    # endregion
