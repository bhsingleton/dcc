import maya.cmds as mc
import maya.api.OpenMaya as om

from dcc import fnnode
from dcc.abstract import afnmesh
from dcc.maya.libs import dagutils, transformutils, meshutils
from dcc.dataclasses.vector import Vector
from dcc.dataclasses.colour import Colour
from dcc.generators.package import package
from dcc.generators.chunks import chunks

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnMesh(fnnode.FnNode, afnmesh.AFnMesh):
    """
    Overload of AFnMesh used to interface with meshes in Maya.
    """

    __slots__ = ()

    def setObject(self, obj):
        """
        Assigns an object to this function set for manipulation.

        :type obj: Union[str, om.MObject, om.MDagPath]
        :rtype: None
        """

        # Check if this is a transform
        #
        obj = dagutils.getMObject(obj)

        if obj.hasFn(om.MFn.kTransform):

            obj = om.MDagPath.getAPathTo(obj).extendToShape().node()

        # Call parent method
        #
        super(FnMesh, self).setObject(obj)

    def objectMatrix(self):
        """
        Returns the object matrix for this mesh.

        :rtype: om.MMatrix
        """

        obj = self.object()

        if obj.hasFn(om.MFn.kDagNode):

            return transformutils.getWorldMatrix(obj)

        else:

            return om.MMatrix()

    def triangulatedObject(self):
        """
        Returns the triangulated mesh data object for this mesh.

        :rtype: om.MObject
        """

        return meshutils.triangulate(self.object())

    def name(self):
        """
        Returns the name of this node.

        :rtype: str
        """

        parent = dagutils.getParent(self.object())
        absoluteName = om.MFnDependencyNode(parent).name()

        return dagutils.stripNamespace(absoluteName)

    def numVertices(self):
        """
        Returns the number of vertices in this mesh.

        :rtype: int
        """

        return om.MFnMesh(self.object()).numVertices

    def numEdges(self):
        """
        Returns the number of edges in this mesh.

        :rtype: int
        """

        return om.MFnMesh(self.object()).numEdges

    def numFaces(self):
        """
        Returns the number of faces in this mesh.

        :rtype: int
        """

        return om.MFnMesh(self.object()).numPolygons

    def component(self):
        """
        Returns the selected component from this mesh.

        :rtype: om.MObject
        """

        obj = self.object()

        components = [component for (dagPath, component) in dagutils.iterActiveComponentSelection() if dagPath.node() == obj]
        numComponents = len(components)

        if numComponents:

            return components[0]

        else:

            return om.MObject.kNullObj

    def selectedVertices(self):
        """
        Returns a list of selected vertex indices.

        :rtype: List[int]
        """

        component = self.component()
        elements = om.MFnSingleIndexedComponent(component).getElements()

        if component.hasFn(om.MFn.kMeshVertComponent):

            return list(elements)

        elif component.hasFn(om.MFn.kMeshEdgeComponent):

            return self.getConnectedVertices(*elements, componentType=self.ComponentType.Edge)

        elif component.hasFn(om.MFn.kMeshPolygonComponent):

            return self.getConnectedVertices(*elements, componentType=self.ComponentType.Face)

        else:

            return []

    def selectedEdges(self):
        """
        Returns a list of selected edge indices.

        :rtype: List[int]
        """

        component = self.component()
        elements = om.MFnSingleIndexedComponent(component).getElements()

        if component.hasFn(om.MFn.kMeshEdgeComponent):

            return list(elements)

        elif component.hasFn(om.MFn.kMeshVertComponent):

            return self.getConnectedEdges(*elements, componentType=self.ComponentType.Vertex)

        elif component.hasFn(om.MFn.kMeshPolygonComponent):

            return self.getConnectedEdges(*elements, componentType=self.ComponentType.Face)

        else:

            return []

    def selectedFaces(self):
        """
        Returns a list of selected face indices.

        :rtype: List[int]
        """

        component = self.component()
        elements = om.MFnSingleIndexedComponent(component).getElements()

        if component.hasFn(om.MFn.kMeshPolygonComponent):

            return list(elements)

        elif component.hasFn(om.MFn.kMeshVertComponent):

            return self.getConnectedFaces(*elements, componentType=self.ComponentType.Vertex)

        elif component.hasFn(om.MFn.kMeshEdgeComponent):

            return self.getConnectedFaces(*elements, componentType=self.ComponentType.Edge)

        else:

            return []
    
    def iterVertices(self, *indices, cls=Vector, worldSpace=False):
        """
        Returns a generator that yield vertex points.
        If no arguments are supplied then all vertices will be yielded.
        
        :type cls: Callable
        :type worldSpace: bool
        :rtype: Iterator[Vector]
        """

        # Evaluate arguments
        #
        numIndices = len(indices)

        if numIndices == 0:

            indices = range(self.numVertices())

        # Iterate through vertices
        #
        iterVertices = om.MItMeshVertex(self.object())
        objectMatrix = self.objectMatrix()

        for index in indices:

            iterVertices.setIndex(index)
            point = iterVertices.position()

            if worldSpace:

                point = point * objectMatrix

            yield cls(point.x, point.y, point.z)

    def iterVertexNormals(self, *indices, cls=Vector):
        """
        Returns a generator that yields vertex normals.
        If no arguments are supplied then all vertex normals will be yielded.
        
        :type cls: Callable
        :rtype: Iterator[Vector]
        """

        # Evaluate arguments
        #
        numIndices = len(indices)

        if numIndices == 0:

            indices = range(self.numVertices())

        # Iterate through vertices
        #
        iterVertices = om.MItMeshVertex(self.object())

        for index in indices:

            iterVertices.setIndex(index)
            normal = iterVertices.getNormal()

            yield cls(normal.x, normal.y, normal.z)

    def hasEdgeSmoothings(self):
        """
        Evaluates if this mesh uses edge smoothings.

        :rtype: bool
        """

        return True

    def iterEdgeSmoothings(self, *indices):
        """
        Returns a generator that yields edge smoothings.

        :rtype: Iterator[bool]
        """

        # Evaluate arguments
        #
        numIndices = len(indices)

        if numIndices == 0:

            indices = range(self.numEdges())

        # Iterate through vertices
        #
        iterEdges = om.MItMeshEdge(self.object())

        for index in indices:

            iterEdges.setIndex(index)
            yield iterEdges.isSmooth

    def hasSmoothingGroups(self):
        """
        Evaluates if this mesh uses smoothing groups.

        :rtype: bool
        """

        return False

    def numSmoothingGroups(self):
        """
        Returns the number of smoothing groups currently in use.

        :rtype: int
        """

        return 0

    def iterSmoothingGroups(self, *indices):
        """
        Returns a generator that yields face smoothing groups.

        :rtype: Iterator[int]
        """

        return iter([])

    def iterFaceVertexIndices(self, *indices):
        """
        Returns a generator that yields face vertex indices.
        If no arguments are supplied then all face vertex indices will be yielded.

        :rtype: Iterator[List[int]]
        """

        # Evaluate arguments
        #
        numIndices = len(indices)

        if numIndices == 0:

            indices = range(self.numFaces())

        # Iterate through vertices
        #
        iterPolygons = om.MItMeshPolygon(self.object())

        for index in indices:

            iterPolygons.setIndex(index)
            vertexIndices = iterPolygons.getVertices()

            yield tuple(vertexIndices)

    def iterFaceVertexNormals(self, *indices, cls=Vector):
        """
        Returns a generator that yields face-vertex indices for the specified faces.
        
        :type cls: Callable
        :rtype: Iterator[List[Vector]]
        """

        # Evaluate arguments
        #
        numIndices = len(indices)

        if numIndices == 0:

            indices = range(self.numFaces())

        # Iterate through indices
        #
        fnMesh = om.MFnMesh(self.object())

        for index in indices:

            normals = fnMesh.getFaceVertexNormals(index)
            yield [cls(normal.x, normal.y, normal.z) for normal in normals]

    def iterFaceCenters(self, *indices, cls=Vector):
        """
        Returns a generator that yields face centers.
        If no arguments are supplied then all face centers will be yielded.
        
        :type cls: Callable
        :rtype: Iterator[Vector]
        """

        # Evaluate arguments
        #
        numIndices = len(indices)

        if numIndices == 0:

            indices = range(self.numFaces())

        # Iterate through vertices
        #
        iterPolygons = om.MItMeshPolygon(self.object())

        for index in indices:

            iterPolygons.setIndex(index)
            center = iterPolygons.center()

            yield cls(center.x, center.y, center.z)

    def iterFaceNormals(self, *indices, cls=Vector):
        """
        Returns a generator that yields face normals.
        If no arguments are supplied then all face normals will be yielded.
        
        :type cls: Callable
        :rtype: Iterator[Vector]
        """

        # Evaluate arguments
        #
        numIndices = len(indices)

        if numIndices == 0:

            indices = range(self.numFaces())

        # Iterate through vertices
        #
        iterPolygons = om.MItMeshPolygon(self.object())

        for index in indices:

            iterPolygons.setIndex(index)
            normals = iterPolygons.getNormals()

            normal = sum(normals, start=om.MVector()) / len(normals)

            yield cls(normal.x, normal.y, normal.z)

    def getFaceTriangleVertexIndices(self):
        """
        Returns a dictionary of faces and their corresponding triangle-vertex indices.

        :rtype: Dict[int, List[Tuple[int, int, int]]]
        """

        triangleCounts, triangleVertexIndices = om.MFnMesh(self.object()).getTriangles()
        vertexCounts = [3 * count for count in triangleCounts]

        faceTriangleVertexIndices = {}

        for (i, vertexIndices) in enumerate(package(vertexCounts, triangleVertexIndices)):

            faceTriangleVertexIndices[i] = list(chunks(list(vertexIndices), 3))

        return faceTriangleVertexIndices

    def iterFaceMaterialIndices(self, *indices):
        """
        Returns a generator that yields face material indices.
        If no arguments are supplied then all face-material indices will be yielded.

        :rtype: Iterator[int]
        """

        # Evaluate arguments
        #
        numIndices = len(indices)

        if numIndices == 0:

            indices = range(self.numFaces())

        # Get connected shaders
        #
        dagPath = om.MDagPath.getAPathTo(self.object())
        fnMesh = om.MFnMesh(dagPath)

        shaders, polygonConnects = fnMesh.getConnectedShaders(dagPath.instanceNumber())

        # Iterate through indices
        #
        for index in indices:

            yield polygonConnects[index]

    def getAssignedMaterials(self):
        """
        Returns a list of material-texture pairs from this mesh.

        :rtype: List[Tuple[Any, str]]
        """

        # Get connected shaders
        #
        dagPath = om.MDagPath.getAPathTo(self.object())
        fnMesh = om.MFnMesh(dagPath)

        shaders, polygonConnects = fnMesh.getConnectedShaders(dagPath.instanceNumber())
        numShaders = len(shaders)

        # Get associated material and textures
        #
        materials = [None] * numShaders

        for (i, shader) in enumerate(shaders):

            # Check if surface shader has any textures
            #
            material = om.MFnDependencyNode(shader).findPlug('surfaceShader', True).source().node()

            textures = dagutils.dependsOn(material, apiType=om.MFn.kFileTexture)
            numTextures = len(textures)

            if numTextures > 0:

                texturePath = om.MFnDependencyNode(textures[0]).findPlug('fileTextureName', True).asString()
                materials[i] = (material, texturePath)

            else:

                materials[i] = (material, '')

        return materials

    def numUVSets(self):
        """
        Returns the number of UV sets.

        :rtype: int
        """

        return om.MFnMesh(self.object()).numUVSets

    def getUVSetNames(self):
        """
        Returns the UV set names.

        :rtype: List[str]
        """

        return om.MFnMesh(self.object()).getUVSetNames()

    def getUVSetName(self, channel):
        """
        Returns the UV set name at the specified index.

        :type channel: int
        :rtype: str
        """

        uvSetNames = self.getUVSetNames()
        numUVSetNames = len(uvSetNames)

        if 0 <= channel < numUVSetNames:

            return uvSetNames[channel]

        else:

            return ''

    def numUVs(self, channel=0):
        """
        Returns the number of UV points from the specified set.

        :type channel: int
        :rtype: int
        """

        return om.MFnMesh(self.object()).numUVs(uvSet=self.getUVSetName(channel))

    def iterUVs(self, *indices, channel=0):
        """
        Returns a generator that yields UV vertex points from the specified set.

        :type channel: int
        :rtype: iter
        """

        # Evaluate arguments
        #
        numIndices = len(indices)

        if numIndices == 0:

            indices = range(self.numUVs(channel=channel))

        # Iterate through indices
        #
        fnMesh = om.MFnMesh(self.object())

        uvSet = self.getUVSetName(channel)
        uValues, vValues = fnMesh.getUVs(uvSet=uvSet)

        for index in indices:

            yield uValues[index], vValues[index]

    def iterAssignedUVs(self, *indices, channel=0):
        """
        Returns a generator that yields UV face-vertex indices from the specified set.

        :type channel: int
        :rtype: iter
        """

        # Evaluate arguments
        #
        numIndices = len(indices)

        if numIndices == 0:

            indices = range(self.numFaces())

        # Get associated UV set name
        #
        fnMesh = om.MFnMesh(self.object())

        uvSet = self.getUVSetName(channel)
        uvCounts, uvIndices = fnMesh.getAssignedUVs(uvSet=uvSet)

        faceVertexIndices = list(meshutils.package(uvCounts, uvIndices))

        for index in indices:

            yield faceVertexIndices[index]

    def iterTangentsAndBinormals(self, *indices, cls=Vector, channel=0):
        """
        Returns a generator that yields face-vertex tangents and binormals for the specified channel.

        :type cls: Callable
        :type channel: int
        :rtype: Iterator[List[Vector], List[Vector]]
        """

        # Evaluate arguments
        #
        numIndices = len(indices)

        if numIndices == 0:

            indices = range(self.numFaces())

        # Iterate through indices
        #
        fnMesh = om.MFnMesh(self.object())
        uvSet = self.getUVSetName(channel)

        for index in indices:

            tangents = fnMesh.getFaceVertexTangents(index, uvSet=uvSet)
            binormals = fnMesh.getFaceVertexBinormals(index, uvSet=uvSet)

            yield list(map(cls, tangents)), list(map(cls, binormals))

    def numColorSets(self):
        """
        Returns the number of vertex color sets currently in use.

        :rtype: int
        """

        return om.MFnMesh(self.object()).numColorSets

    def getColorSetNames(self):
        """
        Returns a list of color set names.

        :rtype: List[str]
        """

        return om.MFnMesh(self.object()).getColorSetNames()

    def getColorSetName(self, channel):
        """
        Returns the color set name at the specified channel.

        :type channel: int
        :rtype: str
        """

        colorSetNames = om.MFnMesh(self.object()).getColorSetNames()
        numColorSetNames = len(colorSetNames)

        if 0 <= channel < numColorSetNames:

            return colorSetNames[channel]

        else:

            return ''

    def iterColors(self, cls=Colour, channel=0):
        """
        Returns a generator that yields index-color pairs for the specified vertex color channel.

        :type cls: Callable
        :type channel: int
        :rtype: Iterator[colour.Colour]
        """

        colorSet = self.getColorSetName(channel)
        colors = om.MFnMesh(self.object()).getColors(colorSet=colorSet)

        for color in colors:

            yield cls(color.r, color.g, color.b, color.a)

    def iterFaceVertexColorIndices(self, *indices, channel=0):
        """
        Returns a generator that yields face-vertex color indices for the specified faces.

        :type channel: int
        :rtype: Iterator[List[int]]
        """

        # Evaluate arguments
        #
        numIndices = len(indices)

        if numIndices == 0:

            indices = range(self.numFaces())

        # Iterate through vertices
        #
        fnMesh = om.MFnMesh(self.object())
        colorSet = self.getColorSetName(channel)
        faceVertexIndices = self.getFaceVertexIndices(*indices)

        for (faceIndex, vertexIndices) in zip(indices, faceVertexIndices):

            colorIndices = [fnMesh.getColorIndex(faceIndex, physicalIndex, colorSet=colorSet) for (physicalIndex, logicalIndex) in enumerate(vertexIndices)]
            yield colorIndices

    def iterConnectedVertices(self, *indices, **kwargs):
        """
        Returns a generator that yields the connected vertex elements.

        :type indices: Union[int, List[int]]
        :key componentType: ComponentType
        :rtype: Iterator[int]
        """

        # Inspect component type
        #
        componentType = kwargs.get('componentType', self.ComponentType.Vertex)

        if componentType == self.ComponentType.Vertex:

            iterVertices = om.MItMeshVertex(self.object())

            for arg in indices:

                iterVertices.setIndex(arg)
                connectedVertices = iterVertices.getConnectedVertices()

                for connectedVertex in connectedVertices:

                    yield connectedVertex

        elif componentType == self.ComponentType.Edge:

            iterEdges = om.MItMeshEdge(self.object())

            for arg in indices:

                iterEdges.setIndex(arg)

                for edgeVertIndex in range(2):

                    yield iterEdges.vertexId(edgeVertIndex)

        elif componentType == self.ComponentType.Face:

            iterFaces = om.MItMeshPolygon(self.object())

            for arg in indices:

                iterFaces.setIndex(arg)
                connectedVertices = iterFaces.getVertices()

                for connectedVertex in connectedVertices:

                    yield connectedVertex

        else:

            raise TypeError('iterConnectedVertices() expects a valid component type (%s given)' % componentType)

    def iterConnectedEdges(self, *indices, **kwargs):
        """
        Returns a generator that yields the connected edge elements.

        :type indices: Union[int, List[int]]
        :key componentType: ComponentType
        :rtype: Iterator[int]
        """

        # Inspect component type
        #
        componentType = kwargs.get('componentType', self.ComponentType.Edge)

        if componentType == self.ComponentType.Vertex:

            iterVertices = om.MItMeshVertex(self.object())

            for arg in indices:

                iterVertices.setIndex(arg)
                connectedEdges = iterVertices.getConnectedEdges()

                for connectedEdge in connectedEdges:

                    yield connectedEdge

        elif componentType == self.ComponentType.Edge:

            iterEdges = om.MItMeshEdge(self.object())

            for arg in indices:

                iterEdges.setIndex(arg)
                connectedEdges = iterEdges.getConnectedEdges()

                for connectedEdge in connectedEdges:

                    yield connectedEdge

        elif componentType == self.ComponentType.Face:

            iterFaces = om.MItMeshPolygon(self.object())

            for arg in indices:

                iterFaces.setIndex(arg)
                connectedEdges = iterFaces.getEdges()

                for connectedEdge in connectedEdges:

                    yield connectedEdge

        else:

            raise TypeError('iterConnectedEdges() expects a valid component type (%s given)' % componentType)

    def iterConnectedFaces(self, *indices, **kwargs):
        """
        Returns a generator that yields the connected face elements.

        :type indices: Union[int, List[int]]
        :key componentType: ComponentType
        :rtype: Iterator[int]
        """

        # Inspect component type
        #
        componentType = kwargs.get('componentType', self.ComponentType.Face)

        if componentType == self.ComponentType.Vertex:

            iterVertices = om.MItMeshVertex(self.object())

            for arg in indices:

                iterVertices.setIndex(arg)
                connectedFaces = iterVertices.getConnectedFaces()

                for connectedFace in connectedFaces:

                    yield connectedFace

        elif componentType == self.ComponentType.Edge:

            iterEdges = om.MItMeshEdge(self.object())

            for arg in indices:

                iterEdges.setIndex(arg)
                connectedFaces = iterEdges.getConnectedFaces()

                for connectedFace in connectedFaces:

                    yield connectedFace

        elif componentType == self.ComponentType.Face:

            iterFaces = om.MItMeshPolygon(self.object())

            for arg in indices:

                iterFaces.setIndex(arg)
                connectedFaces = iterFaces.getConnectedFaces()

                for connectedFace in connectedFaces:

                    yield connectedFace

        else:

            raise TypeError('iterConnectedFaces() expects a valid component type (%s given)' % componentType)

    @classmethod
    def iterInstances(cls, apiType=om.MFn.kMesh):
        """
        Returns a generator that yields mesh instances.

        :type apiType: int
        :rtype: iter
        """

        return dagutils.iterNodes(apiType)
