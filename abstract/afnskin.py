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

        handle = fnnode.FnNode(influence).handle()
        return {handle: index for (index, handle) in self.items()}.get(handle, None)

    def lastIndex(self):
        """
        Returns the last influence ID in this collection.

        :rtype: int
        """

        return list(self.keys())[-1]

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
            'vertices': self.weights(),
            'points': self.controlPoints()
        }

    def range(self, *args):
        """
        Returns a generator for yielding a range of numbers.
        Overload this if your DCC uses one-based arrays.

        :rtype: iter
        """

        return range(*args)

    def enumerate(self, items):
        """
        Returns a generator for enumerating a list of items.
        Overload this if your DCC uses one-based arrays.

        :rtype: iter
        """

        return enumerate(items)

    @abstractmethod
    def shape(self):
        """
        Returns the shape node associated with the deformer.

        :rtype: Any
        """

        pass

    @property
    def clipboard(self):
        """
        Getter method that returns the clipboard.

        :rtype: dict[int:dict[int:float]]
        """

        return self._clipboard

    @abstractmethod
    def controlPoint(self, vertexIndex):
        """
        Returns the control point for the specified vertex.

        :type vertexIndex: int
        :rtype: list[float, float, float]
        """

        pass

    def iterControlPoints(self, *args):
        """
        Returns a generator that yields control points.
        If no arguments are supplied then all control points are yielded.

        :rtype: iter
        """

        # Inspect arguments
        #
        numArgs = len(args)

        if numArgs == 0:

            args = self.range(self.numControlPoints())

        # Iterate through arguments
        #
        for arg in args:

            yield self.controlPoint(arg)

    def controlPoints(self, *args):
        """
        Returns control points.
        If no arguments are supplied then all control points are returned.

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
    def iterSelection(self):
        """
        Returns a generator that yields the selected vertices.

        :rtype: iter
        """

        pass

    def selection(self):
        """
        Returns the selected vertex elements.

        :rtype: list[int]
        """

        return list(self.iterSelection())

    @abstractmethod
    def setSelection(self, vertices):
        """
        Updates the active selection with the supplied vertex elements.

        :type vertices: list[int]
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

        :rtype dict[int:float]
        """

        return dict(self.iterSoftSelection())

    @abstractmethod
    def getConnectedVertices(self, *args):
        """
        Returns a list of vertices connected to the supplied vertices.
        This should not include the original arguments!

        :rtype: list[int]
        """

        pass

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

        :rtype: dict[int:str]
        """

        for (influenceId, influence) in self.influences().items():

            yield influenceId, fnnode.FnNode(influence).name()

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

        :rtype: list[int]
        """

        # Iterate through weights
        #
        influenceIds = set()

        for (vertexIndex, vertexWeights) in self.iterWeights(*args):

            influenceIds = influenceIds.union(set(vertexWeights.keys()))

        return list(influenceIds)

    def getUnusedInfluenceIds(self, *args):
        """
        Returns a list of unused influence IDs.
        An optional list of vertices can used to narrow down this search.

        :rtype: list[int]
        """

        return list(set(self.influences().keys()) - set(self.getUsedInfluenceIds(*args)))

    def createInfluenceMap(self, otherSkin, vertexIndices=None):
        """
        Creates an influence map for transferring weights from this instance to the supplied skin.
        An optional list of vertices can be used to simplify the binder.

        :type otherSkin: AFnSkin
        :type vertexIndices: list[int]
        :rtype: dict[int:int]
        """

        # Check skin cluster type
        #
        if not otherSkin.isValid():

            raise TypeError('createInfluenceMap() expects a valid skin (%s given)!' % type(otherSkin).__name__)

        # Iterate through influences
        #
        influences = self.influences()
        otherInfluences = otherSkin.influences()

        usedInfluenceIds = self.getUsedInfluenceIds(*vertexIndices)
        influenceMap = {}

        for influenceId in usedInfluenceIds:

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

    def remapWeights(self, vertices, influenceMap):
        """
        Remaps the supplied vertex weights using the specified influence map.

        :type vertices: dict[int:dict[int:float]]
        :type influenceMap: dict[int:int]
        :rtype: dict[int:dict[int:float]]
        """

        # Check if arguments are valid
        #
        if not isinstance(vertices, dict) or not isinstance(influenceMap, dict):

            raise TypeError('remapVertexWeights() expects a dict (%s given)!' % type(vertices).__name__)

        # Reiterate through vertices
        #
        updates = {}

        for (vertexIndex, vertexWeights) in vertices.items():

            # Iterate through vertex weights
            #
            updates[vertexIndex] = {}

            for (influenceId, weight) in vertexWeights.items():

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

        :rtype: list[int]
        """

        # Iterate through vertices
        #
        vertexIndices = []

        for vertexIndex in self.range(self.numControlPoints()):

            # Check if weights contain influence ID
            #
            vertexWeights = dict(self.iterWeights(vertexIndex))

            if any([x in vertexWeights for x in args]):

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
        #
        strings = [x for x in commonPrefix.split('|') if len(x) > 0]
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
    def iterWeights(self, *args):
        """
        Returns a generator that yields weights for the supplied vertex indices.
        If no vertex indices are supplied then all weights are yielded instead.

        :rtype: iter
        """

        pass

    def weights(self, *args):
        """
        Returns the weights for the supplied vertex indices.
        If no vertex indices are supplied then all weights are returned instead.

        :rtype: dict[int:dict[int:float]]
        """

        return dict(self.iterWeights(*args))

    def setWeights(self, weights, target, source, amount, falloff=1.0):
        """
        Sets the supplied target ID to the specified amount while preserving normalization.

        :type weights: dict[int:float]
        :type target: int
        :type source: list[int]
        :type amount: float
        :type falloff: float
        :rtype: dict[int:float]
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

        if target in influenceIds or (target not in influenceIds and numInfluences < maxInfluences):

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
            if self.isClose(amount, total, abs_tol=1e-06):

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

        :type weights: dict[int:float]
        :type target: int
        :type source: list[int]
        :type percent: float
        :type falloff: float
        :rtype: dict[int:float]
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

        :type weights: dict[int:float]
        :type target: int
        :type source: list[int]
        :type increment: float
        :type falloff: float
        :rtype: dict[int:float]
        """

        # Get amount to redistribute
        #
        current = weights.get(target, 0.0)
        amount = current + (increment * falloff)

        # Set vertex weight
        #
        log.debug('Changing influence ID: %s, from %s to %s.' % (target, current, amount))
        return self.setWeights(weights, target, source, amount)

    @staticmethod
    def isClose(a, b, rel_tol=1e-03, abs_tol=0.0):
        """
        Evaluates if the two numbers of relatively close.
        Sadly this function doesn't exist in the math module until Python 3.5

        :type a: float
        :type b: float
        :type rel_tol: float
        :type abs_tol: float
        :rtype: bool
        """

        return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

    def isNormalized(self, vertexWeights):
        """
        Evaluates if the supplied weights have been normalized.

        :type vertexWeights: dict
        :rtype: bool
        """

        # Check value type
        #
        if not isinstance(vertexWeights, dict):

            raise TypeError('isNormalized() expects a dict (%s given)!' % type(vertexWeights).__name__)

        # Check influence weight total
        #
        total = sum([weight for (influenceId, weight) in vertexWeights.items()])
        log.debug('Supplied influence weights equal %s.' % total)

        return self.isClose(1.0, total)

    def normalizeWeights(self, vertexWeights, maintainMaxInfluences=True):
        """
        Normalizes the supplied vertex weights.

        :type maintainMaxInfluences: bool
        :type vertexWeights: dict[int:float]
        :rtype: dict[int:float]
        """

        # Check value type
        #
        if not isinstance(vertexWeights, dict):

            raise TypeError('normalizeWeights() expects a dict (%s given)!' % type(vertexWeights).__name__)

        # Check if influences should be pruned
        #
        if maintainMaxInfluences:

            vertexWeights = self.pruneWeights(vertexWeights)

        # Check if weights have already been normalized
        #
        isNormalized = self.isNormalized(vertexWeights)

        if isNormalized:

            log.debug('Vertex weights have already been normalized.')
            return vertexWeights

        # Get total weight we can normalize
        #
        total = sum(vertexWeights.values())

        if total == 0.0:

            raise TypeError('Cannot normalize influences from zero weights!')

        else:

            # Calculate adjusted scale factor
            #
            scale = 1.0 / total

            for (influenceId, weight) in vertexWeights.items():

                normalized = (weight * scale)
                vertexWeights[influenceId] = normalized

                log.debug(
                    'Scaling influence ID: {index}, from {weight} to {normalized}'.format(
                        index=influenceId,
                        weight=weight,
                        normalized=normalized
                    )
                )

        # Return normalized vertex weights
        #
        return vertexWeights

    def pruneWeights(self, vertexWeights):
        """
        Prunes the supplied vertex weights to meet the maximum number of weighted influences.

        :type vertexWeights: dict[int:float]
        :rtype: dict[int:float]
        """

        # Check value type
        #
        if not isinstance(vertexWeights, dict):

            raise TypeError('pruneWeights() expects a dict (%s given)!' % type(vertexWeights).__name__)

        # Check if any influences have dropped below limit
        #
        influences = self.influences()

        for (influenceId, weight) in vertexWeights.items():

            # Check if influence weight is below threshold
            #
            if self.isClose(0.0, weight) or influences[influenceId] is None:

                vertexWeights[influenceId] = 0.0

            else:

                log.debug('Skipping influence ID: %s' % influenceId)

        # Check if influences have exceeded max allowances
        #
        numInfluences = len(vertexWeights)
        maxInfluences = self.maxInfluences()

        if numInfluences > maxInfluences:

            # Order influences from lowest to highest
            #
            orderedInfluences = sorted(vertexWeights, key=vertexWeights.get, reverse=False)

            # Replace surplus influences with zero values
            #
            diff = numInfluences - maxInfluences

            for i in range(diff):

                influenceId = orderedInfluences[i]
                vertexWeights[influenceId] = 0.0

        else:

            log.debug('Vertex weights have not exceeded max influences.')

        # Return dictionary changes
        #
        return vertexWeights

    def averageWeights(self, *args, **kwargs):
        """
        Averages the supplied vertex weights.
        By default maintain max influences is enabled.

        :keyword maintainMaxInfluences: bool
        :rtype: dict[int:float]
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

    @abstractmethod
    def applyWeights(self, vertices):
        """
        Assigns the supplied vertex weights to this deformer.

        :type vertices: dict[int:dict[int:float]]
        :rtype: None
        """

        pass

    @staticmethod
    def mergeDictionaries(*args):
        """
        Combines two dictionaries together with null values.

        :rtype: dict
        """

        # Iterate through arguments
        #
        keys = set()

        for arg in args:

            keys = keys.union(set(arg.keys()))

        return {key: 0.0 for key in keys}

    def inverseDistanceWeights(self, vertices, distances):
        """
        Averages supplied vertex weights based on the inverse distance.

        :type vertices: dict[int:dict[int:float]]
        :type distances: list[float]
        :rtype: dict
        """

        # Check value types
        #
        numVertices = len(vertices)
        numDistances = len(distances)

        if numVertices != numDistances:

            raise TypeError('inverseDistanceVertexWeights() expects identical length lists!')

        # Check for zero distance
        #
        index = distances.index(0.0) if 0.0 in distances else None

        if index is not None:

            log.debug('Zero distance found in %s' % distances)
            return vertices[index]

        # Merge dictionary keys using null values
        #
        vertexWeights = self.mergeDictionaries(*list(vertices.values()))
        influenceIds = vertexWeights.keys()

        # Iterate through influences
        #
        for influenceId in influenceIds:

            # Collect weight values
            #
            weights = [vertexWeights.get(influenceId, 0.0) for vertexWeights in vertices.values()]

            # Zip list and evaluate in parallel
            #
            numerator = 0.0
            denominator = 0.0

            for weight, distance in zip(weights, distances):

                numerator += weight / pow(distance, 2.0)
                denominator += 1.0 / pow(distance, 2.0)

            # Assign average to updates
            #
            vertexWeights[influenceId] = float(numerator / denominator)

        # Return normalized weights
        #
        log.debug('Inverse Distance: %s' % vertexWeights)
        return vertexWeights

    def copyWeights(self):
        """
        Copies the selected vertices to the clipboard.

        :rtype: None
        """

        self._clipboard = self.weights(*self.selection())

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
        self.applyWeights(vertices)

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

        return self.applyWeights(updates)

    def blendVertices(self):
        """
        Blends the selected vertices.

        :rtype: None
        """

        # Get selected vertices
        #
        selection = self.selection()
        numSelected = len(selection)

        if numSelected == 0:

            return

        # Iterate through selected vertices
        #
        updates = {}

        for vertexIndex in selection:

            # Get connected vertices
            #
            connectedVertices = self.getConnectedVertices(vertexIndex)
            log.debug('Averaging vertex weights from %s.' % connectedVertices)

            # Average vertex weights
            #
            vertices = self.weights(*connectedVertices)

            vertexWeights = self.averageWeights(*list(vertices.values()))
            log.debug('%s averaged from connected vertices.' % vertexWeights)

            updates[vertexIndex] = vertexWeights

        # Apply averaged result to skin cluster
        #
        return self.applyWeights(updates)

    def blendBetweenVertices(self, blendByDistance=False):
        """
        Blends along a loop of connected vertices.

        :type blendByDistance: bool
        :rtype: None
        """

        pass

    def blendBetweenTwoVertices(self, blendByDistance=False):
        """
        Blends along the shortest path between two vertices.

        :type blendByDistance: bool
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
