from . import fbxbase
from ... import fnnode, fnlayer

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxSkeleton(fbxbase.FbxBase):
    """
    Overload of FbxNode used to store skeleton properties.
    """

    # region Dunderscores
    __slots__ = (
        '_includeDescendants',
        '_includeJoints',
        '_includeLayers',
        '_includeSelectionSets',
        '_includeRegex'
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Declare private variables
        #
        self._includeDescendants = kwargs.get('includeDescendants', True)
        self._includeJoints = kwargs.get('includeJoints', [])
        self._includeLayers = kwargs.get('includeLayers', [])
        self._includeSelectionSets = kwargs.get('includeSelectionSets', [])
        self._includeRegex = kwargs.get('includeRegex', '')

        # Call parent method
        #
        super(FbxSkeleton, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def includeDescendants(self):
        """
        Getter method that returns the include-descendants flag.

        :rtype: bool
        """

        return self._includeDescendants

    @includeDescendants.setter
    def includeDescendants(self, includeDescendants):
        """
        Setter method that updates the include-descendants flag.

        :type includeDescendants: bool
        :rtype: None
        """

        self._includeDescendants = includeDescendants

    @property
    def includeJoints(self):
        """
        Getter method that returns the list of joints to be included.

        :rtype: List[str]
        """

        return self._includeJoints

    @includeJoints.setter
    def includeJoints(self, includeJoints):
        """
        Setter method that updates the list of joints to be included.

        :type includeJoints: List[str]
        :rtype: None
        """

        self._includeJoints.clear()
        self._includeJoints.extend(includeJoints)

    @property
    def includeLayers(self):
        """
        Getter method that returns the list of layers to be included.

        :rtype: List[str]
        """

        return self._includeLayers

    @includeLayers.setter
    def includeLayers(self, includeLayers):
        """
        Setter method that updates the list of layers to be included.

        :type includeLayers: List[str]
        :rtype: None
        """

        self._includeLayers.clear()
        self._includeLayers.extend(includeLayers)

    @property
    def includeSelectionSets(self):
        """
        Getter method that returns the list of layers to be included.

        :rtype: List[str]
        """

        return self._includeSelectionSets

    @includeSelectionSets.setter
    def includeSelectionSets(self, includeSelectionSets):
        """
        Setter method that updates the list of layers to be included.

        :type includeSelectionSets: List[str]
        :rtype: None
        """

        self._includeSelectionSets.clear()
        self._includeSelectionSets.extend(includeSelectionSets)

    @property
    def includeRegex(self):
        """
        Getter method that returns the regex pattern for including joints.

        :rtype: str
        """

        return self._includeRegex

    @includeRegex.setter
    def includeRegex(self, includeRegex):
        """
        Setter method that updates the regex pattern for including joints.

        :type includeRegex: str
        :rtype: None
        """

        self._includeRegex = includeRegex
    # endregion

    # region Methods
    def select(self, namespace=''):
        """
        Selects the associated nodes from the scene file.

        :type namespace: str
        :rtype: None
        """

        self.scene.clearActiveSelection()
        self.selectRoot(namespace=namespace)
        self.selectIncludeJoints(namespace=namespace)
        self.selectIncludeLayers(namespace=namespace)
        self.selectIncludeSelectionSets(namespace=namespace)
        self.selectIncludeRegex(namespace=namespace)

    def selectRoot(self, namespace=''):
        """
        Selects the associated root node from the scene file.

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

        if self.includeDescendants:

            descendant = fnnode.FnNode(node.iterDescendants())

            while not descendant.isDone():

                descendant.next()
                descendant.select(replace=False)

    def selectIncludeJoints(self, namespace=''):
        """
        Selects the associated nodes from the scene.

        :type namespace: str
        :rtype: None
        """

        jointNames = [self.absolutify(name, namespace) for name in self.includeJoints]
        node = fnnode.FnNode(iter(jointNames))

        while not node.isDone():

            node.next()
            node.select(replace=False)

    def selectIncludeLayers(self, namespace=''):
        """
        Selects the nodes from the associated layers.

        :type namespace: str
        :rtype: None
        """

        layerNames = [self.absolutify(name, namespace) for name in self.includeLayers]
        layer = fnlayer.FnLayer(iter(layerNames))

        node = fnnode.FnNode()

        while not layer.isDone():

            layer.next()

            for obj in layer.iterNodes():

                node.setObject(obj)
                node.select(replace=False)

    def selectIncludeSelectionSets(self, namespace=''):
        """
        Selects the nodes from the associated selection-sets.

        :type namespace: str
        :rtype: None
        """

        pass

    def selectIncludeRegex(self, namespace=''):
        """
        Selects the nodes that match the specified name pattern/regex.

        :type namespace: str
        :rtype: None
        """

        fnNode = fnnode.FnNode(fnnode.FnNode.iterInstancesByRegex(self.includeRegex))

        while not fnNode.isDone():

            fnNode.next()
            fnNode.select(replace=False)

    def serialize(self, fbxScene):
        """
        Serializes the associated mesh for fbx.

        :type fbxScene: Any
        :rtype: None
        """

        pass
    # endregion
