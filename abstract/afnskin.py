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

            influences[influenceId] = fnnode.FnNode(influence).name()

        # Commit vertex weights to state object
        #
        for vertexIndex in self.iterVertices():

            vertices[vertexIndex] = self.controlPoint(vertexIndex)
            points[vertexIndex] = self.weights(vertexIndex)

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
    def iterVertices(self):
        """
        Returns a generator that yields all vertex indices.
        This is here purely to support 1-based arrays in god forsaken programs...

        :rtype: iter
        """

        pass

    @abstractmethod
    def controlPoint(self, vertexIndex):
        """
        Returns the control point for the specified vertex.

        :type vertexIndex: int
        :rtype: list[float, float, float]
        """

        pass

    def iterControlPoints(self):
        """
        Returns a generator that yields all control points.

        :rtype: iter
        """

        for vertexIndex in self.iterVertices():

            yield self.controlPoint(vertexIndex)

    def controlPoints(self):
        """
        Returns the control points from the intermediate object.

        :rtype: list
        """

        return list(self.iterControlPoints())

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

    def getVerticesByInfluenceId(self, *args):
        """
        Returns a list of vertices associated with the supplied influence ids.
        This can be an expensive operation so use sparingly.

        :rtype: list[int]
        """

        # Iterate through vertices
        #
        vertexIndices = []

        for vertexIndex in self.iterVertices():

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
    def iterWeights(self, vertexIndex):
        """
        Returns a generator that yields the weights for the given vertex.

        :rtype: iter
        """

        pass

    def weights(self, vertexIndex):
        """
        Returns the weights for the given vertex.

        :rtype: dict[int:float]
        """

        return dict(self.iterWeights(vertexIndex))

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

    def averageWeights(self, vertices, maintainMaxInfluences=True):
        """
        Averages the supplied vertex weights.
        By default maintain max influences is enabled.

        :type maintainMaxInfluences: bool
        :type vertices: dict[int:dict[int:float]]
        :rtype: dict[int:dict[int:float]]
        """

        # Iterate through vertices
        #
        average = {}

        for (vertexIndex, vertexWeights) in vertices.items():

            # Iterate through copied weights
            #
            for (influenceId, vertexWeight) in vertexWeights.items():

                # Check if influence key already exists
                #
                if influenceId not in average:

                    average[influenceId] = vertexWeights[influenceId]

                else:

                    average[influenceId] += vertexWeights[influenceId]

        # Return normalized result
        #
        return self.normalizeWeights(average, maintainMaxInfluences=maintainMaxInfluences)

    @abstractmethod
    def applyWeights(self, vertexIndex, weights):
        """
        Assigns the supplied vertex weights to this deformer.

        :type vertexIndex: int
        :type weights: dict[int:float]
        :rtype: None
        """

        pass

    def copyWeights(self):
        """
        Copies the selected vertices to the clipboard.

        :rtype: None
        """

        self._clipboard = {x: self.weights(x) for x in self.selection()}

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
            vertices = {target: self.weights(source) for (source, target) in zip(self._clipboard.keys(), selection)}

        else:

            # Iterate through vertices
            #
            source = self._clipboard.keys()[-1]
            vertices = {vertexIndex: deepcopy(self._clipboard[source]) for vertexIndex in selection}

        # Apply weights
        #
        for (vertexIndex, vertexWeights) in vertices.items():

            self.applyWeights(vertexIndex, vertexWeights)

    def pasteAveragedWeights(self):
        """
        Pastes the average of the weights from the clipboard.

        :rtype: None
        """

        pass

    def blendVertices(self):
        """
        Blends the selected vertices.

        :rtype: None
        """

        pass

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

            json.dump(self.__getstate__(), jsonFile)

    def loadWeights(self, filePath):
        """
        Loads the skin weights from the specified file path.

        :type filePath: str
        :rtype: None
        """

        with open(filePath, 'r') as jsonFile:

            self.__setstate__(json.load(jsonFile))
