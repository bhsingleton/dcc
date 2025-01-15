import os
import json

from maya import cmds as mc, OpenMaya as lom
from maya.api import OpenMaya as om
from itertools import chain
from ..libs import attributeutils, plugutils, plugmutators, dagutils, shapeutils, transformutils
from ...python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MShapeEncoder(json.JSONEncoder):
    """
    Overload of `JSONEncoder` that encodes Maya shapes.
    """

    # region Dunderscores
    __slots__ = ()

    __shape_types__ = {
        'locator': 'serializeLocator',
        'pointHelper': 'serializePointHelper',
        'nurbsCurve': 'serializeNurbsCurve',
        'bezierCurve': 'serializeNurbsCurve',
        'nurbsTrimSurface': 'serializeNurbsTrimSurface',
        'nurbsSurface': 'serializeNurbsSurface',
        'mesh': 'serializeMesh'
    }
    # endregion

    # region Methods
    def default(self, obj):
        """
        Returns a json serializable object for the given value.

        :type obj: Any
        :rtype: Any
        """

        # Evaluate object type
        #
        if isinstance(obj, om.MObject):

            # Check if delegate exists
            #
            typeName = str(om.MFnDependencyNode(obj).typeName)
            delegate = self.__shape_types__.get(typeName, '')
            func = getattr(self, delegate, None)

            if callable(func):

                return func(obj)

            else:

                raise TypeError(f'default() expects a valid shape type ({typeName} given)!')

        elif isinstance(obj, om.MObjectHandle):

            return self.default(obj.object())

        elif isinstance(obj, om.MDagPath):

            return self.default(obj.node())

        else:

            return super(MShapeEncoder, self).default(obj)

    @classmethod
    def serializeLocator(cls, obj):
        """
        Dumps the supplied locator into a json serializable object.

        :type obj: om.MObject
        :rtype: dict
        """

        # Get locator parameters
        #
        localPosition = plugmutators.getValue(obj, 'localPosition')
        localScale = plugmutators.getValue(obj, 'localScale')
        lineWidth = plugmutators.getValue(obj, 'lineWidth')

        return {
            'typeName': 'locator',
            'localPosition': localPosition,
            'localScale': localScale,
            'lineWidth': lineWidth
        }

    @classmethod
    def serializePointHelper(cls, obj):
        """
        Dumps the supplied point-helper into a json serializable object.

        :type obj: om.MObject
        :rtype: dict
        """

        # Get point-helper parameters
        #
        size = plugmutators.getValue(obj, 'size')
        localPosition = plugmutators.getValue(obj, 'localPosition')
        localRotate = plugmutators.getValue(obj, 'localRotate')
        localScale = plugmutators.getValue(obj, 'localScale')
        drawables = {attributeutils.getAttributeName(attribute): plugmutators.getValue(obj, attribute) for attribute in attributeutils.iterCategory(obj, 'Drawable')}
        lineWidth = plugmutators.getValue(obj, 'lineWidth')

        return {
            'typeName': 'pointHelper',
            'size': size,
            'localPosition': localPosition,
            'localRotate': localRotate,
            'localScale': localScale,
            'drawables': drawables,
            'lineWidth': lineWidth
        }

    @classmethod
    def serializeNurbsCurve(cls, obj):
        """
        Dumps the supplied nurbs curve into a json serializable object.

        :type obj: om.MObject
        :rtype: dict
        """

        # Get nurbs curve parameters
        #
        dagPath = om.MDagPath.getAPathTo(obj)
        fnNurbsCurve = om.MFnNurbsCurve(dagPath)

        controlPoints = [(point.x, point.y, point.z, point.w) for point in fnNurbsCurve.cvPositions()]
        knots = [knot for knot in fnNurbsCurve.knots()]
        degrees = int(fnNurbsCurve.degree)
        form = int(fnNurbsCurve.form)
        lineWidth = plugmutators.getValue(obj, 'lineWidth')

        return {
            'typeName': 'nurbsCurve',
            'controlPoints': controlPoints,
            'knots': knots,
            'degree': degrees,
            'form': form,
            'lineWidth': lineWidth
        }

    @classmethod
    def serializeNurbsTrimSurface(cls, obj):
        """
        Dumps the supplied nurbs surface's trimmed boundaries into a json serializable object.
        Please note Autodesk have yet to implement these methods in their newest API!

        :type obj: lom.MObject
        :rtype: List[dict]
        """

        # Check number of regions
        # If there are no regions then this surface has no trims!
        #
        fnNurbsSurface = lom.MFnNurbsSurface(obj)
        numRegions = fnNurbsSurface.numRegions()

        if numRegions == 0:

            return []

        # Iterate through regions
        #
        fnNurbsCurve = lom.MFnNurbsCurve()
        items = [None] * numRegions

        for region in range(numRegions):

            # Get trim boundary from region
            #
            boundary = lom.MTrimBoundaryArray()
            fnNurbsSurface.getTrimBoundaries(boundary, region, True)

            numBoundaries = boundary.length()

            for i in range(numBoundaries):

                curveData = boundary.getMergedBoundary(j)
                fnNurbsCurve.setObject(curveData)

                # Get control points
                #
                numCVs = fnNurbsCurve.numCVs()
                controlsPoints = [None] * numCVs

                for j in range(numCVs):

                    point = fnNurbsCurve.getCV(j)
                    controlsPoints.set([point.x(), point.y(), point.z(), point.w()], j)

                # Get knots
                #
                numKnots = fnNurbsCurve.numKnots()
                knots = [None] * numKnots

                for j in range(numKnots):

                    knots.set(fnNurbsCurve.knot(j), j)

                # Commit curve parameters to dictionary
                #
                items[i] = {
                    'typeName': 'nurbsCurveData',  # Forcing type hint for decoder
                    'controlPoints': controlsPoints,
                    'knots': knots,
                    'degree': fnNurbsCurve.degree(),
                    'form': fnNurbsCurve.form(),
                }

        return items

    @classmethod
    def serializeNurbsSurface(cls, obj):
        """
        Dumps the supplied nurbs surface into a json serializable object.

        :type obj: om.MObject
        :rtype: dict
        """

        # Get nurbs surface parameters
        #
        dagPath = om.MDagPath.getAPathTo(obj)
        fnNurbsSurface = om.MFnNurbsSurface(dagPath)

        controlPoints = [(point.x, point.y, point.z, point.w) for point in fnNurbsSurface.cvPositions()]
        uKnots = [x for x in fnNurbsSurface.knotsInU()]
        vKnots = [x for x in fnNurbsSurface.knotsInV()]
        uDegree = int(fnNurbsSurface.degreeInU)
        vDegree = int(fnNurbsSurface.degreeInV)
        uForm = int(fnNurbsSurface.formInU)
        vForm = int(fnNurbsSurface.formInV)
        boundaries = cls.nurbsTrimSurface(dagutils.demoteMObject(obj))
        precision = plugmutators.getValue(obj, 'precision')

        return {
            'typeName': 'nurbsSurface',
            'controlPoints': controlPoints,
            'uKnots': uKnots,
            'vKnots': vKnots,
            'uDegree': uDegree,
            'vDegree': vDegree,
            'uForm': uForm,
            'vForm': vForm,
            'boundaries': boundaries,
            'precision': precision
        }

    @classmethod
    def serializeMesh(cls, obj):
        """
        Dumps the supplied mesh into a json serializable object.

        :type obj: om.MObject
        :rtype: dict
        """

        # Get mesh parameters
        #
        dagPath = om.MDagPath.getAPathTo(obj)
        fnMesh = om.MFnMesh(dagPath)

        controlPoints = [(point.x, point.y, point.z, point.w) for point in fnMesh.getPoints()]
        polygonConnects = [fnMesh.getPolygonVertices(x) for x in range(fnMesh.numPolygons)]
        polygonCounts = [fnMesh.polygonVertexCount(x) for x in range(fnMesh.numPolygons)]
        faceVertexNormals = [[(y.x, y.y, y.z) for y in fnMesh.getFaceVertexNormals(x)] for x in range(fnMesh.numPolygons)]
        edgeSmoothings = [fnMesh.isEdgeSmooth(x) for x in range(fnMesh.numEdges)]

        return {
            'typeName': 'mesh',
            'controlPoints': controlPoints,
            'polygonConnects': polygonConnects,
            'polygonCounts': polygonCounts,
            'faceVertexNormals': faceVertexNormals,
            'edgeSmoothings': edgeSmoothings
        }
    # endregion


