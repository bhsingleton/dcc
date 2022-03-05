import os
import json

from abc import ABCMeta, abstractmethod
from six import with_metaclass, integer_types
from six.moves import collections_abc
from copy import deepcopy
from collections import OrderedDict

from dcc import fnnode, fnmesh
from dcc.abstract import afnbase, afnnode
from dcc.naming import namingutils
from dcc.math import linearalgebra

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

    def __getitem__(self, index):
        """
        Private method that returns an indexed influence.

        :type index: int
        :rtype: Union[om.MObject, pymxs.MXSWrapperBase]
        """

        # Check key type
        #
        if isinstance(index, integer_types):

            return self.get(index)

        else:

            raise TypeError('__getitem__() expects an int (%s given)!' % type(index).__name__)

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

        return iter(self._influences)

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

    def get(self, index, default=None):
        """
        Returns the influence object associated with the given index.

        :type index: int
        :type default: Any
        :rtype: Union[om.MObject, pymxs.MXSWrapperBase]
        """

        handle = self._influences.get(index, 0)
        return fnnode.FnNode.getNodeByHandle(handle)

    def index(self, influence):
        """
        Returns the index for the given influence.
        If no index is found then none is returned!

        :type influence: Union[str, om.MObject, pymxs.MXSWrapperBase]
        :rtype: int
        """

        handle = fnnode.FnNode(influence).handle()
        return {handle: index for (index, handle) in self.items()}.get(handle, None)

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

        self._influences.clear()


