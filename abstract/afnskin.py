import os
import json

from abc import ABCMeta, abstractmethod
from six import with_metaclass, integer_types
from six.moves import collections_abc
from copy import deepcopy

from . import afnbase
from .. import fnnode

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Influences(collections_abc.MutableMapping):
    """
    Overload of MutableMapping used to store influence objects.
    """

    __slots__ = ('_influences',)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(Influences, self).__init__()

        # Declare private variables
        #
        self._influences = {}

        # Evaluate arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            self.update(args[0])

    def __call__(self, index):
        """
        Private method that returns an indexed influence as a function set.

        :type index: int
        :rtype: fnnode.FnNode
        """

        return fnnode.FnNode(self.__getitem__(index))

    def __getitem__(self, key):
        """
        Private method that returns an indexed influence.

        :type key: int
        :rtype: Union[om.MObject, pymxs.MXSWrapperBase]
        """

        # Check key type
        #
        if isinstance(key, integer_types):

            handle = self._influences.get(key, 0)
            return fnnode.FnNode.getNodeByHandle(handle)

        else:

            raise TypeError('__getitem__() expects an int (%s given)!' % type(key).__name__)

    def __setitem__(self, key, value):
        """
        Private method that updates an indexed influence.

        :type key: int
        :type value: Union[om.MObject, pymxs.MXSWrapperBase]
        :rtype: None
        """

        # Check if value is accepted
        #
        fnNode = fnnode.FnNode()
        success = fnNode.trySetObject(value)

        if success:

            self._influences[key] = fnNode.handle()

        else:

            raise TypeError('__setitem__() expects a valid object (%s given)!' % type(value).__name__)

    def __delitem__(self, key):
        """
        Private method that deletes an indexed influence.

        :type key: int
        :rtype: None
        """

        del self._influences[key]

    def __iter__(self):
        """
        Returns a generator that yields all influence objects.

        :rtype: iter
        """

        for (key, value) in self.items():

            yield key, fnnode.FnNode.getNodeByHandle(value)

    def __len__(self):
        """
        Private method that evaluates the size of this collection.

        :rtype: int
        """

        return len(self._influences)

    def __contains__(self, item):
        """
        Private method that evaluates if the given item exists in this collection.

        :type item: Any
        :rtype: bool
        """

        fnNode = fnnode.FnNode()
        success = fnNode.trySetObject(item)

        if success:

            return fnNode.handle() in self._influences.values()

        else:

            return False

    def keys(self):
        """
        Returns a key view for this collection.

        :rtype: collections_abc.KeysView
        """

        return self._influences.keys()

    def values(self):
        """
        Returns a values view for this collection.

        :rtype: collections_abc.ValuesView
        """

        return self._influences.values()

    def items(self):
        """
        Returns an items view for this collection.

        :rtype: collections_abc.ItemsView
        """

        return self._influences.items()

    def index(self, influence):
        """
        Returns the index for the given influence.
        If no index is found then none is returned!

        :type influence: Union[om.MObject, pymxs.MXSWrapperBase]
        :rtype: int
        """

        return {handle: index for (index, handle) in self.items()}.get(fnnode.FnNode(influence).handle(), None)

    def update(self, obj):
        """
        Copies the values from the supplied object to this collection.

        :type obj: dict
        :rtype: None
        """

        for (key, value) in obj.items():

            self.__setitem__(key, value)

    def clear(self):
        """
        Removes all of the influences from this collection.

        :rtype: None
        """

        self._influences.clear()


