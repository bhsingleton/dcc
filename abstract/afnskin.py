from abc import ABCMeta, abstractmethod
from copy import deepcopy
from . import afnnode
from .. import fnnode, fntransform, fnmesh
from ..naming import namingutils
from ..python import stringutils
from ..math import floatmath, skinmath
from ..dataclasses.vector import Vector
from ..vendor.six import with_metaclass, integer_types, string_types
from ..vendor.six.moves import collections_abc

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Influences(collections_abc.MutableMapping):
    """
    Overload of MutableMapping used to store influence objects.
    """

    # region Dunderscores
    __slots__ = ('__objects__',)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(Influences, self).__init__()

        # Declare private variables
        #
        self.__objects__ = {}

        # Evaluate arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            self.update(args[0])

    def __getitem__(self, index):
        """
        Private method that returns an indexed influence.

        :type index: int
        :rtype: Union[fntransform.FnTransform, None]
        """

        # Check key type
        #
        if isinstance(index, integer_types):

            return self.get(index, None)

        else:

            raise TypeError('__getitem__() expects an int (%s given)!' % type(index).__name__)

    def __setitem__(self, key, value):
        """
        Private method that updates an indexed influence.

        :type key: int
        :type value: Any
        :rtype: None
        """

        # Check if value is accepted
        #
        influence = fntransform.FnTransform()
        success = influence.trySetObject(value)

        if success:

            self.__objects__[key] = influence

        else:

            raise TypeError('__setitem__() expects a valid object (%s given)!' % type(value).__name__)

    def __delitem__(self, key):
        """
        Private method that deletes an indexed influence.

        :type key: int
        :rtype: None
        """

        del self.__objects__[key]

    def __contains__(self, item):
        """
        Private method that evaluates if the given item exists in this collection.

        :type item: Any
        :rtype: bool
        """

        return item in self.__objects__.values()

    def __iter__(self):
        """
        Returns a generator that yields all influence objects.

        :rtype: iter
        """

        return iter(self.__objects__)

    def __len__(self):
        """
        Private method that evaluates the size of this collection.

        :rtype: int
        """

        return len(self.__objects__)
    # endregion

    # region Methods
    def keys(self):
        """
        Returns a key view for this collection.

        :rtype: collections_abc.KeysView
        """

        return self.__objects__.keys()

    def values(self):
        """
        Returns a values view for this collection.

        :rtype: collections_abc.ValuesView
        """

        return self.__objects__.values()

    def items(self):
        """
        Returns an items view for this collection.

        :rtype: collections_abc.ItemsView
        """

        return self.__objects__.items()

    def get(self, index, default=None):
        """
        Returns the influence object associated with the given index.

        :type index: int
        :type default: Any
        :rtype: Union[fntransform.FnTransform, None]
        """

        return self.__objects__.get(index, None)

    def index(self, influence):
        """
        Returns the index for the given influence.
        If no index is found then None is returned!


        :type influence: Any
        :rtype: int
        """

        try:

            # Check influence type
            #
            if isinstance(influence, string_types):

                influence = fntransform.FnTransform(influence)

            # Get associated value key
            #
            keys = list(self.__objects__.keys())
            values = list(self.__objects__.values())
            index = values.index(influence)

            return keys[index]

        except (ValueError, TypeError):

            return None

    def lastIndex(self):
        """
        Returns the last influence ID in this collection.

        :rtype: int
        """

        indices = list(self.keys())
        numIndices = len(indices)

        if numIndices > 0:

            return indices[-1]

        else:

            return -1

    def update(self, obj, **kwargs):
        """
        Copies the values from the supplied object to this collection.

        :type obj: dict
        :rtype: None
        """

        for key in sorted(obj.keys()):

            self.__setitem__(key, obj[key])

    def clear(self):
        """
        Removes all the influences from this collection.

        :rtype: None
        """

        self.__objects__.clear()
    # endregion


