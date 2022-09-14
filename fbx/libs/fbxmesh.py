from . import fbxbase, FbxMeshComponent
from ... import fnnode

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxMesh(fbxbase.FbxBase):
    """
    Overload of FbxBase used to store mesh properties.
    """

    # region Dunderscores
    __slots__ = ('_extract', '_extractType', '_extractElements')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Declare private variables
        #
        self._extract = kwargs.get('extract', False)
        self._extractType = kwargs.get('extractType', FbxMeshComponent.Polygon)
        self._extractElements = kwargs.get('extractElements', [])

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
    def extract(self):
        """
        Getter method that returns the extract flag.

        :rtype: bool
        """

        return self._extract

    @extract.setter
    def extract(self, extract):
        """
        Setter method that updates the extract flag.

        :type extract: bool
        :rtype: None
        """

        self._extract = extract

    @property
    def extractType(self):
        """
        Getter method that returns the extraction type.

        :rtype: FbxMeshComponent
        """

        return self._extractType

    @extractType.setter
    def extractType(self, extractType):
        """
        Setter method that updates the extraction type.

        :type extractType: FbxMeshComponent
        :rtype: None
        """

        self._extractType = FbxMeshComponent(extractType)

    @property
    def extractElements(self):
        """
        Getter method that returns the mesh extraction elements.

        :rtype: List[int]
        """

        return self._extractElements

    @extractElements.setter
    def extractElements(self, extractElements):
        """
        Setter method that updates the mesh extraction elements.

        :type extractElements: List[int]
        :rtype: None
        """

        self._extractElements = extractElements
    # endregion

    # region Methods
    def select(self, namespace=''):
        """
        Selects the associated node from the scene file.

        :type namespace: str
        :rtype: None
        """

        # Check if root node is valid
        #
        node = fnnode.FnNode()
        success = node.trySetObject(self.absolutify(self.name, namespace))

        if not success:

            return

        # Select root and descendants
        #
        node.select(replace=False)

    def serialize(self, fbxScene):
        """
        Serializes the associated mesh for fbx.

        :type fbxScene: Any
        :rtype: None
        """

        pass
    # endregion

