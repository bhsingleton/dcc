import os
import json

from maya import cmds as mc, OpenMaya as lom
from maya.api import OpenMaya as om
from itertools import chain
from ..libs import dagutils, transformutils, shapeutils

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

            delegate = self.__shape_types__[om.MFnDependencyNode(obj).typeName]
            func = getattr(self, delegate)

            return func(obj)

        elif isinstance(obj, om.MDagPath):

            return self.default(obj.node())

        else:

            return super(MShapeEncoder, self).default(obj)

    @classmethod
    def serializeNurbsCurve(cls, obj):
        """
        Dumps the supplied nurbs curve into a json compatible object.

        :type obj: om.MObject
        :rtype: dict
        """

        # Get nurbs curve parameters
        #
        dagPath = om.MDagPath.getAPathTo(obj)
        fnNurbsCurve = om.MFnNurbsCurve(dagPath)

        return {
            'typeName': fnNurbsCurve.typeName,
            'controlPoints': [[point.x, point.y, point.z, point.w] for point in fnNurbsCurve.cvPositions()],
            'knots': [x for x in fnNurbsCurve.knots()],
            'degree': fnNurbsCurve.degree,
            'form': fnNurbsCurve.form,
            'lineWidth': fnNurbsCurve.findPlug('lineWidth', True).asFloat()
        }

    @classmethod
    def serializeNurbsTrimSurface(cls, obj):
        """
        Dumps the supplied nurb surface's trimmed boundaries into a json compatible object.
        Please note Autodesk have yet to implement these methods in their newest API!

        :type obj: lom.MObject
        :rtype: List[dict]
        """

        # Check number of regions
        # If zero then this surface has no trimmed surfaces
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
        Dumps the supplied nurbs surface into a json compatible object.

        :type obj: om.MObject
        :rtype: dict
        """

        # Get nurbs surface parameters
        #
        dagPath = om.MDagPath.getAPathTo(obj)
        fnNurbsSurface = om.MFnNurbsSurface(dagPath)

        return {
            'typeName': fnNurbsSurface.typeName,
            'controlPoints': [[point.x, point.y, point.z, point.w] for point in fnNurbsSurface.cvPositions()],
            'uKnots': [x for x in fnNurbsSurface.knotsInU()],
            'vKnots': [x for x in fnNurbsSurface.knotsInV()],
            'uDegree': fnNurbsSurface.degreeInU,
            'vDegree': fnNurbsSurface.degreeInV,
            'uForm': fnNurbsSurface.formInU,
            'vForm': fnNurbsSurface.formInV,
            'boundaries': cls.nurbsTrimSurface(dagutils.demoteMObject(obj)),
            'precision': fnNurbsSurface.findPlug('curvePrecisionShaded', True).asFloat()
        }

    @classmethod
    def serializeMesh(cls, obj):
        """
        Dumps the supplied mesh into a json compatible object.

        :type obj: om.MObject
        :rtype: dict
        """

        # Get mesh parameters
        #
        dagPath = om.MDagPath.getAPathTo(obj)
        fnMesh = om.MFnMesh(dagPath)

        return {
            'typeName': fnMesh.typeName,
            'controlPoints': [[point.x, point.y, point.z, point.w] for point in fnMesh.getPoints()],
            'polygonConnects': [fnMesh.getPolygonVertices(x) for x in range(fnMesh.numPolygons)],
            'polygonCounts': [fnMesh.polygonVertexCount(x) for x in range(fnMesh.numPolygons)],
            'faceVertexNormals': [[[y.x, y.y, y.z] for y in fnMesh.getFaceVertexNormals(x)] for x in range(fnMesh.numPolygons)],
            'edgeSmoothings': [fnMesh.isEdgeSmooth(x) for x in range(fnMesh.numEdges)]
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
        'nurbsCurve': 'deserializeNurbsCurve',
        'bezierCurve': 'deserializeNurbsCurve',
        'nurbsTrimSurface': 'deserializeNurbsTrimSurface',
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
        Object hook for this decoder.

        :type obj: dict
        :rtype: om.MObject
        """

        # Evaluate type name
        #
        typeName = obj.get('typeName', '')
        func = getattr(self, self.__shape_types__[typeName], None)

        if callable(func):

            shape = func(
                obj,
                size=self._size,
                localPosition=self._localPosition,
                localRotate=self._localRotate,
                localScale=self._localScale,
                parent=self._parent
            )

            shapeutils.colorizeShape(shape, colorIndex=self.colorIndex, colorRGB=self.colorRGB, side=self.side, lineWidth=self.lineWidth)

            return shape

        else:

            return obj

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
    def deserializeNurbsCurve(cls, obj, **kwargs):
        """
        Creates a nurbs curve based on the supplied dictionary.

        :type obj: dict
        :key parent: om.MObject
        :rtype: om.MObject
        """

        # Collect arguments
        #
        matrix = cls.composeMatrix(**kwargs)

        cvs = om.MPointArray([om.MPoint(point) * matrix for point in obj['controlPoints']])
        knots = om.MDoubleArray(obj['knots'])
        degree = obj['degree']
        form = obj['form']

        # Create nurbs curve
        #
        parent = kwargs.get('parent', om.MObject.kNullObj)

        fnNurbsCurve = om.MFnNurbsCurve()
        curve = fnNurbsCurve.create(cvs, knots, degree, form, False, True, parent=parent)

        return curve

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
        Creates a nurbs surface based on the supplied object.

        :type obj: dict
        :key parent: om.MObject
        :rtype: om.MObject
        """

        # Collect arguments
        #
        matrix = cls.composeMatrix(**kwargs)

        cvs = om.MPointArray([om.MPoint(point) * matrix for point in obj['controlPoints']])
        uKnots = om.MDoubleArray(obj['uKnots'])
        vKnots = om.MDoubleArray(obj['vKnots'])
        uDegree = obj['uDegree']
        vDegree = obj['vDegree']
        uForm = obj['uForm']
        vForm = obj['vForm']

        # Create nurbs surface from function set
        #
        parent = kwargs.get('parent', om.MObject.kNullObj)

        fnNurbsSurface = om.MFnNurbsSurface()
        surface = fnNurbsSurface.create(cvs, uKnots, vKnots, uDegree, vDegree, uForm, vForm, True, parent)

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

            # Append curves to trim array
            #
            boundaries = lom.MTrimBoundaryArray()
            boundaries.append(curveDataArray)

            # Apply trim boundary to nurbs surface
            #
            fnNurbsSurface = lom.MFnNurbsSurface(dagutils.demoteMObject(surface))
            fnNurbsSurface.trimWithBoundaries(boundaries)

        # Update curve precision
        #
        plug = fnNurbsSurface.findPlug('curvePrecisionShaded', True)
        plug.setFloat(obj['precision'])

        return surface

    @classmethod
    def deserializeMesh(cls, obj, **kwargs):
        """
        Creates a mesh based on the supplied dictionary.

        :type obj: dict
        :key parent: om.MObject
        :rtype: om.MObject
        """

        # Collect arguments
        #
        matrix = cls.composeMatrix(**kwargs)

        vertices = om.MPointArray([om.MPoint(point) * matrix for point in obj['controlPoints']])
        polygonCounts = obj['polygonCounts']
        polygonConnects = obj['polygonConnects']

        # Create mesh from function set
        #
        parent = kwargs.get('parent', om.MObject.kNullObj)

        fnMesh = om.MFnMesh()
        mesh = fnMesh.create(vertices, polygonCounts, list(chain(*polygonConnects)), parent=parent)

        # Set edge smoothings
        #
        edgeSmoothings = obj['edgeSmoothings']

        for edgeIndex in range(fnMesh.numEdges):

            fnMesh.setEdgeSmoothing(edgeIndex, edgeSmoothings[edgeIndex])

        fnMesh.cleanupEdgeSmoothing()

        # Set face vertex normals
        #
        faceVertexNormals = obj['faceVertexNormals']

        for polygonIndex in range(fnMesh.numPolygons):

            faceVertices = fnMesh.getPolygonVertices(polygonIndex)
            normals = faceVertexNormals[polygonIndex]

            for (faceVertexIndex, faceVertexNormal) in zip(faceVertices, normals):

                fnMesh.setFaceVertexNormal(om.MVector(faceVertexNormal), polygonIndex, faceVertexIndex)

        return mesh
    # endregion


def createShapeTemplate(node, filePath):
    """
    Creates a shape template from the supplied transform or shape node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type filePath: str
    :rtype: None
    """

    # Evaluate api type
    #
    node = dagutils.getMObject(node)
    shapes = None

    if node.hasFn(om.MFn.kTransform):

        shapes = list(dagutils.iterShapes(node))

    elif node.hasFn(om.MFn.kShape):

        shapes = [node]

    else:

        raise TypeError(f'createShapeTemplate() expects a shape node ({node.apiTypeStr} given)!')

    # Save json file
    #
    with open(filePath, 'w') as jsonFile:

        log.info(f'Saving shape template to: {filePath}')
        json.dump(shapes, jsonFile, cls=MShapeEncoder, indent=4)


def loadShapeTemplate(filePath, **kwargs):
    """
    Recreates the shapes from the supplied file path.
    This name will be used to lookup the json file from the shapes directory.

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

        log.warning(f'Unable to locate shape template: {filePath}')
        return []

    # Iterate through shape nodes
    #
    with open(filePath, 'r') as jsonFile:

        return json.load(jsonFile, cls=MShapeDecoder, **kwargs)
