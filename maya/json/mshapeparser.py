import json

from maya.api import OpenMaya as om
from maya import OpenMaya as lom
from itertools import chain
from ..libs import dagutils, transformutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MShapeEncoder(json.JSONEncoder):
    """
    Overload of `JSONEncoder` used to create shape templates from shape nodes.
    """

    # region Dunderscores
    __slots__ = ()
    # endregion

    # region Methods
    def default(self, obj):
        """
        Returns a json serializable object for the given value.

        :type obj: Any
        :rtype: Any
        """

        if isinstance(obj, om.MObject):

            typeName = om.MFnDependencyNode(obj).typeName
            func = getattr(self, typeName)

            return func(obj)

        elif isinstance(obj, om.MDagPath):

            return self.default(obj.node())

        else:

            return super(MShapeEncoder, self).default(obj)

    @classmethod
    def nurbsCurve(cls, obj):
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
    def nurbsTrimSurface(cls, obj):
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
    def nurbsSurface(cls, obj):
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
    def mesh(cls, obj):
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
    Overload of `JSONDecoder` used to apply shape templates to transform nodes.
    """

    # region Dunderscores
    __slots__ = (
        '_size',
        '_localPosition',
        '_localRotate',
        '_localScale',
        '_lineWidth',
        '_parent'
    )

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
        self._lineWidth = kwargs.pop('lineWidth', -1.0)
        self._parent = kwargs.pop('parent', om.MObject.kNullObj)

        # Override object hook
        #
        kwargs['object_hook'] = self.default

        # Call parent method
        #
        super(MShapeDecoder, self).__init__(*args, **kwargs)
    # endregion

    # region Methods
    def default(self, obj):
        """
        Object hook for this decoder.

        :type obj: dict
        :rtype: om.MObject
        """

        # Inspect type name
        # We don't want to process any nurbs trim surfaces
        #
        typeName = obj.get('typeName', '')
        func = getattr(self, typeName, None)

        if callable(func):

            return func(
                obj,
                size=self._size,
                localPosition=self._localPosition,
                localRotate=self._localRotate,
                localScale=self._localScale,
                lineWidth=self._lineWidth,
                parent=self._parent
            )

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
    def nurbsCurve(cls, obj, **kwargs):
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

        # Update line width
        #
        lineWidth = kwargs.get('lineWidth', -1.0)

        plug = fnNurbsCurve.findPlug('lineWidth', True)
        plug.setFloat(lineWidth)

        return curve

    @classmethod
    def nurbsCurveData(cls, obj, **kwargs):
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
    def trimNurbsSurface(cls, objs, **kwargs):
        """
        Creates a trim surface based on the supplied objects.
        Sadly this method only works with the legacy API methods...c'mon Autodesk!

        :type objs: list[dict]
        :key surface: lom.MObject
        :type: lom.MTrimBoundaryArray
        """

        # Build curve data array
        #
        numObjs = len(objs)
        curveDataArray = lom.MObjectArray(numObjs)

        for (index, obj) in enumerate(objs):

            curveData = cls.nurbsCurveData(obj, **kwargs)
            curveDataArray.set(curveData, index)

        # Append curves to trim array
        #
        boundaries = lom.MTrimBoundaryArray()
        boundaries.append(curveDataArray)

        # Apply trim boundary to nurbs surface
        #
        surface = kwargs.get('surface', lom.MObject.kNullObj)

        fnNurbsSurface = lom.MFnNurbsSurface(surface)
        fnNurbsSurface.trimWithBoundaries(boundaries)

        return boundaries

    @classmethod
    def nurbsSurface(cls, obj, **kwargs):
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

        # Create trim surfaces
        #
        cls.trimNurbsSurface(
            obj['boundaries'],
            matrix=cls.demoteMatrix(matrix),
            surface=dagutils.demoteMObject(surface)
        )

        # Update curve precision
        #
        plug = fnNurbsSurface.findPlug('curvePrecisionShaded', True)
        plug.setFloat(obj['precision'])

        return surface

    @classmethod
    def mesh(cls, obj, **kwargs):
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
