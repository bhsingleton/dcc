import os
import math
import fbx
import FbxCommon

from itertools import chain
from ... import __application__, DCC, fnscene, fnnode, fntransform, fnmesh, fnskin
from ...python import stringutils
from ...generators.inclusiverange import inclusiveRange

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def getEnumMember(obj, member, cls=None):
    """
    Returns the enum member value from the supplied object.
    If no enum member exists then the enum class is inspected next.
    When enum classes were introduced into python all legacy enum members were consolidated back into their original enum class!

    :type obj: object
    :type member: str
    :type cls: object
    :rtype: Any
    """

    try:

        return getattr(obj, member)

    except AttributeError:

        return getattr(cls, member)


class FbxSerializer(object):
    """
    Base class used for composing fbx files from DCC scene nodes.
    This exporter was created to ensure that the DCC scene data was as clean as possible for game engines.
    This exporter supports animation baking at a decimal framerate to help reduce euler filter abnormalities.
    TODO: Implement support for blendshapes!
    """

    # region Dunderscores
    __slots__ = (
        '_scene',
        '_namespace',
        '_fbxScene',
        '_fbxManager',
        '_fbxAnimStack',
        '_fbxAnimLayer',
        '_fbxNodes'
    )

    __up_axes__ = {
        'x': getEnumMember(fbx.FbxAxisSystem, 'eXAxis', cls=fbx.FbxAxisSystem.EUpVector),
        'y': getEnumMember(fbx.FbxAxisSystem, 'eYAxis', cls=fbx.FbxAxisSystem.EUpVector),
        'z': getEnumMember(fbx.FbxAxisSystem, 'eZAxis', cls=fbx.FbxAxisSystem.EUpVector)
    }

    __unit_types__ = {
        'millimeter': fbx.FbxSystemUnit.mm,
        'centimeter': fbx.FbxSystemUnit.cm,
        'meter': fbx.FbxSystemUnit.m,
        'kilometer': fbx.FbxSystemUnit.km,
        'inch': fbx.FbxSystemUnit.Inch,
        'foot': fbx.FbxSystemUnit.Foot,
        'yard': fbx.FbxSystemUnit.Yard,
        'mile': fbx.FbxSystemUnit.Mile,
    }

    __data_types__ = {
        'bool': fbx.FbxBoolDT,
        'int': fbx.FbxUIntDT,
        'float': fbx.FbxDoubleDT,
        'str': fbx.FbxStringDT
    }

    __rotate_orders__ = {
        'xyz': getEnumMember(fbx, 'eEulerXYZ', cls=fbx.EFbxRotationOrder),
        'xzy': getEnumMember(fbx, 'eEulerXZY', cls=fbx.EFbxRotationOrder),
        'yzx': getEnumMember(fbx, 'eEulerYZX', cls=fbx.EFbxRotationOrder),
        'yxz': getEnumMember(fbx, 'eEulerYXZ', cls=fbx.EFbxRotationOrder),
        'zxy': getEnumMember(fbx, 'eEulerZXY', cls=fbx.EFbxRotationOrder),
        'zyx': getEnumMember(fbx, 'eEulerZYX', cls=fbx.EFbxRotationOrder)
    }

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(FbxSerializer, self).__init__()

        # Declare class variables
        #
        self._scene = fnscene.FnScene()
        self._namespace = kwargs.get('namespace', '')
        self._fbxManager, self._fbxScene = FbxCommon.InitializeSdkObjects()
        self._fbxAnimStack = fbx.FbxAnimStack.Create(self.fbxManager, 'Take 001')
        self._fbxAnimLayer = fbx.FbxAnimLayer.Create(self.fbxManager, 'BaseLayer')
        self._fbxNodes = {}  # type: Dict[int, fbx.FbxNode]

        # Initialize scene settings
        #
        self.copySystemAxis()
        self.copySystemUnits()

        # Initialize anim stack
        # All FBXs require at least one animation layer!
        #
        self.fbxScene.AddMember(self.fbxAnimStack)
        self.fbxScene.SetCurrentAnimationStack(self.fbxAnimStack)

        self.fbxAnimStack.AddMember(self.fbxAnimLayer)
    # endregion

    # region Properties
    @property
    def scene(self):
        """
        Getter method that returns the DCC scene interface.

        :rtype: fnscene.FnScene
        """

        return self._scene

    @property
    def namespace(self):
        """
        Getter method that returns the global namespace.

        :rtype: str
        """

        return self._namespace

    @property
    def fbxScene(self):
        """
        Getter method that returns the Fbx scene.

        :rtype: fbx.FbxScene
        """

        return self._fbxScene

    @property
    def fbxManager(self):
        """
        Getter method that returns the Fbx manager.

        :rtype: fbx.FbxManager
        """

        return self._fbxManager

    @property
    def fbxAnimStack(self):
        """
        Getter method that returns the Fbx animation stack.

        :rtype: fbx.FbxAnimStack
        """

        return self._fbxAnimStack

    @property
    def fbxAnimLayer(self):
        """
        Getter method that returns the Fbx animation layer.

        :rtype: fbx.FbxAnimLayer
        """

        return self._fbxAnimLayer

    @property
    def fbxNodes(self):
        """
        Returns a collection of handle-node pairs that have been created.

        :rtype: Dict[int, fbx.FbxNode]
        """

        return self._fbxNodes
    # endregion

    # region Methods
    def copySystemAxis(self):
        """
        Copies the system axis settings from the current scene file.

        :rtype: None
        """

        globalSettings = self.fbxScene.GetGlobalSettings()

        if __application__ == DCC.MAYA:

            upAxis = self.scene.getUpAxis()
            axisSystem = fbx.FbxAxisSystem.MayaYUp if upAxis == 'y' else fbx.FbxAxisSystem.MayaZUp
            globalSettings.SetAxisSystem(axisSystem)

        elif __application__ == DCC.MAX:

            globalSettings.SetAxisSystem(fbx.FbxAxisSystem.Max)

        else:

            pass

    def copySystemUnits(self):
        """
        Copies the system unit settings from the current scene file.

        :rtype: None
        """

        globalSettings = self.fbxScene.GetGlobalSettings()
        globalSettings.SetSystemUnit(fbx.FbxSystemUnit.cm)  # TODO: Implement support for other unit types!

    def updateTimeRange(self, startFrame, endFrame):
        """
        Updates the FBX time range using the specified start and end frames.

        :type startFrame: Union[int, float]
        :type endFrame: Union[int, float]
        :rtype: None
        """

        timeMode = getEnumMember(fbx.FbxTime, 'eFrames30', cls=fbx.FbxTime.EMode)  # TODO: Add support for other time modes!

        globalSettings = self.fbxScene.GetGlobalSettings()
        globalSettings.SetTimeMode(timeMode)
        globalSettings.SetTimelineDefaultTimeSpan(
            fbx.FbxTimeSpan(
                self.convertFrameToTime(startFrame),
                self.convertFrameToTime(endFrame)
            )
        )

    def hasHandle(self, handle):
        """
        Evaluates if an fbx node with the given handle already exists.

        :type handle: int
        :rtype: bool
        """

        return self.fbxNodes.get(handle, None) is not None

    def getFbxNodeByHandle(self, handle):
        """
        Returns the Fbx node associated with the supplied DCC node's handle.

        :type handle: int
        :rtype: fbx.FbxNode
        """

        return self._fbxNodes.get(handle, None)

    def getAssociatedNode(self, fbxNode):
        """
        Returns the scene node associated with the supplied fbx node.

        :type fbxNode: fbx.FbxNode
        :rtype: Any
        """

        fbxProperty = fbxNode.FindProperty('handle')
        handle = int(str(fbx.FbxPropertyString(fbxProperty).Get()))

        return fnnode.FnNode.getNodeByHandle(handle)

    def allocateFbxNodes(self, *nodes):
        """
        Reserves space for the supplied nodes.

        :rtype: None
        """

        # Evaluate supplied nodes
        #
        numNodes = len(nodes)

        if numNodes > 0:

            node = fnnode.FnNode(iter(nodes))

            while not node.isDone():

                self.createFbxNode(node)
                node.next()

        else:

            log.debug('No nodes supplied to allocate!')

    def ensureParent(self, copyFrom, copyTo, **kwargs):
        """
        Ensures the fbx node has the same equivalent parent node.

        :type copyFrom: fnnode.FnNode
        :type copyTo: fbx.FbxNode
        :rtype: None
        """

        # Check if node has a parent
        #
        parent = fntransform.FnTransform()
        success = parent.trySetObject(copyFrom.parent())

        rootNode = self.fbxScene.GetRootNode()

        if not success:

            rootNode.AddChild(copyTo)
            return

        # Check if equivalent parent exists
        #
        handle = parent.handle()

        if self.hasHandle(handle):

            fbxParent = self.getFbxNodeByHandle(handle)
            fbxParent.AddChild(copyTo)

        else:

            rootNode.AddChild(copyTo)

    def moveToOrigin(self):
        """
        Moves all the root objects to origin.

        :rtype: None
        """

        # Iterate through root nodes
        #
        rootNode = self.fbxScene.GetRootNode()
        childCount = rootNode.GetChildCount()

        animStack = self.fbxScene.GetCurrentAnimationStack()  # type: fbx.FbxAnimStack

        for i in range(childCount):

            # Clear transform keys
            #
            childNode = rootNode.GetChild(i)

            for component in (childNode.LclTranslation, childNode.LclRotation, childNode.LclScaling):

                # Get anim-curve node
                #
                animCurveNode = component.GetCurveNode(animStack, False)

                if animCurveNode is None:

                    continue

                # Reset anim-curve channels
                #
                animCurveNode.ResetChannels()
                animCurveNode.Destroy(True)

            # Reset transform properties
            #
            fnChildNode = fntransform.FnTransform(self.getAssociatedNode(childNode))
            bindMatrix = fnChildNode.bindMatrix()

            translation = bindMatrix.translation()
            order = fnChildNode.rotationOrder()
            eulerAngles = list(map(math.degrees, bindMatrix.eulerRotation(order=order)))
            scale = bindMatrix.scale()

            childNode.LclTranslation.Set(fbx.FbxDouble3(translation.x, translation.y, translation.z))
            childNode.RotationPivot.Set(fbx.FbxDouble3(0.0, 0.0, 0.0))
            childNode.PreRotation.Set(fbx.FbxDouble3(0.0, 0.0, 0.0))
            childNode.LclRotation.Set(fbx.FbxDouble3(eulerAngles[0], eulerAngles[1], eulerAngles[2]))
            childNode.PostRotation.Set(fbx.FbxDouble3(0.0, 0.0, 0.0))
            childNode.LclScaling.Set(fbx.FbxDouble3(scale.x, scale.y, scale.z))

    def copyTransform(self, copyFrom, copyTo, **kwargs):
        """
        Copies the local transform values from the supplied scene node to the specified fbx node.

        :type copyFrom: fntransform.FnTransform
        :type copyTo: fbx.FbxNode
        :rtype: None
        """

        # Edit transformation inheritance
        # Uppercase letters represent parent (rotation/scaling) and lowercase for child (rotation/scaling)!
        #
        inverseScaleEnabled = copyFrom.inverseScaleEnabled()
        inheritType = None

        if inverseScaleEnabled:

            inheritType = getEnumMember(fbx.FbxTransform, 'eInheritRrs', cls=fbx.FbxTransform.EInheritType)
            copyTo.SetTransformationInheritType(inheritType)

        else:

            inheritType = getEnumMember(fbx.FbxTransform, 'eInheritRSrs', cls=fbx.FbxTransform.EInheritType)
            copyTo.SetTransformationInheritType(inheritType)

        # Update local translation
        #
        matrix = copyFrom.matrix()
        globalScale = kwargs.get('globalScale', 1.0)
        translation = matrix.translation() * globalScale

        copyTo.LclTranslation.Set(fbx.FbxDouble3(*translation))

        # Update local rotation in degrees
        #
        pivotType = getEnumMember(fbx.FbxNode, 'eSourcePivot', cls=fbx.FbxNode.EPivotSet)
        order = copyFrom.rotationOrder()
        eulerAngles = list(map(math.degrees, matrix.eulerRotation(order=order)))

        copyTo.SetRotationActive(True)
        copyTo.SetRotationOrder(pivotType, self.__class__.__rotate_orders__[order])
        copyTo.LclRotation.Set(fbx.FbxDouble3(*eulerAngles))

        # Update local scale
        #
        scale = matrix.scale()
        copyTo.LclScaling.Set(fbx.FbxDouble3(*scale))

    def copyMesh(self, copyFrom, copyTo, **kwargs):
        """
        Copies the mesh data from the supplied scene node to the specified fbx node.

        :type copyFrom: fnmesh.FnMesh
        :type copyTo: fbx.FbxMesh
        :rtype: None
        """

        # Assign triangulated mesh to function set
        #
        original = copyFrom.object()
        triangulated = copyFrom.triangulatedObject()

        success = copyFrom.trySetObject(triangulated)

        if not success:

            log.warning(f'Unable to locate triangulated mesh @ {copyFrom.name()}')
            return

        # Initialize control points
        #
        numControlPoints = copyFrom.numVertices()
        copyTo.InitControlPoints(numControlPoints)

        globalScale = kwargs.get('globalScale', 1.0)

        for (index, controlPoint) in enumerate(copyFrom.iterVertices()):

            scaledControlPoint = controlPoint * globalScale
            copyTo.SetControlPointAt(fbx.FbxVector4(*scaledControlPoint), index)

        # Define face-vertex relationships
        #
        normalizeIndex = lambda i: i - copyFrom.arrayIndexType
        normalizeIndices = lambda x: tuple(map(normalizeIndex, x))

        faceVertexIndices = tuple(map(normalizeIndices, copyFrom.iterFaceVertexIndices()))
        numFaceVertices = sum(map(len, faceVertexIndices))

        for (faceIndex, faceVertexIndices) in enumerate(faceVertexIndices):

            # Define face-vertex composition
            #
            copyTo.BeginPolygon(faceIndex)

            for vertexIndex in faceVertexIndices:

                copyTo.AddPolygon(vertexIndex)

            # Mark polygon as complete
            #
            copyTo.EndPolygon()

        # Build mesh edge array
        # This should only be called AFTER the face-vertex relationships have been defined!
        #
        copyTo.BuildMeshEdgeArray()

        # Assign material elements
        #
        mappingMode = getEnumMember(fbx.FbxLayerElement, 'eByPolygon', cls=fbx.FbxLayerElement.EMappingMode)
        referenceMode = getEnumMember(fbx.FbxLayerElement, 'eIndexToDirect', cls=fbx.FbxLayerElement.EReferenceMode)
        faceMaterialIndices = tuple(map(normalizeIndex, copyFrom.iterFaceMaterialIndices()))

        materialElement = copyTo.GetElementMaterial()
        materialElement.SetMappingMode(mappingMode)
        materialElement.SetReferenceMode(referenceMode)

        indexArray = materialElement.GetIndexArray()
        indexArray.SetCount(copyFrom.numFaces())

        for (insertAt, materialIndex) in enumerate(faceMaterialIndices):

            indexArray.SetAt(insertAt, materialIndex)

        # Check if normals should be included
        #
        includeNormals = kwargs.get('includeNormals', False)

        if includeNormals:

            # Initialize new normal element
            #
            mappingMode = getEnumMember(fbx.FbxLayerElement, 'eByPolygonVertex', cls=fbx.FbxLayerElement.EMappingMode)
            referenceMode = getEnumMember(fbx.FbxLayerElement, 'eIndexToDirect', cls=fbx.FbxLayerElement.EReferenceMode)

            normalElement = copyTo.CreateElementNormal()
            normalElement.SetMappingMode(mappingMode)
            normalElement.SetReferenceMode(referenceMode)

            # Assign normals
            #
            faceVertexNormals = copyFrom.iterFaceVertexNormals()

            directArray = normalElement.GetDirectArray()
            directArray.SetCount(numFaceVertices)

            indexArray = normalElement.GetIndexArray()
            indexArray.SetCount(numFaceVertices)

            for (index, normal) in enumerate(chain(*faceVertexNormals)):

                directArray.SetAt(index, fbx.FbxVector4(normal[0], normal[1], normal[2], 1.0))
                indexArray.SetAt(index, index)

        else:

            log.info('Skipping face-vertex normals...')

        # Check if smoothings should be included
        #
        includeSmoothings = kwargs.get('includeSmoothings', False)

        if includeSmoothings:

            # Check if mesh uses edge smoothings
            #
            if copyFrom.hasEdgeSmoothings():

                # Initialize new edge smoothing element
                #
                mappingMode = getEnumMember(fbx.FbxLayerElement, 'eByEdge', cls=fbx.FbxLayerElement.EMappingMode)
                referenceMode = getEnumMember(fbx.FbxLayerElement, 'eDirect', cls=fbx.FbxLayerElement.EReferenceMode)

                smoothingElement = copyTo.CreateElementSmoothing()
                smoothingElement.SetMappingMode(mappingMode)
                smoothingElement.SetReferenceMode(referenceMode)

                # Assign edge smoothings
                #
                edgeSmoothings = copyFrom.getEdgeSmoothings()
                numEdgeSmoothings = len(edgeSmoothings)

                directArray = smoothingElement.GetDirectArray()
                directArray.SetCount(numEdgeSmoothings)

                for (index, smooth) in enumerate(edgeSmoothings):

                    directArray.SetAt(index, smooth)

            elif copyFrom.hasSmoothingGroups():

                # Initialize new smoothing group element
                #
                mappingMode = getEnumMember(fbx.FbxLayerElement, 'eByPolygon', cls=fbx.FbxLayerElement.EMappingMode)
                referenceMode = getEnumMember(fbx.FbxLayerElement, 'eDirect', cls=fbx.FbxLayerElement.EReferenceMode)

                smoothingElement = copyTo.CreateElementSmoothing()
                smoothingElement.SetMappingMode(mappingMode)
                smoothingElement.SetReferenceMode(referenceMode)

                # Assign smoothing groups
                #
                smoothingGroups = copyFrom.getSmoothingGroups()
                numSmoothingGroups = len(smoothingGroups)

                directArray = smoothingElement.GetDirectArray()
                directArray.SetCount(numSmoothingGroups)

                for (index, groupIndex) in enumerate(smoothingGroups):

                    directArray.SetAt(index, groupIndex)

        else:

            log.info('Skipping smoothings...')

        # Check if vertex colors should be included
        #
        includeColorSets = kwargs.get('includeColorSets', False)

        if includeColorSets:

            # Iterate through all color sets
            #
            colorSetNames = copyFrom.getColorSetNames()

            for (channel, colorSetName) in enumerate(colorSetNames):

                # Create new color set element
                #
                log.info(f'Creating "{colorSetName}" colour set...')
                mappingMode = getEnumMember(fbx.FbxLayerElement, 'eByPolygonVertex', cls=fbx.FbxLayerElement.EMappingMode)
                referenceMode = getEnumMember(fbx.FbxLayerElement, 'eIndexToDirect', cls=fbx.FbxLayerElement.EReferenceMode)

                colorElement = copyTo.CreateElementVertexColor()
                colorElement.SetName(colorSetName)  # The constructor takes no arguments so use this method to set the name!
                colorElement.SetMappingMode(mappingMode)
                colorElement.SetReferenceMode(referenceMode)

                # Assign vertex colours
                #
                colors = copyFrom.getColors(channel=channel)
                numColors = len(colors)

                directArray = colorElement.GetDirectArray()
                directArray.SetCount(numColors)

                for (index, color) in enumerate(colors):

                    directArray.SetAt(index, fbx.FbxColor(color[0], color[1], color[2], color[3]))

                # Assign face-vertex color indices
                #
                faceVertexColorIndices = tuple(map(normalizeIndex, chain(*copyFrom.getFaceVertexColorIndices())))
                numFaceVertexColorIndices = len(faceVertexColorIndices)

                indexArray = colorElement.GetIndexArray()
                indexArray.SetCount(numFaceVertexColorIndices)

                for index, colorIndex in enumerate(faceVertexColorIndices):

                    indexArray.SetAt(index, colorIndex)

        else:

            log.info('Skipping color sets...')

        # Iterate through uv sets
        #
        uvSetNames = copyFrom.getUVSetNames()

        for (channel, uvSetName) in enumerate(uvSetNames):

            # Create new uv element
            #
            log.info(f'Creating "{uvSetName}" UV set...')
            mappingMode = getEnumMember(fbx.FbxLayerElement, 'eByPolygonVertex', cls=fbx.FbxLayerElement.EMappingMode)
            referenceMode = getEnumMember(fbx.FbxLayerElement, 'eIndexToDirect', cls=fbx.FbxLayerElement.EReferenceMode)

            layerElement = copyTo.CreateElementUV(uvSetName)
            layerElement.SetMappingMode(mappingMode)
            layerElement.SetReferenceMode(referenceMode)

            # Assign uv co-ordinates
            #
            uvs = copyFrom.getUVs(channel=channel)
            numUVs = len(uvs)

            directArray = layerElement.GetDirectArray()
            directArray.SetCount(numUVs)

            for (index, controlPoint) in enumerate(uvs):

                directArray.SetAt(index, fbx.FbxVector2(*controlPoint))

            # Assign uv indices
            #
            assignedUVs = tuple(map(normalizeIndices, copyFrom.getAssignedUVs(channel=channel)))
            numAssignedUVs = copyFrom.numFaceVertexIndices()

            indexArray = layerElement.GetIndexArray()
            indexArray.SetCount(numAssignedUVs)

            for (index, uvIndex) in enumerate(chain(*assignedUVs)):

                indexArray.SetAt(index, uvIndex)

        # Check if tangents should be saved
        #
        includeTangentsAndBinormals = kwargs.get('includeTangentsAndBinormals', False)

        if includeNormals and includeTangentsAndBinormals:

            success = copyTo.GenerateTangentsDataForAllUVSets()

            if not success:

                log.warning('Unable to generate tangents and binormals!')

        else:

            log.info('Skipping tangents and binormals...')

        # Reassign original mesh
        #
        copyFrom.setObject(original)

    def copyMaterials(self, copyFrom, copyTo, **kwargs):
        """
        Copies the materials from the supplied scene node to the specified fbx node.

        :type copyFrom: fnmesh.FnMesh
        :type copyTo: fbx.FbxNode
        :rtype: None
        """

        # Iterate through assigned materials
        #
        materials = copyFrom.getAssignedMaterials()
        material = fnnode.FnNode()

        for (obj, texturePath) in materials:

            # Check if material already exists
            #
            success = material.trySetObject(obj)

            if success:

                fbxMaterial = self.createFbxMaterial(material, texturePath=texturePath)
                copyTo.AddMaterial(fbxMaterial)

            else:

                fbxMaterial = fbx.FbxSurfaceLambert.Create(self.fbxManager, '')
                copyTo.AddMaterial(fbxMaterial)

    def copyCustomAttributes(self, copyFrom, copyTo, **kwargs):
        """
        Method used to copy any custom attributes between two nodes.

        :type copyFrom: fnnode.FnNode
        :type copyTo: fbx.FbxNode
        :rtype: None
        """

        # Iterate through attributes
        #
        for attributeName in copyFrom.iterAttr(userDefined=True):

            # Check if attribute type is supported
            #
            value = copyFrom.getAttr(attributeName)
            typeName = type(value).__name__

            if typeName not in self.__data_types__:

                log.debug(f'Cannot find an equivalent FBX type for: {typeName}!')
                continue

            # Create user property
            #
            userDefinedFlag = getEnumMember(fbx.FbxPropertyFlags, 'eUserDefined', cls=fbx.FbxPropertyFlags.EFlags)
            animatableFlag = getEnumMember(fbx.FbxPropertyFlags, 'eAnimatable', cls=fbx.FbxPropertyFlags.EFlags)

            fbxProperty = fbx.FbxProperty.Create(copyTo, self.__data_types__[typeName], attributeName, '')
            fbxProperty.ModifyFlag(userDefinedFlag, True)

            isAnimatable = isinstance(value, (bool, int, float))
            fbxProperty.ModifyFlag(animatableFlag, isAnimatable)

            fbxProperty.Set(value)

    def convertFrameToTime(self, frame, timeMode=None):
        """
        Converts the supplied frame number to an FBX time unit.

        :type frame: Union[int, float]
        :type timeMode: fbx.FbxTime.EMode
        :rtype: fbx.FbxTime
        """

        # Check if time mode was supplied
        #
        if timeMode is None:

            timeMode = self.fbxScene.GetGlobalSettings().GetTimeMode()

        # Create new fbx time
        #
        fbxTime = fbx.FbxTime()

        if isinstance(frame, int):

            fbxTime.SetFrame(frame, timeMode)

        elif isinstance(frame, float):

            fbxTime.SetFramePrecise(frame, timeMode)

        else:

            TypeError(f'convertFrameToTime() expects either an int or float ({type(frame).__name__} given)!')

        return fbxTime

    def bakeFbxNode(self, fbxNode, time=None, animLayer=None, **kwargs):
        """
        Keys the individual translate, rotate and scale components at the specified time.

        :type fbxNode: fbx.FbxNode
        :type time: fbx.FbxTime
        :type animLayer: fbx.FbxAnimLayer
        :rtype: None
        """

        # Get local transform matrix
        #
        joint = fntransform.FnTransform(self.getAssociatedNode(fbxNode))
        globalScale = kwargs.get('globalScale', 1.0)
        matrix = joint.matrix()

        translation = matrix.translation() * globalScale
        rotationOrder = joint.rotationOrder()
        eulerAngles = list(map(math.degrees, matrix.eulerRotation(order=rotationOrder)))
        scale = matrix.scale()

        # Iterate through transform components
        #
        names = ('translate', 'rotate', 'scale')
        values = (translation, eulerAngles, scale)
        interpolationType = getEnumMember(fbx.FbxAnimCurveDef, 'eInterpolationLinear', cls=fbx.FbxAnimCurveDef.EInterpolationType)

        for (i, fbxProperty) in enumerate([fbxNode.LclTranslation, fbxNode.LclRotation, fbxNode.LclScaling]):

            # Iterate through each axis
            #
            for (j, axis) in enumerate(['X', 'Y', 'Z']):

                animCurve = fbxProperty.GetCurve(animLayer, axis, True)
                animCurve.SetName(f'{fbxNode.GetName()}_anim_{names[i]}{axis}')

                animCurve.KeyModifyBegin()
                keyIndex, lastIndex = animCurve.KeyAdd(time)
                animCurve.KeySet(keyIndex, time, values[i][j], interpolationType)
                animCurve.KeyModifyEnd()

        # Iterate through custom attributes
        #
        animatableFlag = getEnumMember(fbx.FbxPropertyFlags, 'eAnimatable', cls=fbx.FbxPropertyFlags.EFlags)

        for attributeName in joint.iterAttr(userDefined=True):

            # Find associated property
            #
            fbxProperty = fbxNode.FindProperty(attributeName)

            if not fbxProperty.IsValid():

                continue

            # Check if property is animatable
            #
            isAnimatable = fbxProperty.GetFlag(animatableFlag)

            if not isAnimatable:

                continue

            # Update anim-curve
            #
            animCurve = fbxProperty.GetCurve(animLayer, True)
            animCurve.SetName(f'{fbxNode.GetName()}_anim_{attributeName}')

            animCurve.KeyModifyBegin()
            keyIndex, lastIndex = animCurve.KeyAdd(time)
            animCurve.KeySet(keyIndex, time, joint.getAttr(attributeName), interpolationType)
            animCurve.KeyModifyEnd()

    def bakeAnimation(self, *fbxNodes, startFrame=0, endFrame=1, step=1, **kwargs):
        """
        Bakes the transform components on the supplied joints over the specified time.

        :type fbxNodes: Union[fbx.FbxNode, List[fbx.FbxNode]]
        :type startFrame: int
        :type endFrame: int
        :type step: Union[int, float]
        :rtype: None
        """

        # Disable redraw
        #
        self.scene.suspendViewport()
        log.info(f'Exporting range: {startFrame} : {endFrame} @ {step} step.')

        # Iterate through time range
        #
        timeMode = self.fbxScene.GetGlobalSettings().GetTimeMode()
        animStack = self.fbxScene.GetCurrentAnimationStack()  # type: fbx.FbxAnimStack
        animLayer = animStack.GetMember(0)

        cls = type(step)
        frameRange = cls(endFrame - startFrame)

        for frame in inclusiveRange(cls(startFrame - frameRange), cls(endFrame), step):

            # Update current time
            #
            self.scene.setTime(frame)

            if startFrame <= frame <= endFrame:

                # Iterate through joints
                #
                time = self.convertFrameToTime(frame, timeMode=timeMode)

                for fbxNode in fbxNodes:

                    self.bakeFbxNode(fbxNode, time=time, animLayer=animLayer, **kwargs)

            else:

                continue  # This is here to support nodes that utilize internal caching!

        # Enable redraw
        #
        self.scene.resumeViewport()

    def createFbxNode(self, node, **kwargs):
        """
        Returns an FBX node from the supplied scene node.

        :type node: fnnode.FnNode
        :rtype: fbx.FbxNode
        """

        # Check if node already exists
        #
        handle = node.handle()

        if self.hasHandle(handle):

            return self.getFbxNodeByHandle(handle)

        # Create fbx node and add to scene
        #
        fbxNode = fbx.FbxNode.Create(self.fbxManager, node.name())
        self.fbxNodes[handle] = fbxNode

        self.fbxScene.AddNode(fbxNode)

        # Create fbx property for reverse lookups
        # This property should not be exported since hash codes are not persistent!
        #
        flag = getEnumMember(fbx.FbxPropertyFlags, 'eNotSavable', cls=fbx.FbxPropertyFlags.EFlags)

        fbxProperty = fbx.FbxProperty.Create(fbxNode, fbx.FbxStringDT, 'handle', '')
        fbxProperty.ModifyFlag(flag, True)

        success = fbxProperty.Set(repr(handle))

        if not success:

            raise RuntimeError(f'Unable to assign {handle} handle to FBX property!')

        return fbxNode

    def createFbxSkeleton(self, joint, **kwargs):
        """
        Returns an FBX skeleton from the supplied scene node.

        :type joint: fntransform.FnTransform
        :rtype: fbx.FbxNode
        """

        # Get associated fbx node
        #
        name = joint.name()
        log.info(f'Creating "{name}" joint.')

        fbxNode = self.createFbxNode(joint)
        self.ensureParent(joint, fbxNode, **kwargs)
        self.copyTransform(joint, fbxNode, **kwargs)

        # Check if custom attributes should be copied
        #
        rootNode = self.fbxScene.GetRootNode()
        isTopLevelNode = fbxNode.GetParent() is rootNode

        if isTopLevelNode:

            self.copyCustomAttributes(joint, fbxNode)

        # Promote to fbx skeleton
        #
        skeletonType = getEnumMember(fbx.FbxSkeleton, 'eLimbNode', cls=fbx.FbxSkeleton.EType)
        fbxSkeleton = fbx.FbxSkeleton.Create(self.fbxManager, name)
        fbxSkeleton.SetSkeletonType(skeletonType)

        fbxNode.SetNodeAttribute(fbxSkeleton)

        return fbxNode

    def createFbxCamera(self, camera, **kwargs):
        """
        Returns an FBX camera from the supplied scene node.

        :type camera: fntransform.FnTransform
        :rtype: fbx.FbxNode
        """

        # Create base fbx node
        #
        name = camera.name()
        log.info(f'Creating "{name}" camera.')

        fbxNode = self.createFbxNode(camera)
        self.copyTransform(camera, fbxNode)

        # Create fbx camera attribute
        #
        fbxCamera = fbx.FbxCamera.Create(self.fbxManager, name)
        fbxNode.SetNodeAttribute(fbxCamera)

        return fbxNode

    def createFbxMesh(self, mesh, **kwargs):
        """
        Returns an FBX mesh from the supplied scene node.

        :type mesh: fnmesh.FnMesh
        :rtype: fbx.FbxNode
        """

        # Create base fbx node
        #
        name = mesh.name()
        log.info(f'Creating "{name}" mesh.')

        fbxNode = self.createFbxNode(mesh, **kwargs)
        self.ensureParent(mesh, fbxNode, **kwargs)
        self.copyMaterials(mesh, fbxNode, **kwargs)

        # Create fbx mesh attribute
        #
        fbxMesh = fbx.FbxMesh.Create(self.fbxManager, name)
        self.copyMesh(mesh, fbxMesh, **kwargs)

        fbxNode.SetNodeAttribute(fbxMesh)

        # Check if skin deformers are enabled
        #
        includeSkins = kwargs.get('includeSkins', False)

        if includeSkins:

            skin = fnskin.FnSkin(mesh.object())

            fbxSkin = self.createFbxSkin(skin)
            fbxMesh.AddDeformer(fbxSkin)

        # Check if blendshapes are enabled
        #
        includeBlendshapes = kwargs.get('includeBlendshapes', False)

        if includeBlendshapes:

            raise NotImplementedError('createFbxMesh() no support for blendshape serialization!')

        return fbxNode

    def createFbxCluster(self, fbxLimb):
        """
        Returns an FBX cluster from the supplied fbx limb.

        :type fbxLimb: fbx.FbxNode
        :rtype: fbx.FbxCluster
        """

        # Create new fbx cluster
        #
        fbxCluster = fbx.FbxCluster.Create(self.fbxManager, fbxLimb.GetName())

        # Link cluster to node
        #
        linkMode = getEnumMember(fbx.FbxCluster, 'eTotalOne', cls=fbx.FbxCluster.ELinkMode)

        fbxCluster.SetLink(fbxLimb)
        fbxCluster.SetLinkMode(linkMode)
        fbxCluster.SetTransformLinkMatrix(fbxLimb.EvaluateGlobalTransform())

        return fbxCluster

    def ensureInfluences(self, influences):
        """
        Ensures FBX nodes exist for the supplied influences.

        :type influences: Dict[int, fntransform.FnTransform]
        :rtype: None
        """

        # Check if any influences are missing
        #
        missing = [influence for (influenceId, influence) in influences.items() if not self.hasHandle(influence.handle())]
        numMissing = len(missing)

        if numMissing == 0:

            return

        # Iterate through missing influences
        #
        ancestor = fntransform.FnTransform()

        for influence in missing:

            # Trace hierarchy for any missing parents
            #
            ancestor.setQueue(influence.trace())

            while not ancestor.isDone():

                # Check if ancestor exists
                #
                handle = ancestor.handle()

                if not self.hasHandle(handle):

                    self.createFbxSkeleton(ancestor)

                # Go to next ancestor
                #
                ancestor.next()

    def createFbxSkin(self, skin, **kwargs):
        """
        Returns an FBX skin from the supplied scene node.

        :type skin: fnskin.FnSkin
        :rtype: fbx.FbxSkin
        """

        # Create skin deformer
        #
        skinningType = getEnumMember(fbx.FbxSkin, 'eLinear', cls=fbx.FbxSkin.EType)

        fbxSkin = fbx.FbxSkin.Create(self.fbxManager, skin.name())
        fbxSkin.SetSkinningType(skinningType)

        # Create skin clusters
        #
        influences = skin.influences()
        self.ensureInfluences(influences)

        fbxClusters = {}

        for (influenceId, influence) in influences.items():

            # Get fbx limb from influence's handle
            #
            handle = influence.handle()
            fbxLimb = self.fbxNodes.get(handle, None)

            if fbxLimb is None:

                continue  # Anything required should be accounted for by now!

            # Create new fbx cluster
            #
            fbxCluster = self.createFbxCluster(fbxLimb)
            fbxSkin.AddCluster(fbxCluster)

            fbxClusters[handle] = fbxCluster

        # Apply vertex weights
        #
        normalizeWeights = lambda pair: (pair[0] - skin.arrayIndexType, pair[1])
        skinWeights = dict(map(normalizeWeights, skin.iterVertexWeights()))

        for (vertexIndex, vertexWeights) in skinWeights.items():

            # Iterate through influence ids
            #
            for (influenceId, weight) in vertexWeights.items():

                influence = influences[influenceId]
                handle = influence.handle()

                fbxClusters[handle].AddControlPointIndex(vertexIndex, weight)

        return fbxSkin

    def createFbxPose(self, *args, **kwargs):
        """
        Returns an FBX bind pose using the supplied transforms.
        Most DCC programs expect the name of the FBX pose to match the deformer it originated from for import purposes.

        :rtype: fbx.FbxPose
        """

        # Iterate through fbx limbs
        #
        fbxPose = fbx.FbxPose.Create(self.fbxManager, kwargs.get('name', ''))
        fbxPose.SetIsBindPose(True)

        for arg in args:

            fbxPose.Add(arg, fbx.FbxMatrix(arg.EvaluateGlobalTransform()))

        return fbxPose

    def createFbxBlendShape(self, blendShape):
        """
        Returns an FBX blendshape from the supplied scene node.

        :type blendShape: fnblendshape.FnBlendshape
        :rtype: fbx.FbxBlendShape
        """

        pass

    def createFbxMaterial(self, material, texturePath=''):
        """
        Returns an FBX material from the supplied scene node.

        :type material: fnnode.FnNode
        :type texturePath: str
        :rtype: fbx.FbxSurfaceLambert
        """

        # Check if material already exists
        #
        handle = material.handle()

        if self.hasHandle(handle):

            return self.getFbxNodeByHandle(handle)

        # Create fbx material
        #
        fbxSurfaceLambert = fbx.FbxSurfaceLambert.Create(self.fbxManager, material.name())
        self.fbxNodes[material.handle()] = fbxSurfaceLambert

        # Check if texture path exists
        #
        if not stringutils.isNullOrEmpty(texturePath):

            fbxFileTexture = self.createFbxFileTexture(texturePath)
            fbxSurfaceLambert.Diffuse.ConnectSrcObject(fbxFileTexture)

        return fbxSurfaceLambert

    def createFbxFileTexture(self, texturePath):
        """
        Returns an FBX file texture using the supplied path.

        :type texturePath: str
        :rtype: fbx.FbxFileTexture
        """

        # Create fbx texture
        #
        filename = os.path.basename(texturePath)
        name, extension = os.path.splitext(filename)

        textureUse = getEnumMember(fbx.FbxFileTexture, 'eStandard', cls=fbx.FbxFileTexture.ETextureUse)
        mappingType = getEnumMember(fbx.FbxFileTexture, 'eUV', cls=fbx.FbxFileTexture.EMappingType)
        materialUse = getEnumMember(fbx.FbxFileTexture, 'eModelMaterial', cls=fbx.FbxFileTexture.EMaterialUse)

        fbxFileTexture = fbx.FbxFileTexture.Create(self.fbxManager, name)
        fbxFileTexture.SetFileName(self.scene.makePathAbsolute(texturePath))
        fbxFileTexture.SetTextureUse(textureUse)
        fbxFileTexture.SetMappingType(mappingType)
        fbxFileTexture.SetMaterialUse(materialUse)
        fbxFileTexture.SetSwapUV(False)
        fbxFileTexture.SetTranslation(0.0, 0.0)
        fbxFileTexture.SetRotation(0.0, 0.0)
        fbxFileTexture.SetScale(1.0, 1.0)

        return fbxFileTexture

    def serializeSkeleton(self, settings, globalScale=1.0):
        """
        Serializes the joints from the supplied skeleton settings.

        :type settings: dcc.fbx.libs.fbxskeleton.FbxSkeleton
        :type globalScale: float
        :rtype: List[fbx.FbxNode]
        """

        # Create fbx placeholders for joints
        # This ensures parenting can be performed!
        #
        joints = settings.getHierarchy(namespace=self.namespace)
        self.allocateFbxNodes(*joints)

        # Create fbx skeletons
        #
        joint = fntransform.FnTransform(iter(joints))
        fbxNodes = []

        while not joint.isDone():

            fbxNode = self.createFbxSkeleton(joint, globalScale=globalScale, **settings)
            fbxNodes.append(fbxNode)

            joint.next()

        return fbxNodes

    def serializeMesh(self, settings, globalScale=1.0):
        """
        Serializes the geometry from the supplied mesh settings.

        :type settings: dcc.fbx.libs.fbxmesh.FbxMesh
        :type globalScale: float
        :rtype: List[fbx.FbxNode]
        """

        # Serialize meshes
        #
        meshes = settings.getObjects(namespace=self.namespace)
        mesh = fnmesh.FnMesh(iter(meshes))

        fbxNodes = []

        while not mesh.isDone():

            fbxNode = self.createFbxMesh(mesh, globalScale=globalScale, **settings)
            fbxNodes.append(fbxNode)

            mesh.next()

        return fbxNodes

    def serializeCameras(self, settings, globalScale=1.0):
        """
        Serializes the cameras from the supplied camera settings.

        :type settings: dcc.fbx.libs.fbxcamera.FbxCamera
        :type globalScale: float
        :rtype: List[fbx.FbxNode]
        """

        return []  # TODO: Implement camera serialization!

    def serializeExportSet(self, exportSet, asAscii=False):
        """
        Serializes the nodes from the supplied export set.

        :type exportSet: dcc.fbx.libs.fbxexportset.FbxExportSet
        :type asAscii: bool
        :rtype: str
        """

        # Serialize export set components
        #
        globalScale = float(exportSet.scale)

        self.serializeSkeleton(exportSet.skeleton, globalScale=globalScale)
        self.serializeCameras(exportSet.camera, globalScale=globalScale)
        self.serializeMesh(exportSet.mesh, globalScale=globalScale)

        # Save changes
        #
        exportPath = exportSet.exportPath()
        self.scene.ensureDirectory(exportPath)
        self.scene.ensureWritable(exportPath)

        return self.saveAs(exportPath, asAscii=asAscii)

    def serializeExportRange(self, exportRange, asAscii=False):
        """
        Serializes the nodes from the supplied export range.

        :type exportRange: dcc.fbx.libs.fbxexportrange.FbxExportRange
        :type asAscii: bool
        :rtype: str
        """

        # Serialize skeleton from associated export set
        #
        exportSet = exportRange.exportSet()
        globalScale = float(exportSet.scale)

        fbxNodes = self.serializeSkeleton(exportSet.skeleton, globalScale=globalScale)

        # Bake transform values
        #
        startFrame, endFrame = exportRange.timeRange()
        step = float(exportRange.step)

        self.updateTimeRange(startFrame, endFrame)
        self.bakeAnimation(
            *fbxNodes,
            startFrame=startFrame,
            endFrame=endFrame,
            step=step,
            globalScale=globalScale
        )

        # Check if skeleton should be moved to origin
        #
        if exportRange.moveToOrigin:

            self.moveToOrigin()

        # Save changes
        #
        exportPath = exportRange.exportPath()
        self.scene.ensureDirectory(exportPath)
        self.scene.ensureWritable(exportPath)

        return self.saveAs(exportPath, asAscii=asAscii)

    def saveAs(self, filePath, asAscii=False):
        """
        Commits the fbx scene to the specified file path.

        :type filePath: str
        :type asAscii: bool
        :rtype: str
        """

        log.info(f'Saving FBX file to: {filePath}')
        success = FbxCommon.SaveScene(self.fbxManager, self.fbxScene, filePath, pFileFormat=int(asAscii))

        if success:

            return filePath

        else:

            return ''
    # endregion