class MShapeDecoder(json.JSONDecoder):
    """
    Overload of `JSONDecoder` that decodes Maya shapes.
    """

    # region Dunderscores
    __slots__ = (
        '_size',
        '_localPosition',
        '_localRotate',
        '_localScale',
        '_colorIndex',
        '_colorRGB',
        '_side',
        '_lineWidth',
        '_parent'
    )

    __shape_types__ = {
        'locator': 'deserializeLocator',
        'pointHelper': 'deserializePointHelper',
        'nurbsCurve': 'deserializeNurbsCurve',
        'bezierCurve': 'deserializeNurbsCurve',
        'nurbsSurface': 'deserializeNurbsSurface',
        'mesh': 'deserializeMesh'
    }

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key size: float
        :key localPosition: Union[om.MVector, Tuple[float, float, float]]
        :key localRotate: Union[om.MVector, Tuple[float, float, float]]
        :key localScale: Union[om.MVector, Tuple[float, float, float]]
        :key lineWidth: float
        :key parent: om.MObject
        :rtype: None
        """

        # Declare private variables
        #
        self._size = kwargs.pop('size', 1.0)
        self._localPosition = kwargs.pop('localPosition', om.MVector.kZeroVector)
        self._localRotate = kwargs.pop('localRotate', om.MVector.kZeroVector)
        self._localScale = kwargs.pop('localScale', om.MVector.kOneVector)
        self._colorIndex = kwargs.pop('colorIndex', None)
        self._colorRGB = kwargs.pop('colorRGB', None)
        self._side = kwargs.pop('side', None)
        self._lineWidth = kwargs.pop('lineWidth', -1.0)
        self._parent = kwargs.pop('parent', om.MObject.kNullObj)

        # Override object hook
        #
        kwargs['object_hook'] = self.default

        # Call parent method
        #
        super(MShapeDecoder, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def colorIndex(self):
        """
        Getter method that returns the color index.

        :rtype: Union[int, None]
        """

        return self._colorIndex

    @property
    def colorRGB(self):
        """
        Getter method that returns the color RGB value.

        :rtype: Union[Tuple[float, float, float], None]
        """

        return self._colorRGB

    @property
    def side(self):
        """
        Getter method that returns the side flag.

        :rtype: Union[IntEnum, None]
        """

        return self._side

    @property
    def lineWidth(self):
        """
        Getter method that returns the line width.

        :rtype: Union[int, None]
        """

        return self._lineWidth
    # endregion

    # region Methods
    def default(self, obj):
        """
        Returns a json deserialized object from the supplied dictionary.

        :type obj: dict
        :rtype: om.MObject
        """

        # Check if delegate exists
        #
        typeName = obj.get('typeName', '')
        delegate = self.__shape_types__.get(typeName, None)

        if stringutils.isNullOrEmpty(delegate):

            return obj

        # Call delegate with parameters
        #
        func = getattr(self, delegate)

        shape = func(
            obj,
            size=self._size,
            localPosition=self._localPosition,
            localRotate=self._localRotate,
            localScale=self._localScale,
            parent=self._parent
        )

        if shape.hasFn(om.MFn.kShape):

            shapeutils.colorizeShape(shape, colorIndex=self.colorIndex, colorRGB=self.colorRGB, side=self.side, lineWidth=self.lineWidth)

        return shape

    @staticmethod
    def composeMatrix(**kwargs):
        """
        Composes a transform matrix from the supplied arguments.

        :key size: float
        :key localPosition: Union[om.MVector, Tuple[float, float, float]]
        :key localRotate: Union[om.MVector, Tuple[float, float, float]]
        :key localScale: Union[om.MVector, Tuple[float, float, float]]
        :rtype: om.MMatrix
        """

        size = kwargs.get('size', 1.0)
        localPosition = kwargs.get('localPosition', om.MVector.kZeroVector)
        localRotate = kwargs.get('localRotate', om.MVector.kZeroVector)
        localScale = kwargs.get('localScale', om.MVector.kOneVector)

        sizeMatrix = transformutils.createScaleMatrix(size)
        translateMatrix = transformutils.createTranslateMatrix(localPosition)
        rotateMatrix = transformutils.createRotationMatrix(localRotate)
        scaleMatrix = transformutils.createScaleMatrix(localScale)

        return (scaleMatrix * sizeMatrix) * rotateMatrix * translateMatrix

    @staticmethod
    def demoteMatrix(matrix):
        """
        Demotes the supplied matrix into its legacy equivalent.

        :type matrix: om.MMatrix
        :rtype: lom.MMatrix
        """

        demotedMatrix = lom.MMatrix()

        for row in range(4):

            for column in range(4):

                lom.MScriptUtil.setDoubleArray(demotedMatrix[row], column, matrix.getElement(row, column))

        return demotedMatrix

    @classmethod
    def deserializeLocator(cls, obj, **kwargs):
        """
        Returns a locator using the supplied json object.

        :type obj: dict
        :key parent: om.MObject
        :rtype: om.MObject
        """

        # Decompose object
        #
        localPosition = om.MVector(obj['localPosition'])
        localScale = om.MVector(obj['localScale'])

        # Check if a parent was supplied
        #
        parent = kwargs.get('parent', om.MObject.kNullObj)
        hasParent = not parent.isNull()

        if not hasParent:

            parent = dagutils.createNode('transform')

        locator = dagutils.createNode('locator', parent=parent)
        plugmutators.setValue(locator, 'localPosition', localPosition)
        plugmutators.setValue(locator, 'localScale', localScale)

        return locator

    @classmethod
    def deserializePointHelper(cls, obj, **kwargs):
        """
        Returns a point-helper using the supplied json object.

        :type obj: dict
        :key parent: om.MObject
        :rtype: om.MObject
        """

        # Decompose object
        #
        size = obj['size']
        localPosition = om.MVector(obj['localPosition'])
        localRotate = om.MVector(obj['localRotate'])
        localScale = om.MVector(obj['localScale'])

        # Check if a parent was supplied
        #
        parent = kwargs.get('parent', om.MObject.kNullObj)
        hasParent = not parent.isNull()

        if not hasParent:

            parent = dagutils.createNode('transform')

        pointHelper = dagutils.createNode('pointHelper', parent=parent)
        plugmutators.setValue(pointHelper, 'size', size)
        plugmutators.setValue(pointHelper, 'localPosition', localPosition)
        plugmutators.setValue(pointHelper, 'localRotate', localRotate)
        plugmutators.setValue(pointHelper, 'localScale', localScale)

        for (name, enabled) in obj['drawables'].items():

            plugmutators.setValue(pointHelper, name, enabled)

        return pointHelper

    @classmethod
    def deserializeNurbsCurve(cls, obj, **kwargs):
        """
        Returns a nurbs-curve using the supplied json object.

        :type obj: dict
        :key parent: om.MObject
        :rtype: om.MObject
        """

        # Decompose object
        #
        matrix = cls.composeMatrix(**kwargs)

        cvs = om.MPointArray(list(map(lambda point: om.MPoint(point) * matrix, obj['controlPoints'])))
        knots = om.MDoubleArray(obj['knots'])
        degree = obj['degree']
        form = obj['form']
        is2D = kwargs.get('is2D', False)
        rational = kwargs.get('rational', True)

        # Check if a parent was supplied
        #
        parent = kwargs.get('parent', om.MObject.kNullObj)
        hasParent = not parent.isNull()

        if hasParent:

            fnNurbsCurve = om.MFnNurbsCurve()
            curve = fnNurbsCurve.create(cvs, knots, degree, form, is2D, rational, parent=parent)

            return curve

        else:

            fnCurveData = om.MFnNurbsCurveData()
            curveData = fnCurveData.create()

            fnCurve = om.MFnNurbsCurve()
            fnCurve.create(cvs, knots, degree, form, is2D, rational, parent=curveData)

            return curveData

    @classmethod
    def deserializeNurbsTrimBoundary(cls, obj, **kwargs):
        """
        Creates a legacy nurbs curve data object from the supplied object.

        :type obj: dict
        :key matrix: lom.MMatrix
        :rtype: lom.MObject
        """

        # Create new data object
        #
        fnNurbsCurveData = lom.MFnNurbsCurveData()
        curveData = fnNurbsCurveData.create()

        # Collect control points
        #
        numControlPoints = len(obj['controlPoints'])
        controlPoints = lom.MPointArray(numControlPoints)

        matrix = kwargs.get('matrix', lom.MMatrix.identity)

        for (index, controlPoint) in enumerate(obj['controlPoints']):

            point = lom.MPoint(controlPoint[0], controlPoint[1], controlPoint[2]) * matrix
            controlPoints.set(point, index)

        # Collect knots
        #
        numKnots = len(obj['knots'])
        knots = lom.MDoubleArray(numKnots)

        for (index, knot) in enumerate(obj['knots']):

            knots.set(knot, index)

        # Get curve parameters
        #
        degree = obj['degree']
        form = obj['form']

        fnNurbsCurve = lom.MFnNurbsCurve()
        fnNurbsCurve.create(controlPoints, knots, degree, form, False, True, curveData)

        return curveData

    @classmethod
    def deserializeNurbsSurface(cls, obj, **kwargs):
        """
        Returns a nurbs-surface using the supplied json object.

        :type obj: dict
        :key parent: om.MObject
        :rtype: om.MObject
        """

        # Decompose object
        #
        matrix = cls.composeMatrix(**kwargs)

        cvs = om.MPointArray(list(map(lambda point: om.MPoint(point) * matrix, obj['controlPoints'])))
        uKnots = om.MDoubleArray(obj['uKnots'])
        vKnots = om.MDoubleArray(obj['vKnots'])
        uDegree = obj['uDegree']
        vDegree = obj['vDegree']
        uForm = obj['uForm']
        vForm = obj['vForm']
        rational = kwargs.get('rational', True)

        # Check if a parent was supplied
        #
        parent = kwargs.get('parent', om.MObject.kNullObj)
        hasParent = not parent.isNull()

        if hasParent:

            # Create nurbs surface
            #
            fnNurbsSurface = om.MFnNurbsSurface()
            surface = fnNurbsSurface.create(cvs, uKnots, vKnots, uDegree, vDegree, uForm, vForm, rational, parent)

            # Trim surface
            #
            boundaries = obj['boundaries']
            numBoundaries = len(boundaries)

            if numBoundaries > 0:

                # Deserialize boundaries
                #
                curveDataArray = lom.MObjectArray(numBoundaries)
                boundaryMatrix = cls.demoteMatrix(matrix)

                for (index, boundary) in enumerate(boundaries):

                    curveData = cls.deserializeNurbsTrimBoundary(boundary, matrix=boundaryMatrix)
                    curveDataArray.set(curveData, index)

                # Apply trim boundaries to nurbs surface
                #
                trims = lom.MTrimBoundaryArray()
                trims.append(curveDataArray)

                fnNurbsSurface = lom.MFnNurbsSurface(dagutils.demoteMObject(surface))
                fnNurbsSurface.trimWithBoundaries(trims)

            # Update curve precision
            #
            plug = fnNurbsSurface.findPlug('curvePrecisionShaded', True)
            plug.setFloat(obj['precision'])

            return surface

        else:

            # Create nurbs surface data
            #
            fnSurfaceData = om.MFnNurbsSurfaceData()
            surfaceData = fnSurfaceData.create()

            fnNurbsSurface = om.MFnNurbsSurface()
            fnNurbsSurface.create(cvs, uKnots, vKnots, uDegree, vDegree, uForm, vForm, rational, parent=surfaceData)

            return surfaceData

    @classmethod
    def deserializeMesh(cls, obj, **kwargs):
        """
        Returns a mesh using the supplied json object.

        :type obj: dict
        :key parent: om.MObject
        :rtype: om.MObject
        """

        # Decompose object
        #
        matrix = cls.composeMatrix(**kwargs)

        vertices = om.MPointArray(list(map(lambda point: om.MPoint(point) * matrix, obj['controlPoints'])))
        polygonCounts = om.MIntArray(obj['polygonCounts'])
        polygonConnects = om.MIntArray(obj['polygonConnects'])

        # Check if a parent was supplied
        #
        parent = kwargs.get('parent', om.MObject.kNullObj)
        hasParent = not parent.isNull()

        if hasParent:

            # Create mesh
            #
            fnMesh = om.MFnMesh()
            mesh = fnMesh.create(vertices, polygonCounts, list(chain(*polygonConnects)), parent=parent)

            # Update edge smoothings
            #
            edgeSmoothings = obj['edgeSmoothings']

            for edgeIndex in range(fnMesh.numEdges):

                fnMesh.setEdgeSmoothing(edgeIndex, edgeSmoothings[edgeIndex])

            fnMesh.cleanupEdgeSmoothing()

            # Update face vertex normals
            #
            faceVertexNormals = obj['faceVertexNormals']

            for polygonIndex in range(fnMesh.numPolygons):

                faceVertices = fnMesh.getPolygonVertices(polygonIndex)
                normals = faceVertexNormals[polygonIndex]

                for (faceVertexIndex, faceVertexNormal) in zip(faceVertices, normals):

                    fnMesh.setFaceVertexNormal(om.MVector(faceVertexNormal), polygonIndex, faceVertexIndex)

            return mesh

        else:

            # Create mesh data
            #
            fnMeshData = om.MFnMeshData()
            meshData = fnMeshData.create()

            fnMesh = om.MFnMesh()
            fnMesh.create(vertices, polygonCounts, list(chain(*polygonConnects)), parent=meshData)

            return meshData
    # endregion


def dumps(node, **kwargs):
    """
    Dumps the supplied node's shapes into a JSON serializable string.

    :type node: Union[str, om.MObject, om.MDagPath]
    :key indent: int
    :key sort_keys: bool
    :rtype: List[dict]
    """

    # Evaluate supplied node
    #
    node = dagutils.getMObject(node)
    shapes = None

    if node.hasFn(om.MFn.kTransform):

        shapes = list(dagutils.iterShapes(node))

    elif node.hasFn(om.MFn.kShape):

        shapes = [node]

    else:

        raise TypeError(f'dumps() expects a shape node ({node.apiTypeStr} given)!')

    # Serialize shapes as string
    #
    return json.dumps(shapes, cls=MShapeEncoder, **kwargs)


def dump(node, filePath, **kwargs):
    """
    Dumps the supplied node's shapes into a JSON serializable object.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type filePath: str
    :key indent: int
    :key sort_keys: bool
    :rtype: None
    """

    # Evaluate supplied node
    #
    node = dagutils.getMObject(node)
    shapes = None

    if node.hasFn(om.MFn.kTransform):

        shapes = list(dagutils.iterShapes(node))

    elif node.hasFn(om.MFn.kShape):

        shapes = [node]

    else:

        raise TypeError(f'dump() expects a shape node ({node.apiTypeStr} given)!')

    # Serialize shapes to file
    #
    with open(filePath, 'w') as jsonFile:

        log.info(f'Saving shapes to: {filePath}')
        json.dump(shapes, jsonFile, cls=MShapeEncoder, **kwargs)


def loads(string, **kwargs):
    """
    Loads the shapes from the supplied JSON string onto the specified parent.

    :type string: str
    :key size: float
    :key localPosition: Union[om.MVector, Tuple[float, float, float]]
    :key localRotate: Union[om.MVector, Tuple[float, float, float]]
    :key localScale: Union[om.MVector, Tuple[float, float, float]]
    :key lineWidth: float
    :key parent: om.MObject
    :rtype: List[om.MObject]
    """

    # Check if file exists
    #
    if stringutils.isNullOrEmpty(string):

        raise TypeError('loads() expects a valid string!')

    # Load shapes onto supplied parent
    #
    return json.loads(string, cls=MShapeDecoder, **kwargs)


def load(filePath, **kwargs):
    """
    Loads the shapes from the supplied JSON file onto the specified parent.

    :type filePath: str
    :key size: float
    :key localPosition: Union[om.MVector, Tuple[float, float, float]]
    :key localRotate: Union[om.MVector, Tuple[float, float, float]]
    :key localScale: Union[om.MVector, Tuple[float, float, float]]
    :key lineWidth: float
    :key parent: om.MObject
    :rtype: List[om.MObject]
    """

    # Check if file exists
    #
    if not os.path.exists(filePath):

        raise TypeError('load() expects a valid file path!')

    # Load shapes onto supplied parent
    #
    with open(filePath, 'r') as jsonFile:

        return json.load(jsonFile, cls=MShapeDecoder, **kwargs)
