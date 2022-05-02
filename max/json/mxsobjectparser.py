import re
import pymxs

from dcc.python import stringutils
from dcc.max.json import mxsvalueparser
from dcc.max.libs import sceneutils, nodeutils, skinutils, meshutils, attributeutils, controllerutils, modifierutils
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
        'skipModifiers',
        'skipCustomAttributes',
        'skipKeys',
        'skipChildren'
    )

    __nodetypes__ = {
        'Point': 'serializeNode',
        'BoneGeometry': 'serializeNode',
        'SplineShape': 'serializeEditableSpline',
        'line': 'serializeEditableSpline',
        'Editable_Poly': 'serializeEditablePoly',
        'Editable_mesh': 'serializeEditablePoly'
    }

    __modifiertypes__ = {'Skin': 'serializeSkin'}

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Declare private variables
        #
        self.skipProperties = kwargs.pop('skipProperties', False)
        self.skipSubAnims = kwargs.pop('skipSubAnims', False)
        self.skipModifiers = kwargs.pop('skipModifiers', False)
        self.skipCustomAttributes = kwargs.pop('skipCustomAttributes', False)
        self.skipKeys = kwargs.pop('skipKeys', False)
        self.skipChildren = kwargs.pop('skipChildren', False)
        self.skipShapes = kwargs.pop('skipShapes', False)

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
            if pymxs.runtime.isKindOf(obj, pymxs.runtime.Scene):

                return self.serializeScene(obj)

            elif pymxs.runtime.isValidNode(obj):

                log.info('Serializing node: $%s' % obj.name)
                return self.delegateNode(obj)

            elif controllerutils.isValidSubAnim(obj):

                log.debug('Serializing sub-anim: %s' % obj.name)
                return self.serializeSubAnim(obj)

            elif controllerutils.isValidController(obj):

                log.debug('Serializing controller: %s' % str(pymxs.runtime.classOf(obj)))
                return self.delegateController(obj)

            elif modifierutils.isValidModifier(obj):

                log.debug('Serializing modifier: %s' % str(pymxs.runtime.classOf(obj)))
                return self.delegateModifier(obj)

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
            controllerutils.iterProperties(
                maxObject,
                skipAnimatable=True,
                skipComplexValues=True,
                skipDefaultValues=True
            )
        )

    def serializeSubAnim(self, subAnim):
        """
        Returns a serializable object for the supplied max sub anim.

        :type subAnim: pymxs.runtime.SubAnim
        :rtype: dict
        """

        obj = self.serializeReferenceTarget(subAnim)
        obj['name'] = stringutils.slugify(getattr(subAnim, 'name', ''))
        obj['index'] = subAnim.index
        obj['value'] = subAnim.value
        obj['isAnimated'] = getattr(subAnim, 'isAnimated', False)
        obj['controller'] = subAnim.controller

        return obj

    def serializeAnimatable(self, animatable):
        """
        Returns a serializable object for the supplied max object.

        :type animatable: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize reference target
        #
        obj = self.serializeReferenceTarget(animatable)
        obj['name'] = stringutils.slugify(getattr(animatable, 'name', ''))  # Maya does not accept illegal characters!
        obj['expression'] = pymxs.runtime.exprForMaxObject(animatable)
        obj['properties'] = {}
        obj['subAnims'] = []

        # Check if properties should be included
        #
        if not self.skipProperties:

            obj['properties'].update(self.serializeProperties(animatable))

        # Check if sub-anims should be included
        #
        if not self.skipSubAnims:

            obj['subAnims'].extend(list(controllerutils.iterSubAnims(animatable, skipComplexValues=True)))

        return obj

    def delegateController(self, controller):
        """
        Delegates the supplied controller to the required serializer.

        :type controller: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Check if this is a list controller
        #
        if controllerutils.isListController(controller):

            return self.serializeListController(controller)

        elif controllerutils.isConstraint(controller):

            return self.serializeConstraint(controller)

        elif controllerutils.isWireParameter(controller):

            return self.serializeWireParameter(controller)

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
        obj['expression'] = pymxs.runtime.exprForMaxObject(controller)
        obj['properties'] = self.serializeProperties(controller)
        obj['subAnims'] = list(controllerutils.iterSubAnims(controller, skipComplexValues=True))
        obj['value'] = controller.value
        obj['keys'] = []

        # Check if keys should be included
        #
        if not self.skipKeys and hasattr(controller, 'keys'):

            obj['keys'] = list(controllerutils.iterMaxKeys(controller))

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
        obj['subAnims'].clear()

        # Serialize list components
        #
        controllers = controller.list
        controllerCount = controllers.getCount()

        obj['active'] = controllers.getActive()
        obj['list'] = [{'name': controllers.getName(x), 'controller': controllers.getSubCtrl(x), 'weight': controllers.getSubCtrlWeight(x)} for x in inclusiveRange(1, controllerCount,)]

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
        obj['subAnims'].clear()

        # Serialize constraint-target components
        #
        numTargets = constraint.getNumTargets()
        obj['targets'] = [None] * numTargets

        for i in range(numTargets):

            index = i + 1
            name = constraint.getNode(index).name
            weight = constraint.getWeight(index) if hasattr(constraint, 'getWeight') else 1.0

            obj['targets'][i] = {'name': name, 'weight': weight}

        return obj

    def serializeWireParameter(self, wire):
        """
        Returns a serializable object for the supplied wire parameter.
        In order to avoid cyclical dependencies Max uses a parent controller with sub-anim index to point to other wires.

        :type wire: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize controller components
        #
        obj = self.serializeController(wire)
        obj['subAnims'].clear()

        # Serialize wire components
        #
        obj['isMaster'] = wire.isMaster
        obj['isSlave'] = wire.isSlave
        obj['isTwoWay'] = wire.isTwoWay
        obj['dependents'] = [None] * wire.numWires

        for i in range(wire.numWires):

            index = i + 1
            parent = wire.getWireParent(index)
            subAnim = wire.getWireSubNum(index)
            otherWire = pymxs.runtime.getSubAnim(parent, subAnim).controller
            expression = wire.getExprText(index)

            obj['dependents'][i] = {'controller': pymxs.runtime.exprForMaxObject(otherWire), 'expression': expression}

        return obj

    def delegateModifier(self, modifier):
        """
        Delegates the supplied modifier to the required serializer.

        :type modifier: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Inspect modifier class
        #
        className = str(pymxs.runtime.classOf(modifier))
        delegate = self.__modifiertypes__.get(className, '')
        func = getattr(self, delegate, None)

        if callable(func):

            return func(modifier)

        else:
            
            log.warning('No modifier delegate found for: %s' % className)
            return self.serializeAnimatable(modifier)

    def serializeSkin(self, skin):
        """
        Returns a serializable object for the supplied skin modifier.

        :type skin: pymxs.runtime.Skin
        :rtype: dict
        """

        # Serialize animatable components
        #
        obj = self.serializeAnimatable(skin)

        # Serialize influences and vertex weights
        #
        obj['influences'] = {influenceId: influence.name for (influenceId, influence) in skinutils.iterInfluences(skin)}
        obj['weights'] = dict(skinutils.iterVertexWeights(skin))

        return obj

    def delegateNode(self, node):
        """
        Delegates the supplied node to the required serializer.

        :type node: pymxs.MXSWrapperBase
        :rtype: dict
        """

        className = str(pymxs.runtime.classOf(node.baseObject))
        delegate = self.__nodetypes__.get(className, '')
        func = getattr(self, delegate, None)

        if callable(func):

            return func(node)

        else:
            
            log.warning('No node delegate found for: %s' % className)
            return self.serializeNode(node)

    def serializeNode(self, node):
        """
        Returns a serializable object for the supplied max node.

        :type node: pymxs.runtime.Node
        :rtype: dict
        """

        # Serialize animatable
        #
        obj = self.serializeAnimatable(node)
        obj['handle'] = node.handle
        obj['dagPath'] = nodeutils.dagPath(node)
        obj['wireColor'] = node.wireColor
        obj['objectTransform'] = node.objectTransform
        obj['userPropertyBuffer'] = pymxs.runtime.getUserPropBuffer(node)
        obj['modifiers'] = []
        obj['customAttributes'] = []
        obj['children'] = []

        # Check if modifiers should be skipped
        #
        if not self.skipModifiers and hasattr(node, 'modifiers'):

            obj['modifiers'] = list(node.modifiers)

        # Check if custom attributes should be skipped
        #
        if not self.skipCustomAttributes:

            obj['customAttributes'] = [self.serializeAnimatable(x) for x in attributeutils.iterDefinitions(node)]

        # Check if children should be skipped
        #
        if not self.skipChildren and hasattr(node, 'children'):

            obj['children'] = node.children

        return obj

    @coordsysoverride.coordSysOverride(mode='parent')
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

        for i in range(numKnots):

            # Evaluate knot type
            #
            knotIndex = i + 1
            knotType = pymxs.runtime.getKnotType(spline, splineIndex, knotIndex)

            knot = {'type': knotType, 'inVec': None, 'point': None, 'outVec': None}
            knots[i] = knot

            if knotType in (pymxs.runtime.Name('corner'), pymxs.runtime.Name('bezierCorner')):

                knot['point'] = pymxs.runtime.getKnotPoint(spline, splineIndex, knotIndex)

            elif knotType in (pymxs.runtime.Name('smooth'), pymxs.runtime.Name('bezier')):

                # Extract bezier handles
                #
                if knotIndex == 1:

                    knot['point'] = pymxs.runtime.getKnotPoint(spline, splineIndex, knotIndex)
                    knot['outVec'] = pymxs.runtime.getOutVec(spline, splineIndex, knotIndex)

                elif 1 < knotIndex <= numKnots:

                    knot['inVec'] = pymxs.runtime.getInVec(spline, splineIndex, knotIndex)
                    knot['point'] = pymxs.runtime.getKnotPoint(spline, splineIndex, knotIndex)
                    knot['outVec'] = pymxs.runtime.getOutVec(spline, splineIndex, knotIndex)

                else:

                    knot['inVec'] = pymxs.runtime.getInVec(spline, splineIndex, knotIndex)
                    knot['point'] = pymxs.runtime.getKnotPoint(spline, splineIndex, knotIndex)

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
        obj['splines'] = []

        if not self.skipShapes:

            numSplines = pymxs.runtime.numSplines(spline)
            obj['splines'] = [self.serializeSplineShape(spline, splineIndex=splineIndex) for splineIndex in inclusiveRange(1, numSplines)]

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

        # Serialize iNode components
        #
        obj = self.serializeNode(poly)

        # Serialize mesh components
        #
        obj['vertices'] = []
        obj['faceVertexIndices'] = []
        obj['smoothingGroups'] = []
        obj['maps'] = []

        if not self.skipShapes:

            obj['vertices'] = list(meshutils.iterVertices(poly))
            obj['faceVertexIndices'] = list(meshutils.iterFaceVertexIndices(poly))
            obj['smoothingGroups'] = list(meshutils.iterSmoothingGroups(poly))
            obj['maps'] = [self.serializeMap(poly, channel=channel) for channel in range(meshutils.mapCount(poly))]

        return obj

    def serializeScene(self, scene):
        """
        Returns a serializable object for the supplied max scene.

        :type scene: pymxs.MXSWrapperBase
        :rtype: dict
        """

        obj = self.serializeReferenceTarget(scene)
        obj['filename'] = pymxs.runtime.maxFilename
        obj['directory'] = pymxs.runtime.maxFilePath
        obj['projectPath'] = sceneutils.projectPath()
        obj['properties'] = dict(sceneutils.iterFileProperties())
        obj['animationRange'] = pymxs.runtime.animationRange
        obj['frameRate'] = pymxs.runtime.frameRate
        obj['selectionSets'] = []
        obj['layers'] = []
        obj['world'] = scene.world.children

        return obj
    # endregion
