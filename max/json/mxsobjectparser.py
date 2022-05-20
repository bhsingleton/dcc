import os
import pymxs

from dcc.python import stringutils
from dcc.max.json import mxsvalueparser
from dcc.max.libs import sceneutils, nodeutils, transformutils, meshutils
from dcc.max.libs import modifierutils, skinutils, morpherutils
from dcc.max.libs import layerutils, attributeutils, controllerutils, wrapperutils
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

    __node_types__ = {
        'SplineShape': 'serializeEditableSpline',
        'line': 'serializeEditableSpline',
        'Editable_Poly': 'serializeEditablePoly',
        'Editable_mesh': 'serializeEditablePoly'
    }

    __controller_types__ = {
        'IK_Chain_Object': 'serializeIkChainObject',
        'lookat': 'serializeLookAt'
    }

    __modifier_types__ = {
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

                log.debug('Serializing scene: %s' % pymxs.runtime.maxFilename)
                return self.serializeScene(obj)

            elif nodeutils.isValidNode(obj):

                log.info('Serializing node: $%s' % obj.name)
                return self.delegateNode(obj)

            elif controllerutils.isValidSubAnim(obj):

                log.debug('Serializing sub-anim: %s' % obj.name)
                return self.serializeSubAnim(obj)

            elif controllerutils.isValidController(obj):

                log.debug('Serializing controller: %s' % obj)
                return self.delegateController(obj)

            elif modifierutils.isValidModifier(obj):

                log.debug('Serializing modifier: %s' % obj)
                return self.delegateModifier(obj)

            elif layerutils.isValidLayer(obj):

                log.debug('Serializing layer: %s' % obj.name)
                return self.serializeLayer(obj)

            elif controllerutils.hasSubAnims(obj):

                log.debug('Serializing animatable: %s' % obj)
                return self.serializeMaxObject(obj)

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

        return {
            'class': str(pymxs.runtime.classOf(referenceTarget)),
            'superClass': str(pymxs.runtime.superClassOf(referenceTarget))
        }

    def serializeProperties(self, maxObject):
        """
        Returns a serializable object for the supplied max object's properties.

        :type maxObject: pymxs.MXSWrapperBase
        :rtype: Dict[str, Any]
        """

        return dict(
            controllerutils.iterStaticProperties(
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

        # Serialize reference target
        #
        obj = self.serializeReferenceTarget(subAnim)

        # Serialize sub-anim components
        #
        obj['name'] = stringutils.slugify(str(subAnim.name), illegal='_')
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

    def serializeMaxObject(self, maxObject):
        """
        Returns a serializable object for the supplied Max object.

        :type maxObject: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize reference target
        #
        obj = self.serializeReferenceTarget(maxObject)

        # Serialize max-object components
        #
        obj['name'] = getattr(maxObject, 'name', '')
        obj['handle'] = int(pymxs.runtime.getHandleByAnim(maxObject))
        obj['expression'] = wrapperutils.exprForMaxObject(maxObject)
        obj['properties'] = {}
        obj['subAnims'] = []
        obj['customAttributes'] = []

        # Check if properties should be skipped
        #
        if not self.skipProperties:

            obj['properties'].update(self.serializeProperties(maxObject))

        # Check if sub-anims should be skipped
        #
        if not self.skipSubAnims:

            obj['subAnims'].extend(list(controllerutils.iterSubAnims(maxObject)))

        # Check if custom-attributes should be skipped
        #
        if not self.skipCustomAttributes:

            obj['customAttributes'].extend(list(attributeutils.iterDefinitions(maxObject, baseObject=False)))

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

        elif controllerutils.isWireParameter(controller):

            return self.serializeWire(controller)

        else:

            return self.serializeController(controller)

    def serializeController(self, controller):
        """
        Returns a serializable object for the supplied max controller.

        :type controller: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize controller
        #
        obj = self.serializeReferenceTarget(controller)
        obj['expression'] = wrapperutils.exprForMaxObject(controller)
        obj['properties'] = {}
        obj['subAnims'] = []
        obj['outOfRangeTypes'] = (pymxs.runtime.getBeforeORT(controller), pymxs.runtime.getAfterORT(controller))
        obj['value'] = controller.value
        obj['keys'] = []

        # Check if properties should be included
        #
        if not self.skipProperties:

            obj['properties'].update(self.serializeProperties(controller))

        # Check if sub-anims should be included
        #
        if not self.skipSubAnims:

            obj['subAnims'].extend(list(controllerutils.iterSubAnims(controller)))

        # Check if keys should be included
        #
        if not self.skipKeys and hasattr(controller, 'keys'):

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

        # Serialize constraint targets
        #
        numTargets = constraint.getNumTargets()

        properties = obj['properties']
        properties['targets'] = [nodeutils.getPartialPathTo(constraint.getNode(x)) for x in inclusiveRange(1, numTargets)]

        # Serialize up-node
        #
        if pymxs.runtime.isProperty(constraint, 'pickUpNode'):

            properties['pickUpNode'] = nodeutils.getPartialPathTo(constraint.pickUpNode)

        return obj

    def serializeWire(self, wire):
        """
        Returns a serializable object for the supplied wire parameter.
        In order to avoid cyclical dependencies Max uses a parent controller with sub-anim index to point to other wires.

        :type wire: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize controller components
        #
        obj = self.serializeController(wire)

        # Serialize wire components
        #
        properties = obj['properties']
        properties['isMaster'] = wire.isMaster
        properties['isSlave'] = wire.isSlave
        properties['isTwoWay'] = wire.isTwoWay
        properties['dependents'] = [None] * wire.numWires

        for i in range(wire.numWires):

            index = i + 1
            parent = wire.getWireParent(index)
            subAnim = wire.getWireSubNum(index)
            otherWire = pymxs.runtime.getSubAnim(parent, subAnim).controller
            expression = wire.getExprText(index)

            properties['dependents'][i] = {'controller': wrapperutils.exprForMaxObject(otherWire), 'expression': expression}

        return obj

    def serializeIkChainObject(self, ikChainObject):
        """
        Returns a serializable object for the supplied max constraint.

        :type ikChainObject: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize controller components
        #
        obj = self.serializeController(ikChainObject)

        # Serialize start joint
        #
        properties = obj['properties']
        properties['startJoint'] = None

        if pymxs.runtime.isValidNode(ikChainObject.startJoint):

            properties['startJoint'] = nodeutils.getPartialPathTo(ikChainObject.startJoint)

        # Serialize end joint
        #
        properties['endJoint'] = None

        if pymxs.runtime.isValidNode(ikChainObject.endJoint):

            properties['endJoint'] = nodeutils.getPartialPathTo(ikChainObject.endJoint)

        # Serialize pole target
        #
        properties['VHTarget'] = None

        if pymxs.runtime.isValidNode(ikChainObject.VHTarget):

            properties['VHTarget'] = nodeutils.getPartialPathTo(ikChainObject.VHTarget)

        return obj

    def serializeLookAt(self, lookAt):
        """
        Returns a serializable object for the supplied lookat constraint.

        :type lookAt: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize controller components
        #
        obj = self.serializeController(lookAt)

        # Serialize properties
        # Since this controller is deprecated none of the properties are dynamically accessible
        #
        properties = obj['properties']
        properties['useTargetAsUpNode'] = lookAt.useTargetAsUpNode
        properties['axis'] = lookAt.axis
        properties['flip'] = lookAt.flip

        return obj

    def delegateModifier(self, modifier):
        """
        Delegates the supplied modifier to the required serializer.

        :type modifier: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Check if modifier delegate exists
        #
        className = str(pymxs.runtime.classOf(modifier))
        delegate = self.__modifier_types__.get(className, '')

        func = getattr(self, delegate, None)

        if callable(func):

            return func(modifier)

        else:

            return self.serializeMaxObject(modifier)

    def serializeSkin(self, skin):
        """
        Returns a serializable object for the supplied skin modifier.

        :type skin: pymxs.runtime.Skin
        :rtype: dict
        """

        # Serialize max-object
        #
        obj = self.serializeMaxObject(skin)

        # Check if skin-weights should be skipped
        #
        if not self.skipShapes:

            properties = obj['properties']
            properties['influences'] = {influenceId: nodeutils.getPartialPathTo(influence) for (influenceId, influence) in skinutils.iterInfluences(skin)}
            properties['weights'] = dict(skinutils.iterVertexWeights(skin))

        return obj

    def serializeMorpher(self, morpher):
        """
        Returns a serializable object for the supplied morpher modifier.

        :type morpher: pymxs.runtime.Morpher
        :rtype: dict
        """

        # Serialize max-object
        #
        obj = self.serializeMaxObject(morpher)

        # Check if morph-targets should be skipped
        #
        if not self.skipShapes:

            properties = obj['properties']
            properties['channels'] = [{'name': name, 'target': nodeutils.getPartialPathTo(target), 'weight': weight} for (name, target, weight) in morpherutils.iterTargets(morpher)]

        return obj

    def delegateNode(self, node):
        """
        Delegates the supplied node to the required serializer.

        :type node: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Check if node delegate exists
        #
        className = str(pymxs.runtime.classOf(node.baseObject))
        delegate = self.__node_types__.get(className, '')

        func = getattr(self, delegate, None)

        if callable(func):

            return func(node)

        else:

            return self.serializeNode(node)

    def serializeNode(self, node):
        """
        Returns a serializable object for the supplied max node.

        :type node: pymxs.runtime.Node
        :rtype: dict
        """

        # Serialize max object
        #
        obj = self.serializeMaxObject(node)
        obj['wireColor'] = node.wireColor
        obj['target'] = nodeutils.getPartialPathTo(node.target)  # Deprecated
        obj['path'] = nodeutils.getPartialPathTo(node)
        obj['worldTransform'] = transformutils.getWorldMatrix(node)
        obj['objectTransform'] = node.objectTransform * pymxs.runtime.inverse(transformutils.getWorldMatrix(node))
        obj['userPropertyBuffer'] = pymxs.runtime.getUserPropBuffer(node)
        obj['children'] = []

        # Check if children should be skipped
        #
        if not self.skipChildren and hasattr(node, 'children'):

            obj['children'] = node.children

        return obj

    @coordsysoverride.coordSysOverride(mode='world')
    def serializeSplineKnots(self, spline, splineIndex=1):
        """
        Serializes the knots for the given spline.

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

    def serializeSplineShape(self, spline, splineIndex=1):
        """
        Returns a serializable object for the specified spline shape.

        :type spline: pymxs.MXSWrapperBase
        :type splineIndex: int
        :rtype: dict
        """

        return {
            'isClosed': pymxs.runtime.isClosed(spline, splineIndex),
            'knots': self.serializeSplineKnots(spline, splineIndex=splineIndex)
        }

    def serializeEditableSpline(self, spline):
        """
        Returns a serializable object for the supplied spline object.

        :type spline: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize iNode components
        #
        obj = self.serializeNode(spline)

        # Serialize spline shapes
        #
        if not self.skipShapes:

            numSplines = pymxs.runtime.numSplines(spline)

            properties = obj['properties']
            properties['splines'] = [self.serializeSplineShape(spline, splineIndex=splineIndex) for splineIndex in inclusiveRange(1, numSplines)]

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

        # Serialize node components
        #
        obj = self.serializeNode(poly)

        # Serialize mesh components
        #
        if not self.skipShapes:

            properties = obj['properties']
            properties['vertices'] = list(meshutils.iterVertices(poly))
            properties['faceVertexIndices'] = list(meshutils.iterFaceVertexIndices(poly))
            properties['smoothingGroups'] = list(meshutils.iterSmoothingGroups(poly))
            properties['maps'] = [self.serializeMap(poly, channel=channel) for channel in range(meshutils.mapCount(poly))]
            properties['faceMaterialIndices'] = list(meshutils.iterFaceMaterialIndices(poly))
            properties['material'] = int(pymxs.runtime.getHandleByAnim(poly.material)) if poly.material is not None else None

        return obj

    def serializeLayer(self, layer):
        """
        Returns a serializable object for the supplied layer target.

        :type layer: pymxs.MXSWrapperBase
        :rtype: dict
        """

        obj = self.serializeReferenceTarget(layer)
        obj['name'] = layer.name
        obj['isHidden'] = layer.isHidden
        obj['isFrozen'] = layer.isFrozen
        obj['nodes'] = [nodeutils.getPartialPathTo(x) for x in layerutils.iterNodesFromLayers(layer)]
        obj['children'] = [x.layerAsRefTarg for x in layerutils.iterChildLayers(layer)]

        return obj

    def serializeScene(self, scene):
        """
        Returns a serializable object for the supplied Max scene.

        :type scene: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize reference target
        #
        obj = self.serializeReferenceTarget(scene)

        # Serialize scene components
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

            obj['selectionSets'].update({name: list(map(nodeutils.getPartialPathTo, nodes)) for (name, nodes) in nodeutils.iterSelectionSets()})

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
