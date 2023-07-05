from . import fbxobjectset

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxMesh(fbxobjectset.FbxObjectSet):
    """
    Overload of FbxBase used to store mesh properties.
    """

    # region Dunderscores
    __slots__ = (
        '_includeNormals',
        '_includeTangentsAndBinormals',
        '_includeSmoothings',
        '_includeColorSets',
        '_includeSkins',
        '_includeBlendshapes',
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Declare private variables
        #
        self._includeNormals = kwargs.get('includeNormals', True)
        self._includeTangentsAndBinormals = kwargs.get('includeTangentsAndBinormals', True)
        self._includeSmoothings = kwargs.get('includeSmoothings', True)
        self._includeColorSets = kwargs.get('includeColorSets', False)
        self._includeSkins = kwargs.get('includeSkins', False)
        self._includeBlendshapes = kwargs.get('includeBlendshapes', False)

        # Call parent method
        #
        super(FbxMesh, self).__init__(*args, **kwargs)
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
    def includeNormals(self):
        """
        Getter method that returns the normals flag for this export set.

        :rtype: bool
        """

        return self._includeNormals

    @includeNormals.setter
    def includeNormals(self, includeNormals):
        """
        Setter method that updates the normals flag for this export set.

        :type includeNormals: bool
        :rtype: None
        """

        self._includeNormals = includeNormals

    @property
    def includeTangentsAndBinormals(self):
        """
        Getter method that returns the tangents and binormals flag for this export set.

        :rtype: bool
        """

        return self._includeTangentsAndBinormals

    @includeTangentsAndBinormals.setter
    def includeTangentsAndBinormals(self, includeTangentsAndBinormals):
        """
        Setter method that updates the tangents and binormals flag for this export set.

        :type includeTangentsAndBinormals: bool
        :rtype: None
        """

        self._includeTangentsAndBinormals = includeTangentsAndBinormals

    @property
    def includeSmoothings(self):
        """
        Getter method that returns the smoothings flag for this export set.

        :rtype: bool
        """

        return self._includeSmoothings

    @includeSmoothings.setter
    def includeSmoothings(self, includeSmoothings):
        """
        Setter method that updates the smoothings flag for this export set.

        :type includeSmoothings: bool
        :rtype: None
        """

        self._includeSmoothings = includeSmoothings

    @property
    def includeColorSets(self):
        """
        Getter method that returns the color sets flag for this export set.

        :rtype: bool
        """

        return self._includeColorSets

    @includeColorSets.setter
    def includeColorSets(self, includeColorSets):
        """
        Setter method that updates the color sets flag for this export set.

        :type includeColorSets: bool
        :rtype: None
        """

        self._includeColorSets = includeColorSets

    @property
    def includeSkins(self):
        """
        Getter method that returns the skins flag for this export set.

        :rtype: bool
        """

        return self._includeSkins

    @includeSkins.setter
    def includeSkins(self, includeSkins):
        """
        Setter method that updates the skins flag for this export set.

        :type includeSkins: bool
        :rtype: None
        """

        self._includeSkins = includeSkins

    @property
    def includeBlendshapes(self):
        """
        Getter method that returns the blend shapes flag for this export set.

        :rtype: bool
        """

        return self._includeBlendshapes

    @includeBlendshapes.setter
    def includeBlendshapes(self, includeBlendshapes):
        """
        Setter method that updates the blend shapes flag for this export set.

        :type includeBlendshapes: bool
        :rtype: None
        """

        self._includeBlendshapes = includeBlendshapes
    # endregion


