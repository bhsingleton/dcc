import os
import pymxs

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


class MXSObjectEncoder(mxsvalueparser.MXSValueEncoder):
    """
    Overload of MXSValueEncoder used to serialize MXS objects.
    This encoder uses references so that objects can be reused within the data structure!
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
        'skipSelectionSets',
        'skipMaterials'
    )

    __object_types__ = {
        'SplineShape': 'serializeSplineShape',
        'line': 'serializeSplineShape',
        'Editable_Poly': 'serializeMesh',
        'Editable_mesh': 'serializeMesh',
        'Skin': 'serializeSkin',
        'Morpher': 'serializeMorpher',
        'lookat': 'serializeLookAt',
        'Attachment': 'serializeAttachment'
    }

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Declare private variables
        #
        self.objects = {}
        self.selection = kwargs.get('selection', None)
        self.skipProperties = kwargs.pop('skipProperties', False)
        self.skipSubAnims = kwargs.pop('skipSubAnims', False)
        self.skipCustomAttributes = kwargs.pop('skipCustomAttributes', False)
        self.skipKeys = kwargs.pop('skipKeys', False)
        self.skipChildren = kwargs.pop('skipChildren', False)
        self.skipShapes = kwargs.pop('skipShapes', False)
        self.skipLayers = kwargs.pop('skipLayers', False)
        self.skipSelectionSets = kwargs.pop('skipSelectionSets', False)
        self.skipMaterials = kwargs.pop('skipMaterials', False)

        # Call parent method
        #
        super(MXSObjectEncoder, self).__init__(*args, **kwargs)
    # endregion

    # region Methods
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
        if nodeutils.isValidScene(obj):

            log.info('Serializing scene: %s' % pymxs.runtime.maxFilename)
            return self.serializeScene(obj)

        elif wrapperutils.isValidWrapper(obj) or controllerutils.hasSubAnims(obj):

            return self.serializeRef(obj)

        else:

            return super(MXSObjectEncoder, self).default(obj)

    def hasObjectHandle(self, handle):
        """
        Evaluates if this encoder has serialized the supplied object handle.

        :type handle: int
        :rtype: bool
        """

        return self.objects.get(handle, None) is not None

    def registerObject(self, wrapper):
        """
        Registers the supplied Max-object in the internal object map.

        :type wrapper: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Evaluate if object is valid
        #
        if not pymxs.runtime.isValidObj(wrapper):

            raise TypeError('registerObjectHandle() expects a valid object!')

        # Check if Max-object has already been registered
        #
        handle = pymxs.runtime.getHandleByAnim(wrapper)

        if self.hasObjectHandle(handle):

            return self.objects[handle]

        # Create new object
        #
        obj = self.serializeInheritance(wrapper)
        obj['name'] = getattr(wrapper, 'name', '')
        obj['handle'] = handle
        obj['properties'] = {}
        obj['subAnims'] = []
        obj['customAttributes'] = []

        self.objects[handle] = obj

        return obj

    def serializeRef(self, wrapper):
        """
        Returns a JSON reference for the supplied Max object.

        :type wrapper: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Check if object is valid
        #
        if not pymxs.runtime.isValidObj(wrapper):

            return None

        # Check if object has already been serialized
        #
        handle = pymxs.runtime.getHandleByAnim(wrapper)
        path = {'$ref': '#/objects/{handle}'.format(handle=handle)}

        if self.hasObjectHandle(handle):

            return path

        # Delegate object to associated serializer
        #
        if nodeutils.isValidNode(wrapper):

            log.info('Serializing node: %s' % wrapper.name)
            self.serializeNode(wrapper)

        elif controllerutils.isValidController(wrapper):

            log.debug('Serializing controller: %s' % wrapper)
            self.delegateController(wrapper)

        elif layerutils.isValidLayer(wrapper):

            log.debug('Serializing layer: %s' % wrapper.name)
            self.serializeLayer(wrapper)

        else:

            self.delegateObject(wrapper)

        return path

    def serializeProperties(self, wrapper):
        """
        Returns a list of serializable key-value pairs from the supplied Max object's properties.

        :type wrapper: pymxs.MXSWrapperBase
        :rtype: Dict[str, Any]
        """

        return {key: self.default(value) for (key, value) in propertyutils.iterStaticProperties(wrapper, skipAnimatable=True)}

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
                'value': self.default(subAnim.value),
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

        definitions = list(attributeutils.iterDefinitions(wrapper, baseObject=False))
        numDefinitions = len(definitions)

        refs = [None] * numDefinitions

        for (i, definition) in enumerate(definitions):

            obj = self.serializeObject(definition)
            obj['properties']['owner'] = self.default(pymxs.runtime.custAttributes.getOwner(definition))

            refs[i] = self.serializeRef(definition)

        return refs

    def delegateObject(self, wrapper, **kwargs):
        """
        Delegates the supplied Max object to the required serializer.

        :type wrapper: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Check if object is valid
        #
        if not pymxs.runtime.isValidObj(wrapper):

            raise TypeError('delegateMaxObject() expects a valid object!')

        # Check if object has already been serialized
        #

        # Check if object delegate exists
        #
        className = str(pymxs.runtime.classOf(wrapper))
        delegate = self.__object_types__.get(className, '')

        func = getattr(self, delegate, None)

        if callable(func):

            return func(wrapper, **kwargs)

        else:

            return self.serializeObject(wrapper, **kwargs)

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
        obj = self.registerObject(wrapper)

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

            properties['channels'] = [{'name': name, 'target': self.serializeRef(target), 'weight': weight} for (name, target, weight) in morpherutils.iterTargets(morpher)]

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

            obj['properties']['splines'] = [self.serializeSpline(node, splineIndex=splineIndex) for splineIndex in inclusiveRange(1, numSplines)]

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

            properties = obj['properties']
            properties['vertices'] = list(meshutils.iterVertices(mesh))
            properties['faceVertexIndices'] = list(meshutils.iterFaceVertexIndices(mesh))
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
        className = str(pymxs.runtime.classOf(controller))
        delegate = self.__object_types__.get(className, '')

        func = getattr(self, delegate, None)

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
        properties['nodes'] = [self.serializeRef(x) for x in layerutils.iterNodesFromLayers(layer)]
        properties['parent'] = self.serializeRef(layer.getParent())
        properties['children'] = [self.serializeRef(x.layerAsRefTarg) for x in layerutils.iterChildLayers(layer)]

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
        obj['materials'] = []
        obj['world'] = []

        # Check if custom selection should be used
        #
        if self.selection is not None:

            obj['world'].extend([self.serializeRef(x) for x in self.selection])

        else:

            obj['world'].extend([self.serializeRef(x) for x in scene.world.children])

        # Check if selection-sets should be skipped
        #
        if not self.skipSelectionSets:

            obj['selectionSets'].update({name: list(map(self.serializeRef, nodes)) for (name, nodes) in nodeutils.iterSelectionSets()})

        # Check if layers should be skipped
        #
        if not self.skipLayers:

            obj['layers'].extend([self.serializeRef(layer.layerAsRefTarg) for layer in layerutils.iterTopLevelLayers()])

        # Check if materials should be skipped
        #
        if not self.skipMaterials:

            obj['materials'].extend([self.serializeRef(material) for material in scene.scene_materials])

        return obj
    # endregion
