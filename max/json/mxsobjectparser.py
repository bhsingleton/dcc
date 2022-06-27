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
    """

    # region Dunderscores
    __slots__ = (
        'skipProperties',
        'skipSubAnims',
        'skipCustomAttributes',
        'skipKeys',
        'skipChildren',
        'skipShapes',
        'skipLayers',
        'skipSelectionSets',
        'skipMaterials',
        'suppress'
    )

    __controller_types__ = {
        'IKChainControl': 'serializeIkChainControl',
        'SplineIKChain': 'serializeSplineIKChain',
        'lookat': 'serializeLookAt',
        'Attachment': 'serializeAttachment'
    }

    __object_types__ = {
        'ExposeTm': 'serializeExposeTm',
        'Spline_IK_Control': 'serializeSplineIKControl',
        'SplineShape': 'serializeSplineShape',
        'line': 'serializeSplineShape',
        'Editable_Poly': 'serializeEditablePoly',
        'Editable_mesh': 'serializeEditablePoly',
        'Skin': 'serializeSkin',
        'Morpher': 'serializeMorpher'
    }

    __suppress__ = (
        'Visibility',
        'Space_Warps',
        'Material',
        'Image_Motion_Blur_Multiplier',
        'Object_Motion_Blur_On_Off',
        'Point_Controller_Container'
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Declare private variables
        #
        self.skipProperties = kwargs.pop('skipProperties', False)
        self.skipSubAnims = kwargs.pop('skipSubAnims', False)
        self.skipCustomAttributes = kwargs.pop('skipCustomAttributes', False)
        self.skipKeys = kwargs.pop('skipKeys', False)
        self.skipChildren = kwargs.pop('skipChildren', False)
        self.skipShapes = kwargs.pop('skipShapes', False)
        self.skipLayers = kwargs.pop('skipLayers', False)
        self.skipSelectionSets = kwargs.pop('skipSelectionSets', False)
        self.skipMaterials = kwargs.pop('skipMaterials', False)
        self.suppress = kwargs.get('suppress', self.__suppress__)

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

        # Check if this is a mxs wrapper
        #
        if isinstance(obj, pymxs.MXSWrapperBase):

            # Evaluate mxs object type
            #
            if nodeutils.isValidScene(obj):

                log.info('Serializing scene: %s' % pymxs.runtime.maxFilename)
                return self.serializeScene(obj)

            elif nodeutils.isValidNode(obj):

                log.info('Serializing node: $%s' % obj.name)
                return self.serializeNode(obj)

            elif controllerutils.isValidSubAnim(obj):

                log.debug('Serializing sub-anim: %s' % obj.name)
                return self.serializeSubAnim(obj)

            elif controllerutils.isValidController(obj):

                log.debug('Serializing controller: %s' % obj)
                return self.delegateController(obj)

            elif layerutils.isValidLayer(obj):

                log.debug('Serializing layer: %s' % obj.name)
                return self.serializeLayer(obj)

            elif controllerutils.hasSubAnims(obj):

                log.debug('Serializing animatable: %s' % obj)
                return self.delegateMaxObject(obj)

            else:

                return super(MXSObjectEncoder, self).default(obj)

        else:

            return super(MXSObjectEncoder, self).default(obj)

    def serializeReferenceTarget(self, referenceTarget):
        """
        Returns a serializable object for the supplied reference target.

        :type referenceTarget: pymxs.MXSWrapperBase
        :rtype: dict
        """

        cls = pymxs.runtime.classOf(referenceTarget)
        classes = [str(cls) for cls in wrapperutils.iterBases(cls)]

        return {'class': str(cls), 'superClasses': classes}

    def serializeProperties(self, maxObject):
        """
        Returns a serializable object for the supplied max object's properties.

        :type maxObject: pymxs.MXSWrapperBase
        :rtype: Dict[str, Any]
        """

        return dict(
            propertyutils.iterStaticProperties(
                maxObject,
                skipAnimatable=True,
                skipNonValues=True
            )
        )

    def serializeSubAnim(self, subAnim):
        """
        Returns a serializable object for the supplied max sub anim.

        :type subAnim: pymxs.runtime.SubAnim
        :rtype: dict
        """

        # Serialize reference-target components
        #
        obj = self.serializeReferenceTarget(subAnim)

        # Serialize sub-anim components
        #
        obj['name'] = stringutils.slugify(str(subAnim.name), whitespace='_', illegal='_')
        obj['index'] = subAnim.index
        obj['isAnimated'] = getattr(subAnim, 'isAnimated', False)
        obj['controller'] = subAnim.controller
        obj['value'] = subAnim.value

        # Skip any node materials
        # These should be serialized from the scene materials array!
        #
        if pymxs.runtime.isValidNode(subAnim.parent) and pymxs.runtime.isKindOf(subAnim.value, pymxs.runtime.Material):

            obj['value'] = getattr(subAnim.value, 'name', '')

        return obj

    def delegateMaxObject(self, maxObject):
        """
       Delegates the supplied Max object to the required serializer.

       :type maxObject: pymxs.MXSWrapperBase
       :rtype: dict
       """

        # Check if node delegate exists
        #
        className = str(pymxs.runtime.classOf(maxObject))
        delegate = self.__object_types__.get(className, '')

        func = getattr(self, delegate, None)

        if callable(func):

            return func(maxObject)

        else:

            return self.serializeMaxObject(maxObject)

    def serializeMaxObject(self, maxObject, **kwargs):
        """
        Returns a serializable object for the supplied Max object.

        :type maxObject: pymxs.MXSWrapperBase
        :key skipProperties: bool
        :key skipSubAnims: bool
        :key skipCustomAttributes: bool
        :rtype: dict
        """

        # Serialize reference-target components
        #
        obj = self.serializeReferenceTarget(maxObject)

        # Serialize max-object components
        #
        obj['name'] = getattr(maxObject, 'name', '')
        obj['handle'] = nodeutils.getAnimHandle(maxObject)
        obj['path'] = wrapperutils.exprForMaxObject(maxObject)
        obj['properties'] = {}
        obj['subAnims'] = []
        obj['customAttributes'] = []

        # Check if properties should be skipped
        #
        skipProperties = kwargs.get('skipProperties', self.skipProperties)

        if not skipProperties:

            obj['properties'].update(self.serializeProperties(maxObject))

        # Check if sub-anims should be skipped
        #
        skipSubAnims = kwargs.get('skipSubAnims', self.skipSubAnims)

        if not skipSubAnims:

            obj['subAnims'].extend(list(controllerutils.iterSubAnims(maxObject)))

        # Check if custom-attributes should be skipped
        #
        skipCustomAttributes = kwargs.get('skipCustomAttributes', self.skipCustomAttributes)

        if not skipCustomAttributes:

            obj['customAttributes'].extend(list(attributeutils.iterDefinitions(maxObject, baseObject=False)))

        return obj

    def serializeNode(self, node):
        """
        Returns a serializable object for the supplied Max node.
        Any class-specific properties can be found in the modifier stack!

        :type node: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize max-object components
        #
        obj = self.serializeMaxObject(node, skipProperties=True, skipCustomAttributes=True)

        # Extend node properties
        #
        obj['wireColor'] = node.wireColor
        obj['lockFlags'] = pymxs.runtime.getTransformLockFlags(node)
        obj['inheritanceFlags'] = pymxs.runtime.getInheritanceFlags(node)
        obj['worldTransform'] = transformutils.getWorldMatrix(node)
        obj['objectTransform'] = node.objectTransform * pymxs.runtime.inverse(transformutils.getWorldMatrix(node))
        obj['userPropertyBuffer'] = pymxs.runtime.getUserPropBuffer(node)

        # Check if children should be skipped
        #
        obj['children'] = []

        if not self.skipChildren:

            obj['children'] = getattr(node, 'children', [])

        return obj

    def serializeSkin(self, skin):
        """
        Returns a serializable object for the supplied skin modifier.

        :type skin: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize max-object components
        #
        obj = self.serializeMaxObject(skin)

        # Check if skin-weights should be skipped
        #
        properties = obj['properties']
        properties['influences'] = {}
        properties['preBindMatrices'] = {}
        properties['weights'] = {}

        if not self.skipShapes:

            node = wrapperutils.getAssociatedNode(skin)

            properties['influences'] = {influenceId: nodeutils.getPartialPathTo(influence) for (influenceId, influence) in skinutils.iterInfluences(skin)}
            properties['preBindMatrices'] = {influenceId: pymxs.runtime.skinutils.getBoneBindTM(node, influence) for (influenceId, influence) in skinutils.iterInfluences(skin)}
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
        obj = self.serializeMaxObject(morpher)

        # Check if morph-targets should be skipped
        #
        properties = obj['properties']
        properties['channels'] = []

        if not self.skipShapes:

            properties['channels'] = [{'name': name, 'target': nodeutils.getPartialPathTo(target), 'weight': weight} for (name, target, weight) in morpherutils.iterTargets(morpher)]

        return obj

    def serializeExposeTm(self, exposeTransform):
        """
        Returns a serializable object for the supplied expose-transform.

        :type exposeTransform: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize node components
        #
        obj = self.serializeMaxObject(exposeTransform)

        # Extend expose-transform properties
        #
        properties = obj['properties']
        properties['exposeNode'] = nodeutils.getPartialPathTo(exposeTransform.exposeNode)
        properties['localReferenceNode'] = nodeutils.getPartialPathTo(exposeTransform.localReferenceNode)

        return obj

    def serializeSplineIKControl(self, splineIKControl):
        """
        Returns a serializable object for the supplied spline ik-control.

        :type splineIKControl: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize Max-object components
        #
        obj = self.serializeMaxObject(splineIKControl)

        # Extend spline ik-control properties
        #
        properties = obj['properties']
        properties['helper_list'] = [nodeutils.getPartialPathTo(x) for x in splineIKControl.helper_list]

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
        obj = self.serializeMaxObject(spline)

        # Check if shapes should be skipped
        #
        if not self.skipShapes:

            node = wrapperutils.getAssociatedNode(spline)
            numSplines = pymxs.runtime.numSplines(node)

            obj['properties']['splines'] = [self.serializeSpline(node, splineIndex=splineIndex) for splineIndex in inclusiveRange(1, numSplines)]

        return obj

    def serializeMap(self, poly, channel=0):
        """
        Returns a serializable object for the specified map channel.

        :type poly: pymxs.MXSWrapperBase
        :type channel: int
        :rtype: dict
        """

        isSupported = meshutils.isMapSupported(poly, channel)
        obj = {'supported': isSupported, 'vertices': [], 'faceVertexIndices': []}

        if isSupported:

            obj['vertices'] = list(meshutils.iterMapVertices(poly, channel=channel))
            obj['faceVertexIndices'] = list(meshutils.iterMapFaceVertexIndices(poly, channel=channel))

        return obj

    def serializeEditablePoly(self, poly):
        """
        Returns a serializable object for the supplied mesh object.

        :type poly: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize max-object components
        #
        obj = self.serializeMaxObject(poly)

        # Check if shapes should be skipped
        #
        if not self.skipShapes:

            properties = obj['properties']
            properties['vertices'] = list(meshutils.iterVertices(poly))
            properties['faceVertexIndices'] = list(meshutils.iterFaceVertexIndices(poly))
            properties['smoothingGroups'] = list(meshutils.iterSmoothingGroups(poly))
            properties['maps'] = [self.serializeMap(poly, channel=channel) for channel in range(meshutils.mapCount(poly))]
            properties['faceMaterialIndices'] = list(meshutils.iterFaceMaterialIndices(poly))

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
        delegate = self.__controller_types__.get(className, '')

        func = getattr(self, delegate, None)

        if callable(func):

            return func(controller)

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

        # Serialize max-object components
        #
        obj = self.serializeMaxObject(controller)

        # Extend controller properties
        #
        obj['value'] = controller.value
        obj['outOfRangeTypes'] = (pymxs.runtime.getBeforeORT(controller), pymxs.runtime.getAfterORT(controller))
        obj['keys'] = []

        # Check if keys should be included
        #
        skipKeys = kwargs.get('skipKeys', self.skipKeys)

        if not skipKeys and hasattr(controller, 'keys'):

            obj['keys'] = list(controllerutils.iterMaxKeys(controller))

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
        properties['targets'] = [nodeutils.getPartialPathTo(constraint.getNode(i)) for i in inclusiveRange(1, numTargets, 1)]

        # Serialize up-node
        #
        if pymxs.runtime.isProperty(constraint, 'pickUpNode'):

            properties['pickUpNode'] = nodeutils.getPartialPathTo(constraint.pickUpNode)

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
            properties['dependents'] = [{'controller': wrapperutils.exprForMaxObject(slaveAnimation), 'expression': expression}]

        else:

            # Iterate through wires
            #
            numWires = int(wire.numWires)
            properties['dependents'] = [None] * numWires

            for i in range(numWires):

                index = i + 1
                parent = wire.getWireParent(index)
                subAnim = wire.getWireSubNum(index)
                otherWire = pymxs.runtime.getSubAnim(parent, subAnim).controller
                expression = wire.getExprText(index)

                properties['dependents'][i] = {'controller': wrapperutils.exprForMaxObject(otherWire), 'expression': expression}

        return obj

    def serializeIkChainControl(self, ikChainControl):
        """
        Returns a serializable object for the supplied IK-chain controller.

        :type ikChainControl: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize controller components
        #
        obj = self.serializeController(ikChainControl)

        # Extend IK-Chain object properties
        #
        properties = obj['properties']
        properties['startJoint'] = nodeutils.getPartialPathTo(ikChainControl.startJoint)
        properties['endJoint'] = nodeutils.getPartialPathTo(ikChainControl.endJoint)
        properties['VHTarget'] = nodeutils.getPartialPathTo(ikChainControl.VHTarget)

        return obj

    def serializeSplineIKChain(self, splineIKChain):
        """
        Returns a serializable object for the supplied spline IK-chain controller.

        :type splineIKChain: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize controller components
        #
        obj = self.serializeController(splineIKChain)

        # Extend spline ik-chain properties
        #
        properties = obj['properties']
        properties['pickShape'] = nodeutils.getPartialPathTo(splineIKChain.pickShape)
        properties['startJoint'] = nodeutils.getPartialPathTo(splineIKChain.startJoint)
        properties['endJoint'] = nodeutils.getPartialPathTo(splineIKChain.endJoint)
        properties['upNode'] = nodeutils.getPartialPathTo(splineIKChain.upNode)

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
        properties['target'] = nodeutils.getPartialPathTo(node.target)
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

            obj['keys'].extend(list(controllerutils.iterAMaxKeys(attachment)))

        return obj

    def serializeLayer(self, layer):
        """
        Returns a serializable object for the supplied layer object.

        :type layer: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize max-object components
        #
        obj = self.serializeMaxObject(layer)

        # Extend layer properties
        #
        properties = obj['properties']
        properties['isHidden'] = layer.isHidden
        properties['isFrozen'] = layer.isFrozen
        properties['nodes'] = [nodeutils.getPartialPathTo(x) for x in layerutils.iterNodesFromLayers(layer)]

        # Add child layers
        #
        obj['children'] = [x.layerAsRefTarg for x in layerutils.iterChildLayers(layer)]

        return obj

    def serializeScene(self, scene):
        """
        Returns a serializable object for the supplied Max scene.

        :type scene: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize max-object components
        #
        obj = self.serializeReferenceTarget(scene)

        # Extend scene properties
        #
        obj['filename'] = pymxs.runtime.maxFilename
        obj['directory'] = os.path.normpath(pymxs.runtime.maxFilePath)
        obj['projectPath'] = sceneutils.projectPath()
        obj['properties'] = dict(sceneutils.iterFileProperties())
        obj['animationRange'] = pymxs.runtime.animationRange
        obj['frameRate'] = pymxs.runtime.frameRate
        obj['ticksPerFrame'] = pymxs.runtime.ticksPerFrame
        obj['selectionSets'] = {}
        obj['layers'] = []
        obj['materials'] = []
        obj['world'] = scene.world.children

        # Check if selection-sets should be skipped
        #
        if not self.skipSelectionSets:

            obj['selectionSets'].update({name: list(map(nodeutils.getAnimHandle, nodes)) for (name, nodes) in nodeutils.iterSelectionSets()})

        # Check if layers should be skipped
        #
        if not self.skipLayers:

            obj['layers'].extend([layer.layerAsRefTarg for layer in layerutils.iterTopLevelLayers()])

        # Check if materials should be skipped
        #
        if not self.skipMaterials:

            obj['materials'] = scene.scene_materials

        return obj
    # endregion
