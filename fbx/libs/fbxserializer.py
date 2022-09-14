import fbx
import FbxCommon

from itertools import chain
from ... import __application__, fnscene, fnnode, fntransform, fnmesh, fnskin
from ...math import matrixmath

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def fbxNodeLookup(func):
    """
    Returns a function wrapper that can be used to check for serialization redundancy.
    Anytime a new fbx node is requested this function will check to see if it already exists.

    :rtype: instancemethod
    """

    # Define wrapper function
    #
    def wrapper(*args, **kwargs):

        # Get node handle
        #
        factory = args[0]

        node = args[1]
        handle = node.handle()

        # Check if node already exists
        #
        fbxNode = factory.fbxNodes.get(handle, None)

        if fbxNode is not None:

            return fbxNode

        else:

            return func(*args, **kwargs)

    return wrapper


class FbxSerializer(object):
    """
    Base class used for composing fbx files from DCC scene nodes.
    This exporter was created to ensure that the DCC scene data was as clean as possible for game engines.
    This exporter supports animation baking at a decimal framerate to help reduce euler filter abnormalities.
    TODO: Implement support for custom attributes and blendshapes.
    """

    # region Dunderscores
    __slots__ = (
        '_scene',
        '_exportSet',
        '_fbxScene',
        '_fbxManager',
        '_fbxAnimStack',
        '_fbxAnimLayer',
        '_fbxNodes'
    )

    __types__ = {
        'float': fbx.FbxFloatDT,
        'double': fbx.FbxDoubleDT,
        'int': fbx.FbxIntDT,
        'short': fbx.FbxShortDT,
        'long': fbx.FbxLongLongDT,
        'bool': fbx.FbxBoolDT,
        'string': fbx.FbxStringDT
    }

    __axes__ = {
        'x': fbx.FbxAxisSystem.eXAxis,
        'y': fbx.FbxAxisSystem.eYAxis,
        'z': fbx.FbxAxisSystem.eZAxis
    }

    __units__ = {
        'millimeter': fbx.FbxSystemUnit.mm,
        'centimeter': fbx.FbxSystemUnit.cm,
        'meter': fbx.FbxSystemUnit.m,
        'kilometer': fbx.FbxSystemUnit.km,
        'inch': fbx.FbxSystemUnit.Inch,
        'foot': fbx.FbxSystemUnit.Foot,
        'yard': fbx.FbxSystemUnit.Yard,
        'mile': fbx.FbxSystemUnit.Mile,
    }

    __rotate_orders__ = {
        'xyz': fbx.eEulerXYZ,
        'xzy': fbx.eEulerXZY,
        'yzx': fbx.eEulerYZX,
        'yxz': fbx.eEulerYXZ,
        'zxy': fbx.eEulerZXY,
        'zyx': fbx.eEulerZYX
    }

    def __init__(self, exportSet):
        """
        Private method called after a new instance has been created.

        :type exportSet: fbxexportset.FbxExportSet
        :rtype: None
        """

        # Call parent method
        #
        super(FbxSerializer, self).__init__()

        # Declare class variables
        #
        self._scene = fnscene.FnScene()
        self._exportSet = exportSet
        self._fbxManager, self._fbxScene = FbxCommon.InitializeSdkObjects()
        self._fbxAnimStack = fbx.FbxAnimStack.Create(self.fbxManager, 'Take 001')
        self._fbxAnimLayer = fbx.FbxAnimLayer.Create(self.fbxManager, 'BaseLayer')
        self._fbxNodes = {}

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
    def exportSet(self):
        """
        Getter method that returns the export set.

        :rtype: fbxexportset.FbxExportSet
        """

        return self._exportSet

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
        Copies the DCC application's axis setting to the fbx global settings.

        :rtype: None
        """

        # Change axis system
        #
        globalSettings = self.fbxScene.GetGlobalSettings()
        upAxis = self.scene.getUpAxis()

        if __application__ == 'maya':

            axisSystem = fbx.FbxAxisSystem.MayaYUp if upAxis == 'y' else fbx.FbxAxisSystem.MayaZUp
            globalSettings.SetAxisSystem(axisSystem)

        elif __application__ == '3dsmax':

            globalSettings.SetAxisSystem(fbx.FbxAxisSystem.Max)

        else:

            globalSettings.SetAxisSystem(self.__class__.__axes__[upAxis])

    def copySystemUnits(self):
        """
        Copies the DCC application's unit settings to the fbx global settings.

        :rtype: None
        """

        # Change system units
        #
        globalSettings = self.fbxScene.GetGlobalSettings()

        linearUnit = self.scene.getLinearUnit()  # TODO: Implement this method!
        globalSettings.SetSystemUnit(self.__class__.__units__[linearUnit.name.lower()])

    def getFbxNodeByHandle(self, handle):
        """
        Returns the Fbx node associated with the supplied DCC node's handle.

        :type handle: int
        :rtype: fbx.FbxNode
        """

        return self._fbxNodes.get(handle, None)

    def getFbxNodeByName(self, name):
        """
        Returns the Fbx node with the supplied name.

        :type name: str
        :rtype: fbx.FbxNode
        """

        pass

    def copyTransform(self, copyFrom, copyTo):
        """
        Method used to copy the transform values between two nodes.

        :type copyFrom: fntransform.FnTransform
        :type copyTo: fbx.FbxNode
        :rtype: bool
        """

        # Set local translation
        #
        matrix = copyFrom.matrix()
        translation = None

        if self.exportSet.scale != 1.0:

            # Get matrices
            #
            scaleMatrix = matrixmath.createScaleMatrix(self.exportSet.scale)
            parentMatrix = copyFrom.parentMatrix()
            worldMatrix = copyFrom.worldMatrix()

            # Calculate scaled translation
            #
            matrix = (scaleMatrix.I * (worldMatrix * scaleMatrix)) * (scaleMatrix.I * (parentMatrix * scaleMatrix)).I
            translation = matrixmath.decomposeTranslateMatrix(matrix)

        else:

            translation = matrixmath.decomposeTranslateMatrix(matrix)

        copyTo.LclTranslation.Set(fbx.FbxDouble3(*translation))

        # Set local rotation
        #
        rotationOrder = copyFrom.rotationOrder()
        rotation = matrixmath.decomposeRotateMatrix(matrix, rotateOrder=rotationOrder)

        copyTo.SetRotationActive(True)
        copyTo.SetRotationOrder(fbx.FbxNode.eSourcePivot, self.__class__.__rotate_orders__[rotationOrder])
        copyTo.LclRotation.Set(fbx.FbxDouble3(*rotation))

        # Set local scale
        #
        scale = matrixmath.decomposeScaleMatrix(matrix)
        copyTo.LclScaling.Set(fbx.FbxDouble3(*scale))
        copyTo.SetTransformationInheritType(fbx.FbxTransform.eInheritRrs)  # Add support for inverse scale!

        return True

    def copyCustomAttributes(self, copyFrom, copyTo):
        """
        Method used to copy any custom attributes between two nodes.

        :type copyFrom: Union[maya.api.OpenMaya.MObject, pymxs.MXSWrapperBase]
        :type copyTo: fbx.FbxNode
        :rtype: bool
        """

        pass

    @fbxNodeLookup
    def createFbxNode(self, node, **kwargs):
        """
        Returns an FbxNode from the supplied DCC scene node.
        This method will also copy all the required transform data.
        When it comes to transformation inheritance please see the following:
            [0] eInheritRrSs: Scaling of parent is applied in the child world after the local child rotation.
            [1] eInheritRSrs: Scaling of parent is applied in the parent world.
            [2] eInheritRrs: Scaling of parent does not affect the scaling of children.
        The latter is the equivalent of enabling inverse scaling inside Maya.

        :type node: fnnode.FnNode
        :key fbxParent: fbx.FbxNode
        :rtype: fbx.FbxNode
        """

        # Create fbx node
        #
        name = node.name()
        fbxNode = fbx.FbxNode.Create(self.fbxManager, name)

        self.fbxScene.AddNode(fbxNode)

        # Store reference to fbx node
        #
        handle = node.handle()
        self._fbxNodes[handle] = fbxNode

        # Check if a parent node was supplied
        #
        parent = kwargs.get('parent', self.fbxScene.GetRootNode())
        parent.AddChild(fbxNode)

        # Create fbx property for reverse lookups
        # This property should not be exported since hash codes are not persistent between sessions
        #
        fbxProperty = fbx.FbxProperty.Create(fbxNode, fbx.FbxStringDT, 'handle', '')
        fbxProperty.ModifyFlag(fbx.FbxPropertyFlags.eNotSavable, True)

        success = fbxProperty.Set(repr(handle))

        if not success:

            raise RuntimeError(f'Unable to assign {handle} handle to fbx property!')

        return fbxNode

    @fbxNodeLookup
    def createFbxSkeleton(self, node, **kwargs):
        """
        Returns an FbxSkeleton attribute from the supplied node.

        :type node: fntransform.FnTransform
        :rtype: fbx.FbxNode
        """

        # Create base fbx node
        #
        fbxNode = self.createFbxNode(node, **kwargs)
        self.copyTransform(node, fbxNode)

        # Create fbx skeleton attribute
        #
        fbxSkeleton = fbx.FbxSkeleton.Create(self.fbxManager, node.name())
        fbxSkeleton.SetSkeletonType(fbx.FbxSkeleton.eLimbNode)

        fbxNode.SetNodeAttribute(fbxSkeleton)

        return fbxNode

    @fbxNodeLookup
    def createFbxCamera(self, node, **kwargs):
        """
        Returns an FbxCamera attribute node.

        :type node: fncamera.FnCamera
        :rtype: fbx.FbxNode
        """

        # Create base fbx node
        #
        fbxNode = self.createFbxNode(node, **kwargs)
        self.copyTransform(node, fbxNode)

        # Create fbx camera attribute
        #
        fbxCamera = fbx.FbxCamera.Create(self.fbxManager, '')
        fbxNode.SetNodeAttribute(fbxCamera)

        return fbxNode

    def copyMesh(self, copyFrom, copyTo):
        """
        Method used to copy the transform values between two nodes.

        :type copyFrom: fnmesh.FnMesh
        :type copyTo: fbx.FbxMesh
        :rtype: bool
        """

        # Initialize control points for mesh
        #
        copyTo.InitControlPoints(copyFrom.numVertices())

        for (index, controlPoint) in enumerate(copyFrom.iterVertices()):

            copyTo.SetControlPointAt(fbx.FbxVector4(*controlPoint), index)

        # Assign vertices to polygons
        #
        for (polygonIndex, faceVertexIndices) in enumerate(copyFrom.iterFaceVertexIndices()):

            # Begin defining polygon
            #
            copyTo.BeginPolygon(polygonIndex)

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
        materialElement = copyTo.GetElementMaterial()
        materialElement.SetMappingMode(fbx.FbxLayerElement.eByPolygon)
        materialElement.SetReferenceMode(fbx.FbxLayerElement.eIndexToDirect)

        indexArray = materialElement.GetIndexArray()
        indexArray.SetCount(copyFrom.numFaces())

        for (index, materialIndex) in enumerate(copyFrom.iterFaceMaterialIndices()):  # FIXME

            indexArray.SetAt(index, materialIndex)

        # Check if normals should be included
        #
        if self.exportSet.includeNormals:

            # Initialize new normal element
            #
            normalElement = copyTo.CreateElementNormal()
            normalElement.SetMappingMode(fbx.FbxLayerElement.eByPolygonVertex)
            normalElement.SetReferenceMode(fbx.FbxLayerElement.eIndexToDirect)

            # Assign normals
            #
            numFaceVertices = copyFrom.numFaceVertices()

            directArray = normalElement.GetDirectArray()
            directArray.SetCount(numFaceVertices)

            indexArray = normalElement.GetIndexArray()
            indexArray.SetCount(numFaceVertices)

            for (index, normal) in enumerate(chain(*copyFrom.faceVertexNormals)):  # FIXME

                directArray.SetAt(index, fbx.FbxVector4(normal[0], normal[1], normal[2], 1.0))
                indexArray.SetAt(index, index)

        else:

            log.info('Skipping face-vertex normals...')

        # Check if smoothings should be included
        #
        if self.exportSet.includeSmoothings:

            # Check if mesh uses edge smoothings
            #
            if copyFrom.hasEdgeSmoothings():

                # Initialize new edge smoothing element
                #
                smoothingElement = copyTo.CreateElementSmoothing()
                smoothingElement.SetMappingMode(fbx.FbxLayerElement.eByEdge)
                smoothingElement.SetReferenceMode(fbx.FbxLayerElement.eDirect)

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
                smoothingElement = copyTo.CreateElementSmoothing()
                smoothingElement.SetMappingMode(fbx.FbxLayerElement.eByPolygon)
                smoothingElement.SetReferenceMode(fbx.FbxLayerElement.eDirect)

                # Assign smoothing groups
                #
                smoothingGroups = copyFrom.getSmoothingGroups()
                numSmoothingGroups = len(smoothingGroups)

                directArray = smoothingElement.GetDirectArray()
                directArray.SetCount(numSmoothingGroups)

                for index, group in enumerate(smoothingGroups):

                    directArray.SetAt(index, group)

        else:

            log.info('Skipping component smoothings...')

        # Check if vertex colors should be included
        #
        if self.exportSet.includeColorSets:

            # Iterate through all color sets
            #
            colorSetNames = copyFrom.getColorSetNames()

            for (channel, colorSetName) in enumerate(colorSetNames):

                # Create new color set element
                #
                colorElement = copyTo.CreateElementVertexColor()

                colorElement.SetName(colorSetName)  # The constructor takes no arguments so use this method to set the name
                colorElement.SetMappingMode(fbx.FbxLayerElement.eByPolygonVertex)
                colorElement.SetReferenceMode(fbx.FbxLayerElement.eIndexToDirect)

                # Assign vertex colours
                #
                colors = copyFrom.getColors(channel=channel)
                numColors = len(colors)

                directArray = colorElement.GetDirectArray()
                directArray.SetCount(numColors)

                for (index, color) in enumerate(colors):

                    directArray.SetAt(index, fbx.FbxColor(*color))

                # Assign face-vertex color indices
                #
                faceVertexColorIndices = copyFrom.getFaceVertexColorIndices()
                numFaceVertexColorIndices = len(faceVertexColorIndices)

                indexArray = colorElement.GetIndexArray()
                indexArray.SetCount(numFaceVertexColorIndices)

                for index, colorIndex in enumerate(chain(*faceVertexColorIndices)):

                    indexArray.SetAt(index, colorIndex)

        else:

            log.info('Skipping color sets...')

        # Iterate through uv sets
        #
        uvSetNames = copyFrom.getUVSetNames()

        for (channel, uvSetName) in enumerate(uvSetNames):

            # Create new uv element
            #
            log.info('Creating "%s" UV set...' % uvSetName)

            layerElement = copyTo.CreateElementUV(uvSetName)
            layerElement.SetMappingMode(fbx.FbxLayerElement.eByPolygonVertex)
            layerElement.SetReferenceMode(fbx.FbxLayerElement.eIndexToDirect)

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
            assignedUVs = copyFrom.getAsignedUVs(channel=channel)
            numAssignedUVs = copyFrom.numFaceVertexIndices()

            indexArray = layerElement.GetIndexArray()
            indexArray.SetCount(numAssignedUVs)

            for (index, uvIndex) in enumerate(chain(*assignedUVs)):

                indexArray.SetAt(index, uvIndex)

        # Check if tangents should be saved
        #
        if self.exportSet.includeTangentsAndBinormals:

            # Create new tangent elements
            # This will create a layer for each UV set!
            #
            copyTo.CreateElementTangent()
            copyTo.CreateElementBinormal()

            for (index, uvSet) in enumerate(meshData.uvSets):

                # Get indexed elements
                #
                tangentElement = copyTo.GetElementTangent(index)
                tangentElement.SetName(uvSet.name)
                tangentElement.SetMappingMode(fbx.FbxLayerElement.eByPolygonVertex)
                tangentElement.SetReferenceMode(fbx.FbxLayerElement.eDirect)

                binormalElement = copyTo.GetElementBinormal(index)
                binormalElement.SetName(uvSet.name)
                binormalElement.SetMappingMode(fbx.FbxLayerElement.eByPolygonVertex)
                binormalElement.SetReferenceMode(fbx.FbxLayerElement.eDirect)

                # Assign tangents and binormals
                #
                tangentArray = tangentElement.GetDirectArray()
                tangentArray.SetCount(len(uvSet.tangents))

                binormalArray = binormalElement.GetDirectArray()
                binormalArray.SetCount(len(uvSet.binormals))

                for j, (tangent, binormal) in enumerate(zip(uvSet.tangents, uvSet.binormals)):

                    tangentArray.SetAt(j, fbx.FbxVector4(tangent[0], tangent[1], tangent[2], 1.0))
                    binormalArray.SetAt(j, fbx.FbxVector4(binormal[0], binormal[1], binormal[2], 1.0))

        else:

            log.info('Skipping tangents and binormals...')

    @fbxNodeLookup
    def createFbxMesh(self, node, **kwargs):
        """
        Returns an FbxMesh from the supplied node.

        :type node: fnnode.FnNode
        :rtype: fbx.FbxNode
        """

        # Create base fbx node
        #
        fbxNode = self.createFbxNode(node, **kwargs)
        self.copyTransform(node, fbxNode)

        # Create fbx mesh attribute
        #
        fbxMesh = fbx.FbxMesh.Create(self.fbxManager, node.name())
        self.copyMesh(node, fbxMesh)

        fbxNode.SetNodeAttribute(fbxMesh)

        # Assign materials
        #
        materials = nodehelpers.getAssignedMaterials(node)

        for material in materials:

            fbxMaterial = self.createFbxMaterial(material)
            fbxNode.AddMaterial(fbxMaterial)

        # Check if skin deformers are enabled
        #
        if self.exportSet.includeSkins:

            fbxSkin = self.createFbxSkin(node)
            fbxMesh.AddDeformer(fbxSkin)

        # Check if blendshapes are enabled
        #
        if self.exportSet.includeBlendshapes:

            fbxBlendShape = self.createFbxBlendShape(node)
            fbxMesh.AddDeformer(fbxBlendShape)

        return fbxNode

    @fbxNodeLookup
    def createFbxMaterial(self, node):
        """
        Returns an fbx surface material using the supplied node as a source.

        :type node:
        :rtype: fbx.FbxNode
        """

        # Create fbx material attribute
        #
        fbxSurfaceMaterial = fbx.FbxSurfaceMaterial.Create(self.fbxManager, nodehelpers.getNodeName(node))

        handle = nodehelpers.getNodeHandle(node)
        self.history[handle] = fbxSurfaceMaterial

        return fbxSurfaceMaterial

    def createFbxCluster(self, fbxLimb):
        """
        Method used to create an fbx cluster from an fbx node.

        :type fbxLimb: fbx.FbxNode
        :rtype: fbx.FbxCluster
        """

        # Create new fbx cluster
        #
        fbxCluster = fbx.FbxCluster.Create(self.fbxManager, fbxLimb.GetName())

        # Link cluster to node
        #
        fbxCluster.SetLink(fbxLimb)
        fbxCluster.SetLinkMode(fbx.FbxCluster.eTotalOne)
        fbxCluster.SetTransformLinkMatrix(fbxLimb.EvaluateGlobalTransform())

        return fbxCluster

    def createFbxSkin(self, node, **kwargs):
        """
        Method used to create a skin deformer that can be assigned to an fbx mesh attribute.

        :type node: fnskin.FnSkin
        :rtype: fbx.FbxSkin
        """

        # Create skin deformer
        #
        fbxSkin = fbx.FbxSkin.Create(self.fbxManager, node.name())
        fbxSkin.SetSkinningType(fbx.FbxSkin.eLinear)

        # Create skin clusters
        #
        skinWeights = node.vertexWeights()
        influences = node.influences()

        influence = fnnode.FnNode()
        fbxClusters = {}

        for (influenceId, influenceObj) in enumerate(influences):

            # Check for none type
            #
            success = influence.trySetObject(influenceObj)

            if not success:

                continue

            # Get fbx limb from influence's hash code
            #
            hashCode = influence.handle()
            fbxLimb = self._fbxNodes[hashCode]

            # Create new fbx cluster
            #
            fbxCluster = self.createFbxCluster(fbxLimb)
            fbxSkin.AddCluster(fbxCluster)

            fbxClusters[hashCode] = fbxCluster

        # Apply vertex weights
        #
        for (vertexIndex, vertexWeights) in enumerate(skinWeights):

            # Iterate through influence ids
            #
            for (influenceId, weight) in vertexWeights.items():

                influence.setObject(influences[influenceId])
                hashCode = influence.handle()

                fbxClusters[hashCode].AddControlPointIndex(vertexIndex, weight)

        return fbxSkin

    def createFbxPose(self, *args, **kwargs):
        """
        Returns an fbx bind pose using the supplied transforms.
        Maya expects the name of the fbx pose to match the deformer it is associated with for import purposes.

        :rtype: fbx.FbxPose
        """

        # Iterate through fbx limbs
        #
        fbxPose = fbx.FbxPose.Create(self.fbxManager, kwargs.get('name', ''))
        fbxPose.SetIsBindPose(True)

        for arg in args:

            fbxPose.Add(arg, fbx.FbxMatrix(arg.EvaluateGlobalTransform()))

        return fbxPose

    def createFbxBlendShape(self, node):
        """
        Returns an fbx blendshape from the supplied mesh node.

        :type node: fnblendshape.FnBlendshape
        :rtype: fbx.FbxBlendShape
        """

        pass

    def bakeTransforms(self, fbxNode, startFrame=0, endFrame=1, step=1):
        """
        Bakes the supplied fbx transform over the specified amount of time.

        :type fbxNode: fbx.FbxNode
        :type startFrame: int
        :type endFrame: int
        :type step: Union[int, float]
        :rtype: None
        """

        pass

    def serialize(self, animationOnly=False):
        """
        Serializes all nodes from the internal export set.

        :type animationOnly: bool
        :rtype: None
        """

        pass

    def saveAs(self, filePath):
        """
        Commits the fbx scene to the specified file path.

        :type filePath: str
        :rtype: bool
        """

        log.info(f'Saving FBX file to: {filePath}')
        return FbxCommon.SaveScene(self.fbxManager, self.fbxScene, filePath)
    # endregion