class AFnSkin(with_metaclass(ABCMeta, afnnode.AFnNode)):
    """
    Overload of AFnBase that outlines function set behaviour for DCC skinning.
    """

    # region Dunderscores
    __slots__ = ('_influences', '_clipboard')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Declare private variables
        #
        self._influences = Influences()
        self._clipboard = {}

        # Call parent method
        #
        super(AFnSkin, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def clipboard(self):
        """
        Getter method that returns the clipboard.

        :rtype: Dict[int, Dict[int, float]]
        """

        return self._clipboard
    # endregion

    # region Methods
    @classmethod
    @abstractmethod
    def create(cls, mesh):
        """
        Creates a skin and assigns it to the supplied shape.

        :type mesh: fnmesh.FnMesh
        :rtype: AFnSkin
        """

        pass

    @abstractmethod
    def transform(self):
        """
        Returns the transform node associated with this skin.

        :rtype: Any
        """

        pass

    @abstractmethod
    def shape(self):
        """
        Returns the shape node associated with this skin.

        :rtype: Any
        """

        pass

    @abstractmethod
    def intermediateObject(self):
        """
        Returns the intermediate object associated with this skin.

        :rtype: Any
        """

        pass

    @abstractmethod
    def iterVertices(self):
        """
        Returns a generator that yields vertex indices.

        :rtype: Iterator[int]
        """

        pass

    def vertices(self):
        """
        Returns a list of vertex indices.

        :rtype: List[int]
        """

        return list(self.iterVertices())

    def iterControlPoints(self, *indices, cls=Vector):
        """
        Returns a generator that yields the intermediate control points.
        If no arguments are supplied then all control points are yielded.

        :type indices: Union[int, List[int]]
        :type cls: Callable
        :rtype: Iterator[vector.Vector]
        """

        return fnmesh.FnMesh(self.intermediateObject()).iterVertices(*indices, cls=cls)

    def controlPoints(self, *indices, cls=Vector):
        """
        Returns the intermediate control points.
        If no arguments are supplied then all control points are returned.

        :type indices: Union[int, List[int]]
        :type cls: Callable
        :rtype: List[vector.Vector]
        """

        return list(self.iterControlPoints(*indices, cls=cls))

    def numControlPoints(self):
        """
        Evaluates the number of control points from this skin.

        :rtype: int
        """

        return fnmesh.FnMesh(self.intermediateObject()).numVertices()

    @abstractmethod
    def iterSelection(self):
        """
        Returns a generator that yields the selected vertex elements.

        :rtype: Iterator[int]
        """

        pass

    def selection(self):
        """
        Returns the selected vertex elements.

        :rtype: List[int]
        """

        return list(self.iterSelection())

    @abstractmethod
    def setSelection(self, vertices):
        """
        Updates the active selection with the supplied vertex elements.

        :type vertices: List[int]
        :rtype: None
        """

        pass

    @abstractmethod
    def iterSoftSelection(self):
        """
        Returns a generator that yields selected vertex-weight pairs.

        :rtype Iterator[Dict[int, float]]
        """

        pass

    def softSelection(self):
        """
        Returns a dictionary of the selected vertex-weight pairs.

        :rtype Dict[int, float]
        """

        return dict(self.iterSoftSelection())

    @abstractmethod
    def showColors(self):
        """
        Enables color feedback for the associated mesh.

        :rtype: None
        """

        pass

    @abstractmethod
    def hideColors(self):
        """
        Disable color feedback for the associated mesh.

        :rtype: None
        """

        pass

    def refreshColors(self):
        """
        Forces the vertex colour display to redraw.

        :rtype: None
        """

        pass

    @abstractmethod
    def iterInfluences(self):
        """
        Returns a generator that yields the influence id-objects pairs from this skin.

        :rtype: Iterator[Tuple[int, Any]]
        """

        pass

    def influences(self):
        """
        Returns the influence id-object pairs from this skin.

        :rtype: Influences
        """

        # Check if influences require updating
        #
        current = len(self._influences)

        if current != self.numInfluences():

            self._influences.clear()
            self._influences.update(dict(self.iterInfluences()))

        return self._influences

    def influenceNames(self):
        """
        Returns the influence names from this skin.

        :rtype: Dict[int, str]
        """

        return {influenceId: influence.name() for (influenceId, influence) in self.influences().items()}

    @abstractmethod
    def numInfluences(self):
        """
        Returns the number of influences in use by this skin.

        :rtype: int
        """

        pass

    @abstractmethod
    def addInfluence(self, *influences):
        """
        Adds an influence to this skin.

        :type influences: Union[Any, List[Any]]
        :rtype: None
        """

        pass

    @abstractmethod
    def removeInfluence(self, *influenceIds):
        """
        Removes an influence from this skin by id.

        :type influenceIds: Union[int, List[int]]
        :rtype: None
        """

        pass

    @abstractmethod
    def maxInfluences(self):
        """
        Returns the max number of influences for this skin.

        :rtype: int
        """

        pass

    @abstractmethod
    def setMaxInfluences(self, count):
        """
        Updates the max number of influences for this skin.

        :type count: int
        :rtype: None
        """

        pass

    @abstractmethod
    def selectInfluence(self, influenceId):
        """
        Changes the color display to the specified influence id.

        :type influenceId: int
        :rtype: None
        """

        pass

    def getUsedInfluenceIds(self, *indices):
        """
        Returns a list of active influence IDs from the specified vertices.
        If no vertices are supplied then all vertices are evaluated instead!

        :type indices: Union[int, List[int]]
        :rtype: List[int]
        """

        # Iterate through weights
        #
        influenceIds = set()

        for (vertexIndex, vertexWeights) in self.iterVertexWeights(*indices):

            influenceIds = influenceIds.union(set(vertexWeights.keys()))

        return list(influenceIds)

    def getUnusedInfluenceIds(self, *indices):
        """
        Returns a list of inactive influence IDs from the specified vertices.
        If no vertices are supplied then all vertices are evaluated instead!

        :type indices: Union[int, List[int]]
        :rtype: List[int]
        """

        return list(set(self.influences().keys()) - set(self.getUsedInfluenceIds(*indices)))

    def createInfluenceMap(self, otherSkin, influenceIds=None):
        """
        Creates an influence map for transferring weights from this skin to the other skin.
        An optional list of influence IDs can be supplied to simplify the map.

        :type otherSkin: AFnSkin
        :type influenceIds: Union[list, tuple, set]
        :rtype: Dict[int, int]
        """

        # Check if skin is valid
        #
        if not otherSkin.isValid():

            raise TypeError('createInfluenceMap() expects a valid skin (%s given)!' % type(otherSkin).__name__)

        # Check if influence IDs were supplied
        #
        influences = self.influences()

        if influenceIds is None:

            influenceIds = list(influences.keys())

        # Iterate through influences
        #
        otherInfluences = {influenceObject.name(): influenceId for (influenceId, influenceObject) in otherSkin.influences().items()}
        influenceMap = {}

        for influenceId in influenceIds:

            # Try and find a match for the influence name
            #
            influenceName = influences[influenceId].name()
            remappedId = otherInfluences.get(influenceName, None)

            if remappedId is not None:

                influenceMap[influenceId] = remappedId

            else:

                raise KeyError('Unable to find a matching ID for %s influence!' % influenceName)

        # Return influence map
        #
        log.debug('Successfully created %s influence map!' % influenceMap)
        return influenceMap

    def remapVertexWeights(self, vertexWeights, influenceMap):
        """
        Remaps the supplied vertex weights using the specified influence map.

        :type vertexWeights: Dict[int, Dict[int, float]]
        :type influenceMap: Dict[int, int]
        :rtype: Dict[int, Dict[int, float]]
        """

        # Check if arguments are valid
        #
        if not isinstance(vertexWeights, dict) or not isinstance(influenceMap, dict):

            raise TypeError('remapVertexWeights() expects a dict (%s given)!' % type(vertexWeights).__name__)

        # Reiterate through vertices
        #
        updates = {}

        for (vertexIndex, weights) in vertexWeights.items():

            # Iterate through vertex weights
            #
            updates[vertexIndex] = {}

            for (influenceId, weight) in weights.items():

                # Get remapped id and check if weights should be merged
                #
                newInfluenceId = influenceMap[influenceId]
                log.debug('Influence ID: %s, has been remapped to: %s' % (influenceId, newInfluenceId))

                if newInfluenceId in updates[vertexIndex]:

                    updates[vertexIndex][newInfluenceId] += weight

                else:

                    updates[vertexIndex][newInfluenceId] = weight

        return updates

    def getVerticesByInfluenceId(self, *influenceIds):
        """
        Returns a list of vertices associated with the supplied influence ids.
        This can be an expensive operation so use sparingly.

        :rtype: List[int]
        """

        # Iterate through vertices
        #
        vertexIndices = []

        for (vertexIndex, weights) in self.iterVertexWeights():

            # Check if weights contain influence ID
            #
            if any([influenceId in weights for influenceId in influenceIds]):

                vertexIndices.append(vertexIndex)

            else:

                continue

        return vertexIndices

    def findRoot(self):
        """
        Returns the skeleton root associated with this skin.

        :rtype: Any
        """

        # Find common path
        #
        influences = self.influences()
        commonPath = self.findCommonPath(*influences.values())

        if not stringutils.isNullOrEmpty(commonPath):

            strings = commonPath.split('/')
            return fnnode.FnNode(strings[0]).object()

        else:

            return None

    @abstractmethod
    def iterVertexWeights(self, *indices):
        """
        Returns a generator that yields vertex-weights pairs from this skin.
        If no vertex indices are supplied then all weights are yielded instead.

        :type indices: Union[int, List[int]]
        :rtype: Iterator[Tuple[int, Dict[int, float]]]
        """

        pass

    def vertexWeights(self, *indices):
        """
        Returns the weights for the supplied vertex indices.
        If no vertex indices are supplied then all weights are returned instead.

        :type indices: Union[int, List[int]]
        :rtype: Dict[int, Dict[int, float]]
        """

        return dict(self.iterVertexWeights(*indices))

    @abstractmethod
    def applyVertexWeights(self, vertexWeights):
        """
        Assigns the supplied vertex weights to this skin.

        :type vertexWeights: Dict[int, Dict[int, float]]
        :rtype: None
        """

        pass

    def copyWeights(self):
        """
        Copies the selected vertices to the clipboard.

        :rtype: None
        """

        self._clipboard = self.vertexWeights(*self.selection())

    def pasteWeights(self):
        """
        Pastes the clipboard to the selected vertices.

        :rtype: None
        """

        # Get active selection
        #
        selection = self.selection()
        numSelected = len(selection)

        numClipboard = len(self._clipboard)

        if numSelected == 0 or numClipboard == 0:

            return

        # Check which operation to perform:
        #
        vertices = {}

        if numSelected == numClipboard:

            # Reallocate clipboard values to updates
            #
            vertices = {vertexIndex: deepcopy(vertexWeights) for (vertexIndex, vertexWeights) in zip(selection, self._clipboard.values())}

        else:

            # Apply last set of weights to selected vertices
            #
            vertexWeights = list(self._clipboard.values())[-1]
            vertices = {vertexIndex: deepcopy(vertexWeights) for vertexIndex in selection}

        # Apply weights
        #
        self.applyVertexWeights(vertices)

    def pasteAveragedWeights(self):
        """
        Pastes an average of the clipboard to the selected vertices.

        :rtype: None
        """

        # Get active selection
        #
        selection = self.selection()
        numSelected = len(selection)

        numClipboard = len(self._clipboard)

        if numSelected == 0 or numClipboard == 0:

            return

        # Average all weights in clipboard
        #
        average = skinmath.averageWeights(*list(self._clipboard.values()), maintainMaxInfluences=True)
        updates = {vertexIndex: deepcopy(average) for vertexIndex in selection}

        return self.applyVertexWeights(updates)

    def slabPasteWeights(self, vertexIndices, mode=0):
        """
        Copies the supplied vertex indices to the nearest neighbour based on the specified mode.

        :type vertexIndices: List[int]
        :type mode: int
        :rtype: None
        """

        # Get selected vertices
        #
        numVertices = len(vertexIndices)

        if numVertices == 0:

            return

        # Check which method to use
        #
        mesh = fnmesh.FnMesh(self.intermediateObject())
        closestIndices = []

        log.debug('Getting closest vertices for %s.' % vertexIndices)

        if mode == 0:  # Closest point

            closestIndices = mesh.nearestVertices(*vertexIndices)

        elif mode == 1:  # Nearest neighbour

            closestIndices = mesh.nearestNeighbours(*vertexIndices)

        elif mode == 2:  # Along vertex normal

            pass

        else:

            raise TypeError('slabPasteWeights() expects a valid mode (%s given)!' % mode)

        # Check if lists are the same size
        #
        closestCount = len(closestIndices)
        log.debug('Using %s for closest vertices.' % closestIndices)

        if closestCount == numVertices:

            # Get vertex weights
            #
            log.debug('Pasting weights from %s to %s.' % (vertexIndices, closestIndices))
            vertexWeights = self.vertexWeights(*vertexIndices)

            # Compose new weights dictionary
            #
            updates = {closestIndex: vertexWeights[vertexIndex] for (vertexIndex, closestIndex) in zip(vertexIndices, closestIndices)}
            return self.applyVertexWeights(updates)

        else:

            log.warning('Unable to slab paste selection!')

    def mirrorVertexWeights(self, vertexIndices, pull=False, axis=0, tolerance=1e-3):
        """
        Returns a series of mirrored weights for the supplied vertex weights.

        :type vertexIndices: List[int]
        :type pull: bool
        :type axis: int
        :type tolerance: float
        :rtype: Dict[int, Dict[int, float]]
        """

        # Mirror the supplied vertex indices
        #
        mesh = fnmesh.FnMesh(self.intermediateObject())
        mirrorIndices = mesh.mirrorVertices(vertexIndices, axis=axis, tolerance=tolerance)

        # Mirror the found vertex pairs
        #
        vertexWeights = self.vertexWeights(*list(set.union(set(mirrorIndices.keys()), set(mirrorIndices.values()))))
        mirrorVertexWeights = {}

        for (vertexIndex, mirrorIndex) in mirrorIndices.items():

            isCenterSeam = (vertexIndex == mirrorIndex)
            log.debug(f'.vtx[{vertexIndex}] == .vtx[{mirrorIndex}]')

            if pull:

                mirrorVertexWeights[vertexIndex] = self.mirrorWeights(vertexWeights[mirrorIndex], isCenterSeam=isCenterSeam)

            else:

                mirrorVertexWeights[mirrorIndex] = self.mirrorWeights(vertexWeights[vertexIndex], isCenterSeam=isCenterSeam)

        return mirrorVertexWeights

    def mirrorWeights(self, weights, isCenterSeam=False):
        """
        Mirrors the influence IDs in the supplied vertex weight dictionary.

        :type weights: Dict[int, float]
        :type isCenterSeam: bool
        :rtype: Dict[int, float]
        """

        # Check value type
        #
        if not isinstance(weights, dict):

            raise TypeError(f'mirrorWeights() expects a dict ({type(weights).__name__} given)!')

        # Iterate through influences
        #
        influences = self.influences()
        otherInfluence = fnnode.FnNode()

        mirrorWeights = {}

        for influenceId in weights.keys():

            # Concatenate mirror name
            # Be sure to check for redundancy
            #
            influenceName = influences[influenceId].absoluteName()
            mirrorName = namingutils.mirrorName(influenceName)

            if influenceName == mirrorName:

                log.debug(f'No mirrored influence name found for {influenceName}.')
                mirrorWeights[influenceId] = weights[influenceId]

                continue

            # Check if mirrored influence name exists
            #
            success = otherInfluence.trySetObject(mirrorName)

            if not success:

                log.debug(f'No mirrored influence name found for {influenceName}.')
                continue

            # Check if mirror name is in list
            #
            log.debug(f'Checking if {mirrorName} exists in influence list...')
            mirrorId = influences.index(otherInfluence.object())

            if mirrorId is not None:

                # Check if this is for a center seam
                #
                if isCenterSeam:

                    log.debug(f'Splitting {mirrorName} vertex weights with {influenceName} influence.')

                    weight = (weights.get(influenceId, 0.0) + weights.get(mirrorId, 0.0)) / 2.0
                    mirrorWeights[influenceId] = weight
                    mirrorWeights[mirrorId] = weight

                else:

                    log.debug(f'Trading {mirrorName} vertex weights for {influenceName} influence.')
                    mirrorWeights[mirrorId] = weights[influenceId]

            else:

                log.warning(f'Unable to find a matching mirrored influence for {influenceName}.')
                mirrorWeights[influenceId] = weights[influenceId]

        # Return mirrored vertex weights
        #
        return mirrorWeights

    def relaxVertices(self, vertexIndices):
        """
        Relaxes the supplied vertices.

        :type vertexIndices: List[int]
        :rtype: None
        """

        # Evaluate supplied vertices
        #
        numVertices = len(vertexIndices)

        if numVertices == 0:

            return

        # Iterate through vertices
        #
        mesh = fnmesh.FnMesh(self.shape())
        maxInfluences = self.maxInfluences()

        updates = {}

        for vertexIndex in vertexIndices:

            # Get connected vertices
            #
            connectedVertices = list(mesh.iterConnectedVertices(vertexIndex))
            connectedVertices.append(vertexIndex)

            log.debug(f'Relaxing vertex weights from: {connectedVertices}')

            # Average vertex weights
            #
            influenceIds = list(self.vertexWeights(vertexIndex)[vertexIndex].keys())
            vertices = {connectedIndex: {influenceId: influenceWeight for (influenceId, influenceWeight) in connectedWeights.items() if influenceId in influenceIds} for (connectedIndex, connectedWeights) in self.iterVertexWeights(*connectedVertices)}

            vertexWeights = skinmath.averageWeights(*list(vertices.values()), maxInfluences=maxInfluences)
            log.debug(f'Relaxed vertex weights: {vertexWeights}')

            updates[vertexIndex] = vertexWeights

        # Apply averaged result to skin cluster
        #
        return self.applyVertexWeights(updates)

    def blendVertices(self, vertexIndices):
        """
        Blends the supplied vertices.

        :type vertexIndices: List[int]
        :rtype: None
        """

        # Evaluate supplied vertices
        #
        numVertices = len(vertexIndices)

        if numVertices == 0:

            return

        # Iterate through vertices
        #
        mesh = fnmesh.FnMesh(self.shape())
        maxInfluences = self.maxInfluences()

        updates = {}

        for vertexIndex in vertexIndices:

            # Get connected vertices
            #
            connectedVertices = list(mesh.iterConnectedVertices(vertexIndex))
            log.debug(f'Blending vertex weights from: {connectedVertices}')

            # Average vertex weights
            #
            vertices = self.vertexWeights(*connectedVertices)

            vertexWeights = skinmath.averageWeights(*list(vertices.values()), maxInfluences=maxInfluences)
            log.debug(f'Blended vertex weights: {vertexWeights}')

            updates[vertexIndex] = vertexWeights

        # Apply averaged result to skin cluster
        #
        return self.applyVertexWeights(updates)

    def blendBetweenVertices(self, vertexIndices, blendByDistance=False):
        """
        Blends between the supplied vertex pairs using the shortest path.

        :type vertexIndices: List[int]
        :type blendByDistance: bool
        :rtype: None
        """

        # Get selected vertices
        #
        numVertices = len(vertexIndices)

        if numVertices < 2:

            return

        # Iterate through vertex pairs
        #
        for i in range(numVertices - 1):

            # Get start and end weights
            #
            startVertex = vertexIndices[i]
            endVertex = vertexIndices[i+1]

            self.blendBetweenTwoVertices(startVertex, endVertex, blendByDistance=blendByDistance)

    def blendBetweenTwoVertices(self, startVertex, endVertex, blendByDistance=False):
        """
        Blends between the start and end vertices using the shortest path.

        :type startVertex: int
        :type endVertex: int
        :type blendByDistance: bool
        :rtype: None
        """

        # Evaluate path between vertices
        #
        fnMesh = fnmesh.FnMesh(self.shape())

        path = fnMesh.shortestPathBetweenTwoVertices(startVertex, endVertex)
        pathLength = len(path)

        if pathLength == 2:

            return

        # Evaluate max parameter
        #
        maxParam = 0.0
        param = 0.0

        if blendByDistance:

            maxParam = fnMesh.distanceBetweenVertices(*path)

        else:

            maxParam = float(pathLength - 1)

        # Iterate through elements
        #
        fnMesh = fnmesh.FnMesh(self.shape())
        points = fnMesh.getVertices(*path)

        maxInfluences = self.maxInfluences()
        vertexWeights = self.vertexWeights(startVertex, endVertex)
        startWeights, endWeights = vertexWeights[startVertex], vertexWeights[endVertex]

        updates = {}

        for (i, vertexIndex) in enumerate(path[1:-1]):

            # Get parameter
            #
            if blendByDistance:

                param += points[i].distanceBetween(points[i+1])

            else:

                param = float(i + 1)

            # Weighted average start and end weights
            #
            percent = param / maxParam

            updates[vertexIndex] = skinmath.weightedAverageWeights(
                startWeights,
                endWeights,
                percent=percent,
                maxInfluences=maxInfluences
            )

        # Apply weights
        #
        self.applyVertexWeights(updates)

    def pruneVertices(self, vertexIndices, tolerance=1e-3):
        """
        Prunes any influences below the specified tolerance.

        :type vertexIndices: List[int]
        :type tolerance: float
        :rtype: None
        """

        vertices = self.vertexWeights(*vertexIndices)
        prunedVertices = {vertexIndex: skinmath.pruneWeights(vertexWeights, tolerance=tolerance) for (vertexIndex, vertexWeights) in vertices.items()}
        updates = {vertexIndex: prunedVertices[vertexIndex] for vertexIndex in vertexIndices if len(vertices[vertexIndex]) != len(prunedVertices[vertexIndex])}

        self.applyVertexWeights(updates)

    def inverseDistanceWeights(self, vertexWeights, distances, power=2.0):
        """
        Averages supplied vertex weights based on the inverse distance.

        :type vertexWeights: Dict[int,Dict[int, float]]
        :type distances: list[float]
        :type power: float
        :rtype: Dict[int, float]
        """

        # Check value types
        #
        numVertices = len(vertexWeights)
        numDistances = len(distances)

        if numVertices != numDistances:

            raise TypeError('inverseDistanceVertexWeights() expects identical length lists!')

        # Merge dictionary keys using null values
        #
        inverseWeights = skinmath.mergeWeights(*list(vertexWeights.values()))
        influenceIds = inverseWeights.keys()

        # Iterate through influences
        #
        for influenceId in influenceIds:

            # Collect weight values
            #
            weights = [x.get(influenceId, 0.0) for x in vertexWeights.values()]

            # Zip list and evaluate in parallel
            #
            numerator = 0.0
            denominator = 0.0

            for (weight, distance) in zip(weights, distances):

                clampedDistance = distance if distance > 0.0 else 1e-3
                numerator += weight / pow(clampedDistance, power)
                denominator += 1.0 / pow(clampedDistance, power)

            # Assign average to updates
            #
            inverseWeights[influenceId] = float(numerator / denominator)

        # Return normalized weights
        #
        log.debug(f'Inverse Distance: {inverseWeights}')
        return skinmath.normalizeWeights(inverseWeights)

    def barycentricWeights(self, vertexIndices, baryCoords):
        """
        Returns the barycentric average for the specified vertices.

        :type vertexIndices: List[int]
        :type baryCoords list[float, float, float]
        :rtype: Dict[int, float]
        """

        # Check if list size mismatch
        #
        numVertices = len(vertexIndices)
        numBary = len(baryCoords)

        if numVertices != numBary:

            raise TypeError('barycentricWeights() list sizes must be identical!')

        # Merge dictionary keys using null values
        #
        vertexWeights = self.vertexWeights(*vertexIndices)

        baryWeights = skinmath.mergeWeights(*list(vertexWeights.values()))
        influenceIds = baryWeights.keys()

        # Iterate through influences
        #
        for influenceId in influenceIds:

            # Collect weight values
            #
            weight = 0.0

            for (vertexIndex, baryCoord) in zip(vertexIndices, baryCoords):

                weight += vertexWeights[vertexIndex].get(influenceId, 0.0) * baryCoord

            # Assign average to updates
            #
            baryWeights[influenceId] = weight

        # Return normalized weights
        #
        log.debug(f'Barycentric Average: {baryWeights}')
        return skinmath.normalizeWeights(baryWeights)

    def bilinearWeights(self, vertexIndices, biCoords):
        """
        Returns the bilinear average for the specified vertices.

        :type vertexIndices: Tuple[int, int, int, int]
        :type biCoords: Tuple[int, int]
        :rtype: Dict[int, float]
        """

        u, v = biCoords
        v0, v1, v2, v3 = vertexIndices
        vertexWeights = self.vertexWeights(*vertexIndices)

        w0 = skinmath.weightedAverageWeights(vertexWeights[v0], vertexWeights[v1], percent=u)
        w1 = skinmath.weightedAverageWeights(vertexWeights[v3], vertexWeights[v2], percent=u)
        w2 = skinmath.weightedAverageWeights(w0, w1, percent=v)

        return w2

    @abstractmethod
    def resetPreBindMatrices(self):
        """
        Resets the pre-bind matrices on the associated joints.

        :rtype: None
        """

        pass

    @abstractmethod
    def resetIntermediateObject(self):
        """
        Resets the control points on the associated intermediate object.

        :rtype: None
        """

        pass
    # endregion