class AFnSkin(with_metaclass(ABCMeta, afnnode.AFnNode)):
    """
    Overload of AFnBase that outlines function set behaviour for DCC skinning.
    """

    __slots__ = ('_influences', '_clipboard')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.
        """

        # Declare private variables
        #
        self._influences = Influences()
        self._clipboard = {}

        # Call parent method
        #
        super(AFnSkin, self).__init__(*args, **kwargs)

    def __getstate__(self):
        """
        Private method that returns an object state for this instance.

        :rtype: dict
        """

        return {
            'name': self.name(),
            'influences': self.influenceNames(),
            'maxInfluences': self.maxInfluences(),
            'vertices': self.vertexWeights(),
            'points': self.controlPoints()
        }

    @abstractmethod
    def shape(self):
        """
        Returns the shape node associated with the deformer.

        :rtype: Any
        """

        pass

    @abstractmethod
    def intermediateObject(self):
        """
        Returns the intermediate object associated with the deformer.

        :rtype: Any
        """

        pass

    @property
    def clipboard(self):
        """
        Getter method that returns the clipboard.

        :rtype: Dict[int,Dict[int, float]]
        """

        return self._clipboard

    @abstractmethod
    def iterVertices(self):
        """
        Returns a generator that yields all vertex indices.

        :rtype: iter
        """

        pass

    def vertices(self):
        """
        Returns a list of vertex indices.

        :rtype: List[int]
        """

        return list(self.iterVertices())

    def iterControlPoints(self, *args):
        """
        Returns a generator that yields control points.
        If no arguments are supplied then all control points are yielded.

        :rtype: iter
        """

        return fnmesh.FnMesh(self.intermediateObject()).iterVertices(*args)

    def controlPoints(self, *args):
        """
        Returns control points.
        If no arguments are supplied then all control points are returned.

        :rtype: list
        """

        return fnmesh.FnMesh(self.intermediateObject()).vertices(*args)

    def numControlPoints(self):
        """
        Evaluates the number of control points from this skin.

        :rtype: int
        """

        return fnmesh.FnMesh(self.intermediateObject()).numVertices()

    @abstractmethod
    def iterSelection(self):
        """
        Returns a generator that yields the selected vertex indices.

        :rtype: iter
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
        Returns a generator that yields selected vertex and soft value pairs.

        :rtype iter
        """

        pass

    def softSelection(self):
        """
        Returns a dictionary of selected vertex and soft value pairs.

        :rtype Dict[int, float]
        """

        return OrderedDict(self.iterSoftSelection())

    @abstractmethod
    def showColors(self):
        """
        Enables color feedback for the associated shape.

        :rtype: None
        """

        pass

    @abstractmethod
    def hideColors(self):
        """
        Disable color feedback for the associated shape.

        :rtype: None
        """

        pass

    def invalidateColors(self):
        """
        Forces the vertex colour display to redraw.

        :rtype: None
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
            self._influences.update(dict(self.iterInfluences()))

        return self._influences

    def influenceNames(self):
        """
        Returns all of the influence names from this deformer.

        :rtype: Dict[int,str]
        """

        influences = self.influences()
        return {influenceId: influences(influenceId).name() for influenceId in influences}

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

    @abstractmethod
    def selectInfluence(self, influenceId):
        """
        Changes the color display to the specified influence id.

        :type influenceId: int
        :rtype: None
        """

        pass

    def getUsedInfluenceIds(self, *args):
        """
        Returns a list of used influence IDs.
        An optional list of vertices can used to narrow down this search.

        :rtype: List[int]
        """

        # Iterate through weights
        #
        influenceIds = set()

        for (vertexIndex, vertexWeights) in self.iterVertexWeights(*args):

            influenceIds = influenceIds.union(set(vertexWeights.keys()))

        return list(influenceIds)

    def getUnusedInfluenceIds(self, *args):
        """
        Returns a list of unused influence IDs.
        An optional list of vertices can used to narrow down this search.

        :rtype: List[int]
        """

        return list(set(self.influences().keys()) - set(self.getUsedInfluenceIds(*args)))

    def createInfluenceMap(self, otherSkin, influenceIds=None):
        """
        Creates an influence map for transferring weights from this instance to the supplied skin.
        An optional list of influence IDs can be used to simplify the binder.

        :type otherSkin: AFnSkin
        :type influenceIds: Union[list, tuple, set]
        :rtype: Dict[int,int]
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
        otherInfluences = otherSkin.influences()
        influenceMap = {}

        for influenceId in influenceIds:

            # Try and find a match for the influence name
            #
            influenceName = influences(influenceId).name()
            remappedId = otherInfluences.index(influenceName)

            if remappedId is not None:

                influenceMap[influenceId] = remappedId

            else:

                raise KeyError('Unable to find a matching ID for %s influence!' % influenceName)

        # Return influence map
        #
        log.debug('Successfully created %s influence binder.' % influenceMap)
        return influenceMap

    def remapVertexWeights(self, vertexWeights, influenceMap):
        """
        Remaps the supplied vertex weights using the specified influence map.

        :type vertexWeights: Dict[int,Dict[int, float]]
        :type influenceMap: Dict[int,int]
        :rtype: Dict[int,Dict[int, float]]
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

    def getVerticesByInfluenceId(self, *args):
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
            if any([x in weights for x in args]):

                vertexIndices.append(vertexIndex)

            else:

                continue

        return vertexIndices

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
        # It is possible for commonprefix to return an incomplete node name!
        #
        strings = [x for x in commonPrefix.split('|') if fnnode.FnNode.doesNodeExist(x)]
        numStrings = len(strings)

        fnNode = fnnode.FnNode(strings[-1])
        root = fnNode.object()

        # Check number of strings
        #
        if numStrings == 0:

            return root

        # Walk up hierarchy until we find the root joint
        #
        while True:

            # Check if this joint has a parent
            #
            if not fnNode.hasParent():

                return root

            # Check if parent is still a joint
            #
            parent = fnNode.parent()
            fnNode.setObject(parent)

            if not fnNode.isJoint():

                return root

            else:

                root = parent

    @abstractmethod
    def iterVertexWeights(self, *args):
        """
        Returns a generator that yields weights for the supplied vertex indices.
        If no vertex indices are supplied then all weights are yielded instead.

        :rtype: iter
        """

        pass

    def vertexWeights(self, *args):
        """
        Returns the weights for the supplied vertex indices.
        If no vertex indices are supplied then all weights are returned instead.

        :rtype: Dict[int,Dict[int, float]]
        """

        return dict(self.iterVertexWeights(*args))

    def setWeights(self, weights, target, source, amount, falloff=1.0):
        """
        Sets the supplied target ID to the specified amount while preserving normalization.

        :type weights: Dict[int, float]
        :type target: int
        :type source: List[int]
        :type amount: float
        :type falloff: float
        :rtype: Dict[int, float]
        """

        # Check weights type
        #
        if not isinstance(weights, dict):

            raise TypeError('setWeights() expects a dict (%s given)!' % type(weights).__name__)

        # Check source and target influences
        #
        if not isinstance(target, int) or not isinstance(source, list):

            raise TypeError('setWeights() expects a valid target and source influences!')

        # Check amount type
        #
        if not isinstance(amount, float):

            raise TypeError('setWeights() expects a valid amount (%s given)!' % type(amount).__name__)

        # Copy weights to manipulate
        #
        newWeights = deepcopy(weights)

        softAmount = amount * falloff
        total = sum([weights.get(x, 0.0) for x in source])

        log.debug('%s weights available to redistribute.' % total)

        # Check if influence exists on vertex
        #
        influenceIds = newWeights.keys()
        numInfluences = len(influenceIds)

        maxInfluences = self.maxInfluences()

        if (target in influenceIds) or (target not in influenceIds and numInfluences < maxInfluences):

            # Determine redistribution method:
            # If amount is less than current then give those weights back to the source list
            # If amount is greater than current then take weights from the source list
            #
            current = newWeights.get(target, 0.0)

            if softAmount < current and 0.0 < total:

                # Redistribute target weight to source influences
                #
                diff = current - softAmount

                for (influenceId, weight) in newWeights.items():

                    # Check if influence is from source
                    #
                    if influenceId in source:

                        # Apply percentage of difference to influence
                        #
                        percent = weight / total
                        newWeight = weight + (diff * percent)

                        newWeights[influenceId] = newWeight

                    else:

                        continue

                # Set target to amount
                #
                newWeights[target] = current - diff

            elif softAmount > current and 0.0 < total:

                # Make sure amount has not exceeded total
                #
                diff = softAmount - current

                if diff >= total:

                    log.debug('Insufficient weights to pull from, clamping amount to: %s' % total)
                    diff = total

                # Redistribute source weights to target influences
                #
                for (influenceId, weight) in newWeights.items():

                    # Check if influence is from source
                    #
                    if influenceId in source:

                        # Reduce influence based on percentage of difference
                        #
                        percent = weight / total
                        newWeight = weight - (diff * percent)

                        newWeights[influenceId] = newWeight

                    else:

                        continue

                # Set target to accumulated amount
                #
                newWeights[target] = current + diff

            else:

                pass

        elif target not in influenceIds and numInfluences >= maxInfluences:

            # Check if all influences are being replaced
            #
            if linearalgebra.isClose(amount, total, abs_tol=1e-06):

                newWeights = {target: 1.0}

            elif amount == 0.0:

                log.debug('No weights available to redistribute!')

            else:

                log.warning('Cannot exceed max influences!')

        else:

            raise TypeError('Unable to set vertex weights using supplied arguments!')

        # Return updated vertex weights
        #
        return newWeights

    def scaleWeights(self, weights, target, source, percent, falloff=1.0):
        """
        Scales the supplied target ID to the specified amount while preserving normalization.

        :type weights: Dict[int, float]
        :type target: int
        :type source: List[int]
        :type percent: float
        :type falloff: float
        :rtype: Dict[int, float]
        """

        # Get amount to redistribute
        #
        current = weights.get(target, 0.0)
        amount = current + ((current * percent) * falloff)

        # Set vertex weight
        #
        log.debug('Changing influence ID: %s, from %s to %s.' % (target, current, amount))
        return self.setWeights(weights, target, source, amount)

    def incrementWeights(self, weights, target, source, increment, falloff=1.0):
        """
        Increments the supplied target ID to the specified amount while preserving normalization.

        :type weights: Dict[int, float]
        :type target: int
        :type source: List[int]
        :type increment: float
        :type falloff: float
        :rtype: Dict[int, float]
        """

        # Get amount to redistribute
        #
        current = weights.get(target, 0.0)
        amount = current + (increment * falloff)

        # Set vertex weight
        #
        log.debug('Changing influence ID: %s, from %s to %s.' % (target, current, amount))
        return self.setWeights(weights, target, source, amount)

    def removeZeroWeights(self, weights):
        """
        Removes any zeroes from the supplied weights.

        :type weights: Dict[int, float]
        :rtype: Dict[int, float]
        """

        return {influenceId: weight for (influenceId, weight) in weights.items() if not linearalgebra.isClose(0.0, weight)}

    def isNormalized(self, weights):
        """
        Evaluates if the supplied weights have been normalized.

        :type weights: Dict[int, float]
        :rtype: bool
        """

        # Check value type
        #
        if not isinstance(weights, dict):

            raise TypeError('isNormalized() expects a dict (%s given)!' % type(weights).__name__)

        # Check influence weight total
        #
        total = sum([weight for (influenceId, weight) in weights.items()])
        log.debug('Supplied influence weights equal %s.' % total)

        return linearalgebra.isClose(1.0, total)

    def normalizeWeights(self, weights, maintainMaxInfluences=True):
        """
        Normalizes the supplied vertex weights.

        :type maintainMaxInfluences: bool
        :type weights: Dict[int, float]
        :rtype: Dict[int, float]
        """

        # Check value type
        #
        if not isinstance(weights, dict):

            raise TypeError('normalizeWeights() expects a dict (%s given)!' % type(weights).__name__)

        # Check if influences should be pruned
        #
        if maintainMaxInfluences:

            weights = self.pruneWeights(weights)

        # Check if weights have already been normalized
        #
        isNormalized = self.isNormalized(weights)

        if isNormalized:

            log.debug('Vertex weights have already been normalized.')
            return weights

        # Get total weight we can normalize
        #
        total = sum(weights.values())

        if total == 0.0:

            raise TypeError('Cannot normalize influences from zero weights!')

        else:

            # Calculate adjusted scale factor
            #
            scale = 1.0 / total

            for (influenceId, weight) in weights.items():

                normalized = (weight * scale)
                weights[influenceId] = normalized

                log.debug(
                    'Scaling influence ID: {index}, from {weight} to {normalized}'.format(
                        index=influenceId,
                        weight=weight,
                        normalized=normalized
                    )
                )

        return weights

    def pruneWeights(self, weights):
        """
        Prunes the supplied vertex weights to meet the maximum number of weighted influences.

        :type weights: Dict[int, float]
        :rtype: Dict[int, float]
        """

        # Check value type
        #
        if not isinstance(weights, dict):

            raise TypeError('pruneWeights() expects a dict (%s given)!' % type(weights).__name__)

        # Check if any influences have dropped below limit
        #
        influences = self.influences()

        for (influenceId, weight) in weights.items():

            # Check if influence weight is below threshold
            #
            if linearalgebra.isClose(0.0, weight) or influences[influenceId] is None:

                weights[influenceId] = 0.0

            else:

                log.debug('Skipping influence ID: %s' % influenceId)

        # Check if influences have exceeded max allowances
        #
        numInfluences = len(weights)
        maxInfluences = self.maxInfluences()

        if numInfluences > maxInfluences:

            # Order influences from lowest to highest
            #
            orderedInfluences = sorted(weights, key=weights.get, reverse=False)

            # Replace surplus influences with zero values
            #
            diff = numInfluences - maxInfluences

            for i in range(diff):

                influenceId = orderedInfluences[i]
                weights[influenceId] = 0.0

        else:

            log.debug('Vertex weights have not exceeded max influences.')

        # Return dictionary changes
        #
        return weights

    def averageWeights(self, *args, **kwargs):
        """
        Averages the supplied vertex weights.
        By default maintain max influences is enabled.

        :key maintainMaxInfluences: bool
        :rtype: Dict[int, float]
        """

        # Iterate through vertices
        #
        average = {}

        for arg in args:

            # Check argument type
            #
            if not isinstance(arg, dict):

                continue

            # Iterate through copied weights
            #
            for (influenceId, vertexWeight) in arg.items():

                # Check if influence key already exists
                #
                if influenceId not in average:

                    average[influenceId] = arg[influenceId]

                else:

                    average[influenceId] += arg[influenceId]

        # Return normalized result
        #
        return self.normalizeWeights(average, **kwargs)

    def weightedAverageWeights(self, startWeights, endWeights, percent=0.5):
        """
        Averages supplied vertex weights based on a normalized percentage.

        :type startWeights: dict
        :type endWeights: dict
        :type percent: float
        :rtype: Dict[int, float]
        """

        # Check percentage type
        #
        if not isinstance(percent, (int, float)):

            raise TypeError('weightedAverageWeights() expects a float (%s given)!' % type(percent).__name__)

        # Merge dictionary keys using null values
        #
        weights = self.mergeDictionaries(startWeights, endWeights)
        influenceIds = weights.keys()

        for influenceId in influenceIds:

            # Get weight values
            #
            startWeight = startWeights.get(influenceId, 0.0)
            endWeight = endWeights.get(influenceId, 0.0)

            # Average weights
            #
            weight = (startWeight * (1.0 - percent)) + (endWeight * percent)
            weights[influenceId] = weight

        # Return normalized weights
        #
        return self.normalizeWeights(weights)

    @abstractmethod
    def applyVertexWeights(self, vertices):
        """
        Assigns the supplied vertex weights to this deformer.

        :type vertices: Dict[int,Dict[int, float]]
        :rtype: None
        """

        pass

    @staticmethod
    def mergeDictionaries(*args):
        """
        Combines any number of dictionaries together with null values.

        :rtype: dict
        """

        # Iterate through arguments
        #
        keys = set()

        for arg in args:

            keys = keys.union(set(arg.keys()))

        return {key: 0.0 for key in keys}

    def inverseDistanceWeights(self, vertexWeights, distances):
        """
        Averages supplied vertex weights based on the inverse distance.

        :type vertexWeights: Dict[int,Dict[int, float]]
        :type distances: list[float]
        :rtype: Dict[int, float]
        """

        # Check value types
        #
        numVertices = len(vertexWeights)
        numDistances = len(distances)

        if numVertices != numDistances:

            raise TypeError('inverseDistanceVertexWeights() expects identical length lists!')

        # Check for zero distance
        #
        index = distances.index(0.0) if 0.0 in distances else None

        if index is not None:

            log.debug('Zero distance found in %s' % distances)
            return vertexWeights[index]

        # Merge dictionary keys using null values
        #
        weights = self.mergeDictionaries(*list(vertexWeights.values()))
        influenceIds = weights.keys()

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

            for weight, distance in zip(weights, distances):

                numerator += weight / pow(distance, 2.0)
                denominator += 1.0 / pow(distance, 2.0)

            # Assign average to updates
            #
            weights[influenceId] = float(numerator / denominator)

        # Return normalized weights
        #
        log.debug('Inverse Distance: %s' % weights)
        return weights

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

        weights = self.mergeDictionaries(*list(vertexWeights.values()))
        influenceIds = weights.keys()

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
            weights[influenceId] = weight

        # Return normalized weights
        #
        log.debug('Barycentric Average: %s' % weights)
        return self.normalizeWeights(weights)

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

            # Iterate through vertices
            #
            vertexWeights = self._clipboard.values()[-1]
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
        average = self.averageWeights(*list(self._clipboard.values()), maintainMaxInfluences=True)
        updates = {vertexIndex: deepcopy(average) for vertexIndex in selection}

        return self.applyVertexWeights(updates)

    def slabPasteWeights(self, vertexIndices, mode=0):
        """
        Copies the supplied vertex indices to the nearest neighbour.

        :type vertexIndices: List[int]
        :type mode: int
        :rtype: None
        """

        pass

    def mirrorVertexWeights(self, vertexIndices, pull=False, axis=0, tolerance=1e-3):
        """
        Returns a series of mirrored weights for the supplied vertex weights.

        :type vertexIndices: List[int]
        :type pull: bool
        :type axis: int
        :type tolerance: float
        :rtype: Dict[int,Dict[int, float]]
        """

        # Mirror the supplied vertex indices
        #
        fnMesh = fnmesh.FnMesh(self.intermediateObject())
        mirrorIndices = fnMesh.mirrorVertices(vertexIndices, axis=axis, tolerance=tolerance)

        # Mirror the found vertex pairs
        #
        vertexWeights = self.vertexWeights(*list(set.union(set(mirrorIndices.keys()), set(mirrorIndices.values()))))
        mirrorVertexWeights = {}

        for (vertexIndex, mirrorIndex) in mirrorIndices.items():

            isCenterSeam = (vertexIndex == mirrorIndex)
            log.debug('.vtx[%s] == .vtx[%s]' % (vertexIndex, mirrorIndex))

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

            raise TypeError('mirrorWeights() expects a dict (%s given)!' % type(weights).__name__)

        # Iterate through influences
        #
        influences = self.influences()
        mirrorWeights = {}

        for influenceId in weights.keys():

            # Concatenate mirror name
            # Be sure to check for redundancy
            #
            influenceName = influences(influenceId).name()
            mirrorName = namingutils.mirrorName(influenceName)

            if influenceName == mirrorName:

                log.debug('No mirrored influence name found for %s.' % influenceName)

                mirrorWeights[influenceId] = weights[influenceId]
                continue

            # Check if mirror name is in list
            #
            log.debug('Checking if %s exists in influence list...' % mirrorName)
            mirrorId = influences.index(mirrorName)

            if mirrorId is not None:

                # Check if this is for a center seam
                #
                if isCenterSeam:

                    log.debug('Splitting %s vertex weights with %s influence.' % (mirrorName, influenceName))

                    weight = (weights.get(influenceId, 0.0) + weights.get(mirrorId, 0.0)) / 2.0
                    mirrorWeights[influenceId] = weight
                    mirrorWeights[mirrorId] = weight

                else:

                    log.debug('Trading %s vertex weights for %s influence.' % (mirrorName, influenceName))
                    mirrorWeights[mirrorId] = weights[influenceId]

            else:

                log.warning('Unable to find a matching mirrored influence for %s.' % influenceName)
                mirrorWeights[influenceId] = weights[influenceId]

        # Return mirrored vertex weights
        #
        return mirrorWeights

    def blendVertices(self, vertexIndices):
        """
        Blends the selected vertices.

        :type vertexIndices: List[int]
        :rtype: None
        """

        # Check number of vertices
        #
        numVertices = len(vertexIndices)

        if numVertices == 0:

            return

        # Iterate through vertices
        #
        fnMesh = fnmesh.FnMesh(self.shape())
        updates = {}

        for vertexIndex in vertexIndices:

            # Get connected vertices
            #
            connectedVertices = list(fnMesh.iterConnectedVertices(vertexIndex))
            log.debug('Averaging vertex weights from %s.' % connectedVertices)

            # Average vertex weights
            #
            vertices = self.vertexWeights(*connectedVertices)

            vertexWeights = self.averageWeights(*list(vertices.values()))
            log.debug('%s averaged from connected vertices.' % vertexWeights)

            updates[vertexIndex] = vertexWeights

        # Apply averaged result to skin cluster
        #
        return self.applyVertexWeights(updates)

    def blendBetweenVertices(self, vertexIndices, blendByDistance=False):
        """
        Blends between the supplied vertices using the shortest path.

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
        points = fnMesh.vertices(*path)

        vertexWeights = self.vertexWeights(startVertex, endVertex)
        startWeights, endWeights = vertexWeights[startVertex], vertexWeights[endVertex]

        updates = {}

        for (i, vertexIndex) in enumerate(path[1:-1]):

            # Get parameter
            #
            if blendByDistance:

                param += fnMesh.distanceBetween(points[i], points[i+1])

            else:

                param = float(i + 1)

            # Weighted average start and end weights
            #
            percent = param / maxParam
            updates[vertexIndex] = self.weightedAverageWeights(startWeights, endWeights, percent=percent)

        # Apply weights
        #
        self.applyVertexWeights(updates)

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

    def saveWeights(self, filePath):
        """
        Saves the skin weights to the specified file path.

        :type filePath: str
        :rtype: None
        """

        with open(filePath, 'w') as jsonFile:

            json.dump(self.__getstate__(), jsonFile, indent=4, sort_keys=True)

    def loadWeights(self, filePath):
        """
        Loads the skin weights from the specified file path.

        :type filePath: str
        :rtype: dict
        """

        with open(filePath, 'r') as jsonFile:

            return json.load(jsonFile)
