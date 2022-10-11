import os
import pymxs

from collections import deque
from dcc.python import stringutils
from dcc.max.json import mxsvalueparser
from dcc.max.libs import sceneutils, nodeutils, transformutils, meshutils
from dcc.max.libs import skinutils, morpherutils
from dcc.max.libs import layerutils, attributeutils, propertyutils, controllerutils, wrapperutils
from dcc.max.decorators import coordsysoverride
from dcc.generators.inclusiverange import inclusiveRange

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MXSIterDependencies(object):
    """
    Generator class that yields the dependents required to serialize an MXS object.
    Without this we cannot pre-size the objects collection before JSON begins serializing.
    """

    # region Dunderscores
    __slots__ = (
        'objects',
        'processed',
        'skipProperties',
        'skipSubAnims',
        'skipCustomAttributes',
        'skipChildren',
        'skipLayers',
        'skipSelectionSets',
    )

    def __init__(self, *args, **kwargs):

        # Call parent method
        #
        super(MXSIterDependencies, self).__init__()

        # Declare public variables
        #
        self.objects = kwargs.get('selection', [pymxs.runtime.RootNode])
        self.processed = {}
        self.skipProperties = kwargs.get('skipProperties', False)
        self.skipSubAnims = kwargs.get('skipSubAnims', False)
        self.skipCustomAttributes = kwargs.get('skipCustomAttributes', False)
        self.skipChildren = kwargs.pop('skipChildren', False)
        self.skipLayers = kwargs.pop('skipLayers', False)
        self.skipSelectionSets = kwargs.pop('skipSelectionSets', False)

    def __iter__(self):
        """
        Private method that returns a generator that yields dependents.

        :rtype: iter
        """

        queue = deque(self.objects)

        while len(queue) > 0:

            obj = queue.popleft()
            handle = nodeutils.getAnimHandle(obj)

            processed = self.processed.get(handle, False)

            if not processed:

                yield handle, obj

                self.processed[handle] = True
                queue.extend(list(self.iterDependents(obj)))

            else:

                continue
    # endregion

    # region Methods
    def iterDependents(self, obj):
        """
        Returns a generator that yields dependents from the supplied object.

        :type obj: pymxs.MXSWrapperBase
        :rtype: iter
        """

        if not self.skipProperties:

            yield from self.iterFromProperties(obj)

        if not self.skipSubAnims:

            yield from self.iterFromSubAnims(obj)

        if not self.skipCustomAttributes:

            yield from self.iterFromCustomAttributes(obj)

        if not self.skipChildren:

            yield from self.iterChildren(obj)

        if not self.skipLayers:

            yield from self.iterLayers(obj)

    def iterFromProperties(self, obj):
        """
        Returns a generator that yields MXS objects from supplied object's properties.

        :type obj: pymxs.MXSWrapperBase
        :rtype: iter
        """

        for (key, value) in propertyutils.iterStaticProperties(obj, skipAnimatable=True):

            # Check if value is valid
            #
            if pymxs.runtime.isValidObj(value):

                yield value

            else:

                continue

    def iterFromSubAnims(self, obj):
        """
        Returns a generator that yields MXS objects from supplied object's sub-anims.

        :type obj: pymxs.MXSWrapperBase
        :rtype: iter
        """

        for subAnim in controllerutils.iterSubAnims(obj):

            # Check if value is valid
            #
            value, controller = subAnim.value, subAnim.controller

            if pymxs.runtime.isValidObj(value):

                yield value

            # Check if controller is valid
            #
            if pymxs.runtime.isValidObj(controller):

                yield controller

    def iterFromCustomAttributes(self, obj):
        """
        Returns a generator that yields attribute definitions from the supplied object.

        :type obj: pymxs.MXSWrapperBase
        :rtype: iter
        """

        yield from attributeutils.iterDefinitions(obj, baseObject=False)

    def iterLayers(self, obj):
        """
        Returns a generator that yields display layers from the supplied object.

        :type obj: pymxs.MXSWrapperBase
        :rtype: iter
        """

        layer = getattr(obj, 'layer', None)

        for parentLayer in layerutils.traceLayer(layer):

            yield parentLayer.layerAsRefTarg

    def iterChildren(self, obj):
        """
        Returns a generator that yields child nodes from the supplied object.

        :type obj: pymxs.MXSWrapperBase
        :rtype: iter
        """

        yield from iter(getattr(obj, 'children', []))
    # endregion