class AFnSkin(with_metaclass(ABCMeta, afnbase.AFnBase)):
    """
    Overload of AFnBase that outlines function set behaviour for DCC skinning.
    """

    __slots__ = ('_influences',)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.
        """

        # Declare private variables
        #
        self._influences = Influences()

        # Call parent method
        #
        super(AFnSkin, self).__init__(*args, **kwargs)

    def __getstate__(self):
        """
        Private method that returns an object state for this instance.

        :rtype: dict
        """

        # Define state object
        #
        influences = {}
        vertices = {}
        points = {}

        state = {
            'name': self.name(),
            'influences': influences,
            'maxInfluences': self.maxInfluences,
            'vertices': vertices,
            'points': points
        }

        # Commit influence binder to state object
        #
        for (influenceId, influence) in self.iterInfluences():

            influences[influenceId] = None

        # Commit vertex weights to state object
        #
        for ((vertexIndex, vertexWeights), point) in zip(self.iterWeights(), self.iterControlPoints()):

            vertices[vertexIndex] = point
            points[vertexIndex] = vertexWeights

        return state

    def __setstate__(self, state):
        """
        Private method that copies the weights from the supplied state object.

        :type state: dict
        :rtype: None
        """

        pass

    @abstractmethod
    def shape(self):
        """
        Returns the shape node associated with the deformer.

        :rtype: Any
        """

        pass

    @abstractmethod
    def iterControlPoints(self, *args):
        """
        Returns a generator that yields control points.

        :rtype: iter
        """

        pass

    def controlPoints(self, *args):
        """
        Returns the control points from the intermediate object.

        :rtype: list
        """

        return list(self.iterControlPoints(*args))

    @abstractmethod
    def numControlPoints(self):
        """
        Evaluates the number of control points from this deformer.

        :rtype: int
        """

        pass

    @abstractmethod
    def iterInfluences(self):
        """
        Returns a generator that yields all of the influence objects from this deformer.

        :rtype: iter
        """

        pass

    def influences(self):
        """
        Returns all of the influence objects from this deformer.

        :rtype: Influences
        """

        # Check if influences require updating
        #
        current = len(self._influences)

        if current != self.numInfluences():

            self._influences.clear()
            self._influences.update(self.iterInfluences())

        return self._influences

    @abstractmethod
    def numInfluences(self):
        """
        Returns the number of influences being use by this deformer.

        :rtype: int
        """

        pass

    @abstractmethod
    def addInfluence(self, influence):
        """
        Adds an influence to this deformer.

        :type influence: Any
        :rtype: bool
        """

        pass

    def addInfluences(self, influences):
        """
        Adds a list of influences to this deformer.

        :type influences: list
        :rtype: None
        """

        for influence in influences:

            self.addInfluence(influence)

    @abstractmethod
    def removeInfluence(self, influenceId):
        """
        Removes an influence from this deformer by id.

        :type influenceId: int
        :rtype: bool
        """

        pass

    def removeInfluences(self, influences):
        """
        Removes a list of influences from this deformer.

        :type influences: list
        :rtype: None
        """

        for influence in influences:

            self.removeInfluence(influence)

    @abstractmethod
    def maxInfluences(self):
        """
        Getter method that returns the max number of influences for this deformer.

        :rtype: int
        """

        pass

    def findRoot(self):
        """
        Returns the skeleton root associated with this deformer.

        :rtype: Union[om.MObject, pymxs.MXSWrapperBase]
        """

        # Get all influences
        #
        influences = self.influences()

        fullPathNames = [influences(x).dagPath() for x in influences.keys()]
        commonPrefix = os.path.commonprefix(fullPathNames)

        if commonPrefix is None:

            raise TypeError('Influence objects do not share a common root!')

        # Split pipes
        #
        strings = [x for x in commonPrefix.split('|') if len(x) > 0]
        numStrings = len(strings)

        fnNode = fnnode.FnNode(commonPrefix)
        joint = fnNode.object()

        # Check number of strings
        #
        if numStrings == 0:

            return joint

        # Walk up hierarchy until we find the root joint
        #
        while True:

            # Check if this joint has a parent
            #
            if not fnNode.hasParent():

                return joint

            # Check if parent is still a joint
            #
            parent = fnNode.parent()
            fnNode.setObject(parent)

            if not fnNode.isJoint():

                return joint

            else:

                joint = parent

    @abstractmethod
    def iterWeights(self, *args):
        """
        Returns a generator that yields skin weights.
        If no vertex indices are supplied then all of the skin weights should be yielded.

        :rtype: iter
        """

        pass

    def weights(self, *args):
        """
        Returns a dictionary with skin weights.
        Each key represents a vertex index for each set of vertex weights.

        :rtype: dict[int:dict[int:float]]
        """

        return dict(self.iterWeights(*args))

    def setWeights(self, vertexIndices, target, source, amount, falloff=None):
        """
        Sets the supplied target ID to the specified amount while preserving normalization.

        :type vertexIndices: list[int]
        :type target: int
        :type source: list[int]
        :type amount: float
        :type falloff: dict[int:float]
        :rtype: dict[int:dict[int:float]]
        """

        pass

    def scaleWeights(self, vertexIndices, target, source, percent, falloff=None):
        """
        Scales the supplied target ID to the specified amount while preserving normalization.

        :type vertexIndices: list
        :type target: int
        :type source: list[int]
        :type percent: float
        :type falloff: dict[int:float]
        :rtype: dict[int:dict[int:float]]
        """

        pass

    def incrementWeights(self, vertexIndices, target, source, increment, falloff=None):
        """
        Increments the supplied target ID to the specified amount while preserving normalization.

        :type vertexIndices: list
        :type target: int
        :type source: list[int]
        :type increment: float
        :type falloff: dict[int:float]
        :rtype: dict[int:dict[int:float]]
        """

        pass

    def normalizeWeights(self, vertexWeights):
        """
        Normalizes the supplied vertex weights.

        :type vertexWeights: dict[int:float]
        :rtype: dict[int:float]
        """

        pass

    def pruneWeights(self, vertexWeights):
        """
        Prunes the supplied vertex weights to meet the maximum number of weighted influences.

        :type vertexWeights: dict[int:float]
        :rtype: dict[int:float]
        """

        pass

    def applyWeights(self, vertices):
        """
        Assigns the supplied vertex weights to this deformer.

        :type vertices: dict[int:dict[int:float]]
        :rtype: None
        """

        pass

    def saveWeights(self, filePath):
        """
        Saves the skin weights to the specified file path.

        :type filePath: str
        :rtype: None
        """

        with open(filePath, 'w') as jsonFile:

            json.dump(self.__getstate__(), jsonFile)

    def loadWeights(self, filePath):
        """
        Loads the skin weights from the specified file path.

        :type filePath: str
        :rtype: None
        """

        with open(filePath, 'r') as jsonFile:

            self.__setstate__(json.load(jsonFile))