class MXSObjectEncoder(mxsvalueparser.MXSValueEncoder):
    """
    Overload of MXSValueEncoder used to serialize MXS scenes.
    All MXS objects are stored via JSON references.
    The scene objects collection contains handle-object pairs to allow for referencing.
    To avoid recursion errors this encoder queues objects for serialization.
    """

    # region Dunderscores
    __slots__ = (
        'objects',
        'selection',
        'skipProperties',
        'skipSubAnims',
        'skipCustomAttributes',
        'skipKeys',
        'skipChildren',
        'skipShapes',
        'skipLayers',
        'skipSelectionSets'
    )

    __object_types__ = {
        'SplineShape': 'serializeSplineShape',
        'line': 'serializeSplineShape',
        'NURBSCurveshape': 'serializeNurbsCurveShape',
        'Editable_Poly': 'serializeMesh',
        'Editable_mesh': 'serializeMesh',
        'Skin': 'serializeSkin',
        'Morpher': 'serializeMorpher',
        'lookat': 'serializeLookAt',
        'Attachment': 'serializeAttachment',
        'AttributeDef': 'serializeAttributeDef',
        'Base_Layer': 'serializeLayer',
        'ArrayParameter': 'serializeArrayParameter'
    }

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Declare private variables
        #
        self.objects = {handle: dependent for (handle, dependent) in MXSIterDependencies(**kwargs)}
        self.selection = kwargs.pop('selection', None)
        self.skipProperties = kwargs.pop('skipProperties', False)
        self.skipSubAnims = kwargs.pop('skipSubAnims', False)
        self.skipCustomAttributes = kwargs.pop('skipCustomAttributes', False)
        self.skipKeys = kwargs.pop('skipKeys', False)
        self.skipChildren = kwargs.pop('skipChildren', False)
        self.skipShapes = kwargs.pop('skipShapes', False)
        self.skipLayers = kwargs.pop('skipLayers', False)
        self.skipSelectionSets = kwargs.pop('skipSelectionSets', False)

        # Call parent method
        #
        super(MXSObjectEncoder, self).__init__(*args, **kwargs)
    # endregion

    # region Methods
    def hasHandle(self, handle):
        """
        Evaluates if the supplied handle is serializable.

        :type handle: int
        :rtype: bool
        """

        return self.objects.get(handle, None) is not None

    def isSerializable(self, obj):
        """
        Evaluates if the supplied object is serializable.

        :type obj: Any
        :rtype: bool
        """

        try:

            handle = nodeutils.getAnimHandle(obj)
            return self.hasHandle(handle)

        except RuntimeError:

            return False

    def findDelegate(self, obj, default=None):
        """
        Returns the delegate for the supplied Max object.

        :type obj: pymxs.MXSWrapperBase
        :type default: Union[Callable, None]
        :rtype: Callable
        """

        bases = set(map(str, wrapperutils.iterBases(obj)))
        options = set(self.__object_types__.keys())

        delegates = bases.intersection(options)
        numDelegates = len(delegates)

        if numDelegates == 1:

            className = list(delegates)[0]
            return getattr(self, self.__object_types__[className])

        else:

            return default

    def default(self, obj):
        """
        Returns a serializable object for the supplied value.

        :type obj: Any
        :rtype: Any
        """

        # Evaluate object type
        #
        if not isinstance(obj, pymxs.MXSWrapperBase):

            return super(MXSObjectEncoder, self).default(obj)

        # Evaluate MXS object class
        #
        if wrapperutils.isKindOf(obj, pymxs.runtime.Scene):

            log.info('Serializing scene: %s' % pymxs.runtime.maxFilename)
            return self.serializeScene(obj)

        elif wrapperutils.isKindOf(obj, pymxs.runtime.MAXRootNode):

            return self.serializeRootNode(obj)

        elif pymxs.runtime.isValidNode(obj):

            log.info('Serializing node: %s' % obj.name)
            return self.serializeNode(obj)

        elif pymxs.runtime.isController(obj):

            return self.delegateController(obj)

        elif pymxs.runtime.isValidObj(obj):

            return self.delegateObject(obj)

        else:

            return super(MXSObjectEncoder, self).default(obj)

    def serializeProperties(self, wrapper):
        """
        Returns a list of serializable key-value pairs from the supplied Max object's properties.

        :type wrapper: pymxs.MXSWrapperBase
        :rtype: Dict[str, Any]
        """

        return {key: self.serializeRef(value) for (key, value) in propertyutils.iterStaticProperties(wrapper, skipAnimatable=True)}

    def serializeSubAnims(self, wrapper):
        """
        Returns a list serializable objects from the supplied Max object's sub-anims.

        :type wrapper: pymxs.MXSWrapperBase
        :rtype: List[dict]
        """

        # Iterate through sub-anims
        #
        numSubAnims = getattr(wrapper, 'numSubs', 0)
        subAnims = [None] * numSubAnims

        parent = self.serializeRef(wrapper)

        for i in range(numSubAnims):

            # Get indexed sub-anim
            #
            index = i + 1
            subAnim = pymxs.runtime.getSubAnim(wrapper, index)

            # Serialize sub-anim
            #
            obj = self.serializeInheritance(subAnim)
            obj['args'] = []
            obj['kwargs'] = {
                'name': stringutils.slugify(str(subAnim.name), whitespace='_', illegal='_'),
                'index': index,
                'isAnimated': getattr(subAnim, 'isAnimated', False),
                'controller': self.serializeRef(subAnim.controller),
                'value': self.serializeRef(subAnim.value),
                'parent': parent
            }

            subAnims[i] = obj

        return subAnims

    def serializeCustomAttributes(self, wrapper):
        """
        Returns a list serializable objects from the supplied Max object's custom attributes.

        :type wrapper: pymxs.MXSWrapperBase
        :rtype: List[dict]
        """

        return list(map(self.serializeRef, attributeutils.iterDefinitions(wrapper, baseObject=False)))

    def serializeNoteTracks(self, wrapper):
        """
        Returns a list serializable objects from the supplied Max object's note tracks.

        :type wrapper: pymxs.MXSWrapperBase
        :rtype: List[dict]
        """

        numTracks = pymxs.runtime.numNoteTracks(wrapper)
        tracks = [pymxs.runtime.getNoteTrack(wrapper, i) for i in inclusiveRange(1, numTracks, 1)]

        return list(map(self.serializeNoteTrack, tracks))

    def serializeRef(self, wrapper):
        """
        Returns a JSON reference for the supplied Max object.

        :type wrapper: pymxs.MXSWrapperBase
        :rtype: Any
        """

        # Check if object is valid
        #
        if not pymxs.runtime.isValidObj(wrapper):

            return self.default(wrapper)

        # Check if reference exists
        #
        handle = nodeutils.getAnimHandle(wrapper)

        if self.hasHandle(handle):

            return {'$ref': '#/objects/{handle}'.format(handle=handle)}

        else:

            return None

    def delegateObject(self, wrapper, **kwargs):
        """
        Delegates the supplied Max object to the required serializer.

        :type wrapper: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Check if object is valid
        #
        if not pymxs.runtime.isValidObj(wrapper):

            raise TypeError('delegateObject() expects a valid object!')

        # Check if object delegate exists
        #
        func = self.findDelegate(wrapper, default=self.serializeObject)
        return func(wrapper, **kwargs)

    def serializeObject(self, wrapper, **kwargs):
        """
        Returns a serializable object for the supplied Max-object.
        By default, this method returns a JSON reference to the Max-object.

        :type wrapper: pymxs.MXSWrapperBase
        :key skipProperties: bool
        :key skipSubAnims: bool
        :key skipCustomAttributes: bool
        :rtype: dict
        """

        # Register Max-object
        #
        obj = self.serializeInheritance(wrapper)
        obj['name'] = getattr(wrapper, 'name', '')
        obj['handle'] = nodeutils.getAnimHandle(wrapper)
        obj['properties'] = {}
        obj['subAnims'] = []
        obj['customAttributes'] = []
        obj['noteTracks'] = []

        # Check if note tracks should be skipped
        #
        skipKeys = kwargs.get('skipKeys', self.skipKeys)

        if not skipKeys:

            obj['noteTracks'].extend(self.serializeNoteTracks(wrapper))

        # Check if properties should be skipped
        #
        skipProperties = kwargs.get('skipProperties', self.skipProperties)

        if not skipProperties:

            obj['properties'].update(self.serializeProperties(wrapper))

        # Check if sub-anims should be skipped
        #
        skipSubAnims = kwargs.get('skipSubAnims', self.skipSubAnims)

        if not skipSubAnims:

            obj['subAnims'].extend(self.serializeSubAnims(wrapper))

        # Check if custom-attributes should be skipped
        #
        skipCustomAttributes = kwargs.get('skipCustomAttributes', self.skipCustomAttributes)

        if not skipCustomAttributes:

            obj['customAttributes'].extend(self.serializeCustomAttributes(wrapper))

        return obj

    def serializeNode(self, node, **kwargs):
        """
        Returns a serializable object for the supplied Max node.
        Any class-specific properties can be found in the modifier stack!

        :type node: pymxs.MXSWrapperBase
        :key skipChildren: bool
        :rtype: dict
        """

        # Check if node is valid
        #
        if not pymxs.runtime.isValidNode(node):

            raise TypeError('serializeNode() expects a valid node!')

        # Serialize object components
        #
        obj = self.serializeObject(node, skipProperties=True, skipCustomAttributes=True)

        # Extend node properties
        #
        properties = obj['properties']
        properties['wireColor'] = node.wireColor
        properties['lockFlags'] = pymxs.runtime.getTransformLockFlags(node)
        properties['inheritanceFlags'] = pymxs.runtime.getInheritanceFlags(node)
        properties['worldTransform'] = transformutils.getWorldMatrix(node)
        properties['objectTransform'] = node.objectTransform * pymxs.runtime.inverse(transformutils.getWorldMatrix(node))
        properties['userPropertyBuffer'] = pymxs.runtime.getUserPropBuffer(node)
        properties['parent'] = None
        properties['children'] = []

        # Check if parent should be skipped
        #
        parent = getattr(node, 'parent', None)
        skipChildren = kwargs.get('skipChildren', self.skipChildren)

        if parent is not None and not skipChildren:

            properties['parent'] = self.serializeRef(parent)

        # Check if children should be skipped
        #
        children = getattr(node, 'children', None)

        if children is not None and not skipChildren:

            properties['children'].extend([self.serializeRef(x) for x in children])

        return obj

    def serializeAttributeDef(self, attributeDef):
        """
        Returns a serializable object for the supplied attribute definition.

        :type attributeDef: pymxs.MXSWrapperBase
        :rtype: dict
        """

        obj = self.serializeObject(attributeDef)
        obj['properties']['owner'] = self.serializeRef(pymxs.runtime.custAttributes.getOwner(attributeDef))

        return obj

    def serializeSkin(self, skin):
        """
        Returns a serializable object for the supplied skin modifier.

        :type skin: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize max-object components
        #
        obj = self.serializeObject(skin)

        # Check if skin-weights should be skipped
        #
        properties = obj['properties']
        properties['influences'] = {}
        properties['meshBindMatrix'] = pymxs.runtime.Matrix3(1)
        properties['boneBindMatrices'] = {}
        properties['weights'] = {}

        if not self.skipShapes:

            node = wrapperutils.getAssociatedNode(skin)

            properties['influences'] = {influenceId: self.serializeRef(influence) for (influenceId, influence) in skinutils.iterInfluences(skin)}
            properties['meshBindMatrix'] = pymxs.runtime.skinutils.GetMeshBindTM(node)
            properties['boneBindMatrices'] = {influenceId: pymxs.runtime.skinutils.getBoneBindTM(node, influence) for (influenceId, influence) in skinutils.iterInfluences(skin)}
            properties['weights'] = dict(skinutils.iterVertexWeights(skin))

        return obj

    def serializeMorpher(self, morpher):
        """
        Returns a serializable object for the supplied morpher modifier.

        :type morpher: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize max-object components
        #
        obj = self.serializeObject(morpher)

        # Check if morph-targets should be skipped
        #
        properties = obj['properties']
        properties['channels'] = []

        if not self.skipShapes:

            properties['channels'].extend([{'name': name, 'target': self.serializeRef(target), 'weight': weight} for (name, target, weight) in morpherutils.iterTargets(morpher)])

        return obj

    @coordsysoverride.coordSysOverride(mode='local')
    def serializeNurbsObject(self, nurbsSet, nurbsIndex=1):
        """
        Returns a serializable object for the specified nurbs curve object.

        :type nurbsSet: pymxs.MXSWrapperBase
        :type nurbsIndex: int
        :rtype: dict
        """

        nurbsObject = pymxs.runtime.getObject(nurbsSet, nurbsIndex)

        return {
            'order': nurbsObject.order,
            'transform': nurbsObject.transform,
            'isClosed': nurbsObject.isClosed,
            'endsOverlap': nurbsObject.endsOverlap,
            'autoParam': nurbsObject.autoParam,
            'cvs': [pymxs.runtime.getCV(nurbsObject, i).position for i in inclusiveRange(1, nurbsObject.numCVs, 1)],
            'knots': [pymxs.runtime.getKnot(nurbsObject, i) for i in inclusiveRange(1, nurbsObject.numKnots, 1)]
        }

    def serializeNurbsCurveShape(self, nurbsCurve):
        """
        Returns a serializable object for the supplied nurbs curve shape.

        :type nurbsCurve: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize max-object components
        #
        obj = self.serializeObject(nurbsCurve)

        # Check if shapes should be skipped
        #
        if not self.skipShapes:

            node = wrapperutils.getAssociatedNode(nurbsCurve)
            nurbsSet = pymxs.runtime.getNurbsSet(node)  # Do not supply the relational flag!
            nurbsSetCount = nurbsSet.count

            obj['properties']['nurbs'] = [self.serializeNurbsObject(nurbsSet, nurbsIndex=nurbsIndex) for nurbsIndex in inclusiveRange(1, nurbsSetCount, 1)]

        return obj

    @coordsysoverride.coordSysOverride(mode='world')
    def serializeKnots(self, spline, splineIndex=1):
        """
        Serializes the knots for the given spline.
        Knots are sampled in world space in order to bypass object-transform.

        :type spline: pymxs.MXSWrapperBase
        :type splineIndex: int
        :rtype: List[dict]
        """

        # Iterate through knots
        #
        numKnots = pymxs.runtime.numKnots(spline, splineIndex)
        knots = [None] * numKnots

        parentInverseMatrix = pymxs.runtime.inverse(spline.transform)

        for i in range(numKnots):

            # Evaluate knot type
            #
            knotIndex = i + 1
            knotType = pymxs.runtime.getKnotType(spline, splineIndex, knotIndex)

            knot = {'type': knotType, 'inVec': None, 'point': None, 'outVec': None}
            knots[i] = knot

            if knotType in (pymxs.runtime.Name('corner'), pymxs.runtime.Name('bezierCorner')):

                knot['point'] = pymxs.runtime.getKnotPoint(spline, splineIndex, knotIndex) * parentInverseMatrix

            elif knotType in (pymxs.runtime.Name('smooth'), pymxs.runtime.Name('bezier')):

                knot['inVec'] = pymxs.runtime.getInVec(spline, splineIndex, knotIndex) * parentInverseMatrix
                knot['point'] = pymxs.runtime.getKnotPoint(spline, splineIndex, knotIndex) * parentInverseMatrix
                knot['outVec'] = pymxs.runtime.getOutVec(spline, splineIndex, knotIndex) * parentInverseMatrix

            else:

                continue

        return knots

    def serializeSpline(self, spline, splineIndex=1):
        """
        Returns a serializable object for the specified spline shape.

        :type spline: pymxs.MXSWrapperBase
        :type splineIndex: int
        :rtype: dict
        """

        return {
            'isClosed': pymxs.runtime.isClosed(spline, splineIndex),
            'knots': self.serializeKnots(spline, splineIndex=splineIndex)
        }

    def serializeSplineShape(self, spline):
        """
        Returns a serializable object for the supplied spline object.

        :type spline: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize max-object components
        #
        obj = self.serializeObject(spline)

        # Check if shapes should be skipped
        #
        if not self.skipShapes:

            node = wrapperutils.getAssociatedNode(spline)
            numSplines = pymxs.runtime.numSplines(node)

            obj['properties']['splines'] = [self.serializeSpline(node, splineIndex=splineIndex) for splineIndex in inclusiveRange(1, numSplines, 1)]

        return obj

    def serializeMap(self, mesh, channel=0):
        """
        Returns a serializable object for the specified map channel.

        :type mesh: pymxs.MXSWrapperBase
        :type channel: int
        :rtype: dict
        """

        isSupported = meshutils.isMapSupported(mesh, channel)
        obj = {'supported': isSupported, 'vertices': [], 'faceVertexIndices': []}

        if isSupported:

            obj['vertices'] = list(meshutils.iterMapVertices(mesh, channel=channel))
            obj['faceVertexIndices'] = list(meshutils.iterMapFaceVertexIndices(mesh, channel=channel))

        return obj

    def serializeMesh(self, mesh):
        """
        Returns a serializable object for the supplied mesh object.

        :type mesh: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize max-object components
        #
        obj = self.serializeObject(mesh)

        # Check if shapes should be skipped
        #
        if not self.skipShapes:

            # Compute face-triangle vertex indices
            #
            triMesh = meshutils.getTriMesh(mesh)
            faceTriangleIndices = meshutils.getFaceTriangleIndices(mesh)
            faceTriangleVertexIndices = [[list(meshutils.iterFaceVertexIndices(triMesh, indices=[triangleIndex]))[0] for triangleIndex in triangleIndices] for (faceIndex, triangleIndices) in faceTriangleIndices.items()]

            # Update object properties
            #
            properties = obj['properties']
            properties['vertices'] = list(meshutils.iterVertices(mesh))
            properties['faceVertexIndices'] = list(meshutils.iterFaceVertexIndices(mesh))
            properties['faceTriangleVertexIndices'] = faceTriangleVertexIndices
            properties['smoothingGroups'] = list(meshutils.iterSmoothingGroups(mesh))
            properties['maps'] = [self.serializeMap(mesh, channel=channel) for channel in range(meshutils.mapCount(mesh))]
            properties['faceMaterialIndices'] = list(meshutils.iterFaceMaterialIndices(mesh))

        return obj

    def delegateController(self, controller):
        """
        Delegates the supplied controller to the required serializer.

        :type controller: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Check if controller delegate exists
        #
        func = self.findDelegate(controller)

        if callable(func):

            return func(controller)

        elif controllerutils.isListController(controller):

            return self.serializeListController(controller)

        elif controllerutils.isConstraint(controller):

            return self.serializeConstraint(controller)

        elif controllerutils.isWire(controller):

            return self.serializeWire(controller)

        else:

            return self.serializeController(controller)

    def serializeController(self, controller, **kwargs):
        """
        Returns a serializable object for the supplied Max controller.

        :type controller: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize object components
        #
        obj = self.serializeObject(controller)

        # Extend controller properties
        #
        properties = obj['properties']
        properties['value'] = controller.value
        properties['outOfRangeTypes'] = (pymxs.runtime.getBeforeORT(controller), pymxs.runtime.getAfterORT(controller))
        properties['keys'] = []

        # Check if keys should be included
        #
        skipKeys = kwargs.get('skipKeys', self.skipKeys)

        if not skipKeys and hasattr(controller, 'keys'):

            properties['keys'].extend([self.serializeMAXKey(x) for x in controllerutils.iterMaxKeys(controller)])

        return obj

    def serializeListController(self, controller):
        """
        Returns a serializable object for the supplied list controller.

        :type controller: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize controller components
        #
        obj = self.serializeController(controller)

        # Extend controller properties
        #
        properties = obj['properties']
        properties['active'] = controller.getActive()

        return obj

    def serializeConstraint(self, constraint):
        """
        Returns a serializable object for the supplied max constraint.

        :type constraint: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize controller components
        #
        obj = self.serializeController(constraint)

        # Extend constraint properties
        #
        numTargets = constraint.getNumTargets()

        properties = obj['properties']
        properties['targets'] = [self.serializeRef(constraint.getNode(i)) for i in inclusiveRange(1, numTargets, 1)]

        # Serialize up-node
        #
        if pymxs.runtime.isProperty(constraint, 'pickUpNode'):

            properties['pickUpNode'] = self.serializeRef(constraint.pickUpNode)

        return obj

    def serializeWire(self, wire):
        """
        Returns a serializable object for the supplied wire parameter.
        Be aware that a majority of the wire interface becomes useless once you introduce instanced controller dependents!

        :type wire: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize controller components
        #
        obj = self.serializeController(wire)

        # Extend wire properties
        #
        properties = obj['properties']
        properties['isMaster'] = wire.isMaster
        properties['isSlave'] = wire.isSlave
        properties['isTwoWay'] = wire.isTwoWay

        # Evaluate if master controller is instanced
        #
        slaveAnimation = wire.slaveAnimation

        if controllerutils.isInstancedController(slaveAnimation):

            expression = wire.getExprText(1)
            properties['dependents'] = [{'controller': self.serializeRef(slaveAnimation), 'expression': expression}]

        else:

            # Iterate through wires
            #
            numWires = int(wire.numWires)
            properties['dependents'] = []

            for i in inclusiveRange(1, numWires, 1):

                # Check if dependent is valid
                #
                parent = wire.getWireParent(i)
                subAnim = wire.getWireSubNum(i)
                dependent = pymxs.runtime.getSubAnim(parent, subAnim).controller
                expression = wire.getExprText(i)

                if wrapperutils.hasValidExpression(dependent):

                    properties['dependents'].append({'controller': self.serializeRef(dependent), 'expression': expression})

                else:

                    continue

        return obj

    def serializeLookAt(self, lookAt):
        """
        Returns a serializable object for the supplied lookat constraint.
        Since this controller is deprecated none of the properties are dynamically accessible!

        :type lookAt: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize controller components
        #
        obj = self.serializeController(lookAt)

        # Extend look-at properties
        #
        node = wrapperutils.getAssociatedNode(lookAt)

        properties = obj['properties']
        properties['target'] = self.serializeRef(node.target)
        properties['useTargetAsUpNode'] = lookAt.useTargetAsUpNode
        properties['axis'] = lookAt.axis
        properties['flip'] = lookAt.flip

        return obj

    def serializeAttachment(self, attachment):
        """
        Returns a serializable object for the supplied attachment constraint.
        This controller uses a special key type which is only accessible via the AttachCtrl interface.

        :type attachment: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize controller components
        #
        obj = self.serializeController(attachment, skipKeys=True)

        # Check if keys should be included
        #
        if not self.skipKeys:

            properties = obj['properties']
            properties['keys'].extend([self.serializeMAXKey(x) for x in controllerutils.iterAMaxKeys(attachment)])

        return obj

    def serializeArrayParameter(self, array):
        """
        Serializes the supplied array parameter into a json object.

        :type array: pymxs.runtime.ArrayParameter
        :rtype: dict
        """

        obj = self.serializeObject(array)
        obj['__parameters__'] = list(map(self.serializeRef, array))

        return obj

    def serializeSelectionSet(self, selectionSet):
        """
        Serializes the supplied selection set into a json object.

        :type selectionSet: pymxs.runtime.SelectionSet
        :rtype: List[dict]
        """

        return [self.serializeRef(selectionSet[i]) for i in range(0, selectionSet.count, 1) if self.isSerializable(selectionSet[i])]

    def serializeLayer(self, layer):
        """
        Returns a serializable object for the supplied layer object.

        :type layer: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize max-object components
        #
        obj = self.serializeObject(layer)

        # Extend layer properties
        #
        properties = obj['properties']
        properties['isHidden'] = layer.isHidden
        properties['isFrozen'] = layer.isFrozen
        properties['nodes'] = [self.serializeRef(node) for node in layerutils.iterNodesFromLayers(layer) if self.isSerializable(node)]
        properties['parent'] = self.serializeRef(getattr(layer.getParent(), 'layerAsRefTarg', None))
        properties['children'] = [self.serializeRef(child) for child in layerutils.iterChildLayers(layer) if self.isSerializable(child)]

        return obj

    def serializeRootNode(self, rootNode):
        """
        Returns a serializable object for the supplied root node.

        :type rootNode: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize object
        #
        obj = self.serializeObject(rootNode)

        # Extend children
        #
        properties = obj['properties']

        if stringutils.isNullOrEmpty(self.selection):

            properties['children'] = [self.serializeRef(child) for child in rootNode.children]

        else:

            properties['children'] = [self.serializeRef(child) for child in self.selection]

        return obj

    def serializeScene(self, scene):
        """
        Returns a serializable object for the supplied Max scene.

        :type scene: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize scene properties
        #
        obj = self.serializeInheritance(scene)
        obj['filePath'] = os.path.join(os.path.normpath(pymxs.runtime.maxFilePath), pymxs.runtime.maxFilename)
        obj['projectPath'] = sceneutils.projectPath()
        obj['properties'] = dict(sceneutils.iterFileProperties())
        obj['animationRange'] = pymxs.runtime.animationRange
        obj['frameRate'] = pymxs.runtime.frameRate
        obj['ticksPerFrame'] = pymxs.runtime.ticksPerFrame
        obj['objects'] = self.objects
        obj['selectionSets'] = {}
        obj['layers'] = []
        obj['world'] = self.serializeRef(pymxs.runtime.RootNode)
        obj['materials'] = [self.serializeRef(material) for material in scene.scene_materials if self.isSerializable(material)]

        # Check if selection-sets should be skipped
        #
        if not self.skipSelectionSets:

            obj['selectionSets'].update(self.serializeSelectionSetArray(pymxs.runtime.SelectionSets))

        # Check if layers should be skipped
        #
        if not self.skipLayers:

            obj['layers'].extend([self.serializeRef(layer) for layer in layerutils.iterTopLevelLayers() if self.isSerializable(layer)])

        return obj
    # endregion
