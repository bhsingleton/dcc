import os
import json

from maya import cmds as mc
from maya import OpenMaya as legacy
from maya.api import OpenMaya as om
from itertools import chain

from . import dagutils, plugutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


COLOUR_RGB = {0: [1.0, 1.0, 0.0], 1: [0.0, 0.0, 1.0], 2: [1.0, 0.0, 0.0], 3: [1.0, 1.0, 0.0]}
COLOR_INDEX = {0: 17, 1: 6, 2: 13, 3: 17}


class ShapeEncoder(json.JSONEncoder):
    """
    Overload of JSONEncoder used to create shape templates from shape nodes.
    """

    __slots__ = ()

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

            return super(ShapeEncoder, self).default(obj)

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

        :type obj: legacy.MObject
        :rtype: list[dict]
        """

        # Check number of regions
        # If zero then this surface has no trimmed surfaces
        #
        fnNurbsSurface = legacy.MFnNurbsSurface(obj)
        numRegions = fnNurbsSurface.numRegions()

        if numRegions == 0:

            return []

        # Iterate through regions
        #
        fnNurbsCurve = legacy.MFnNurbsCurve()
        items = [None] * numRegions

        for region in range(numRegions):

            # Get trim boundary from region
            #
            boundary = legacy.MTrimBoundaryArray()
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


class ShapeDecoder(json.JSONDecoder):
    """
    Overload of JSONDecoder used to apply shape templates to transform nodes.
    """

    __slots__ = ('_parent', '_scale')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :keyword parent: om.MObject
        :keyword scale: float
        :rtype: None
        """

        # Declare private variables
        #
        self._parent = kwargs.pop('parent')
        self._scale = kwargs.pop('scale')

        # Override object hook
        #
        kwargs['object_hook'] = self.default

        # Call parent method
        #
        super(ShapeDecoder, self).__init__(*args, **kwargs)

    def default(self, obj):
        """
        Object hook for this decoder.

        :type obj: dict
        :rtype: om.MObject
        """

        # Inspect type name
        # We don't want to process any nurbs trim surfaces
        #
        typeName = obj['typeName']

        if hasattr(self, typeName):

            func = getattr(self, typeName)
            return func(obj, scale=self._scale, parent=self._parent)

        else:

            return obj

    @classmethod
    def nurbsCurve(cls, obj, scale=1.0, parent=om.MObject.kNullObj):
        """
        Creates a nurbs curve based on the supplied dictionary.

        :type obj: dict
        :type scale: float
        :type parent: om.MObject
        :rtype: om.MObject
        """

        # Collect arguments
        #
        cvs = om.MPointArray([om.MPoint(x) * scale for x in obj['controlPoints']])
        knots = om.MDoubleArray(obj['knots'])
        degree = obj['degree']
        form = obj['form']

        # Create nurbs curve using function set
        #
        fnCurve = om.MFnNurbsCurve()
        curve = fnCurve.create(cvs, knots, degree, form, False, True, parent)

        # Update line width
        #
        plug = fnCurve.findPlug('lineWidth', False)
        plug.setFloat(obj['lineWidth'])

        return curve

    @classmethod
    def nurbsCurveData(cls, obj, scale=1.0):
        """
        Creates a legacy nurbs curve data object from the.

        :type obj: dict
        :type scale: float
        :rtype: legacy.MObject
        """

        # Create new data object
        #
        fnNurbsCurveData = legacy.MFnNurbsCurveData()
        curveData = fnNurbsCurveData.create()

        # Collect control points
        #
        numControlPoints = len(obj['controlPoints'])
        controlPoints = legacy.MPointArray(numControlPoints)

        for (index, controlPoint) in enumerate(obj['controlPoints']):

            point = legacy.MPoint(controlPoint[0] * scale, controlPoint[1] * scale, controlPoint[2] * scale)
            controlPoints.set(point, index)

        # Collect knots
        #
        numKnots = len(obj['knots'])
        knots = legacy.MDoubleArray(numKnots)

        for (index, knot) in enumerate(obj['knots']):

            knots.set(knot, index)

        # Get curve parameters
        #
        degree = obj['degree']
        form = obj['form']

        fnNurbsCurve = legacy.MFnNurbsCurve()
        fnNurbsCurve.create(controlPoints, knots, degree, form, False, True, curveData)

        return curveData

    @classmethod
    def trimNurbsSurface(cls, objs, surface=legacy.MObject.kNullObj):
        """
        Creates a trim surface based on the supplied objects.
        Sadly this method on works with the legacy API methods...c'mon Autodesk!

        :type objs: list[dict]
        :type surface: legacy.MObject
        :type: legacy.MTrimBoundaryArray
        """

        # Build curve data array
        #
        numObjs = len(objs)
        curveDataArray = legacy.MObjectArray(numObjs)

        for (index, obj) in enumerate(objs):

            curveData = cls.nurbsCurveData(obj)
            curveDataArray.set(curveData, index)

        # Append curves to trim array
        #
        boundaries = legacy.MTrimBoundaryArray()
        boundaries.append(curveDataArray)

        # Apply trim boundary to nurbs surface
        #
        fnNurbsSurface = legacy.MFnNurbsSurface(surface)
        fnNurbsSurface.trimWithBoundaries(boundaries)

        return boundaries

    @classmethod
    def nurbsSurface(cls, obj, scale=1.0, parent=om.MObject.kNullObj):
        """
        Creates a nurbs surface based on the supplied object.

        :type obj: dict
        :type scale: float
        :type parent: om.MObject
        :rtype: om.MObject
        """

        # Collect arguments
        #
        cvs = om.MPointArray([om.MPoint(x[0] * scale, x[1] * scale, x[2] * scale) for x in obj['controlPoints']])
        uKnots = om.MDoubleArray(obj['uKnots'])
        vKnots = om.MDoubleArray(obj['vKnots'])
        uDegree = obj['uDegree']
        vDegree = obj['vDegree']
        uForm = obj['uForm']
        vForm = obj['vForm']

        # Create nurbs surface from function set
        #
        fnNurbsSurface = om.MFnNurbsSurface()
        surface = fnNurbsSurface.create(cvs, uKnots, vKnots, uDegree, vDegree, uForm, vForm, True, parent)

        # Create trim surfaces
        # This can only be done with the legacy API!!!
        #
        cls.trimNurbsSurface(obj['boundaries'], surface=dagutils.demoteMObject(surface))

        # Update curve precision
        #
        plug = fnNurbsSurface.findPlug('curvePrecisionShaded', True)
        plug.setFloat(obj['precision'])

        return surface

    @classmethod
    def mesh(cls, obj, scale=1.0, parent=om.MObject.kNullObj):
        """
        Creates a mesh based on the supplied dictionary.

        :type obj: dict
        :type scale: float
        :type parent: om.MObject
        :rtype: om.MObject
        """

        # Collect arguments
        #
        vertices = om.MPointArray([om.MPoint(x) * scale for x in obj['controlPoints']])
        polygonCounts = obj['polygonCounts']
        polygonConnects = obj['polygonConnects']

        # Create mesh from function set
        #
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


def applyColorIndex(shape, colorIndex):
    """
    Applies the color index to the supplied shape node.

    :type shape: Union[om.MObject, om.MDagPath]
    :type colorIndex: int
    :rtype: None
    """

    # Initialize function set
    #
    fnDagNode = om.MFnDagNode(shape)
    fullPathName = fnDagNode.fullPathName()

    # Enable color overrides
    #
    mc.setAttr('%s.overrideEnabled' % fullPathName, True)
    mc.setAttr('%s.overrideRGBColors' % fullPathName, True)
    mc.setAttr('%s.overrideColor' % fullPathName, colorIndex)


def applyColorRGB(shape, colorRGB):
    """
    Applies the color RGB to the supplied shape node.

    :type shape: Union[om.MObject, om.MDagPath]
    :type colorRGB: list[float, float, float]
    :rtype: None
    """

    # Initialize function set
    #
    fnDagNode = om.MFnDagNode(shape)
    fullPathName = fnDagNode.fullPathName()

    # Enable color overrides
    #
    mc.setAttr('%s.overrideEnabled' % fullPathName, True)
    mc.setAttr('%s.overrideRGBColors' % fullPathName, True)

    # Set color RGB values
    #
    mc.setAttr('%s.overrideColorR' % fullPathName, colorRGB[0])
    mc.setAttr('%s.overrideColorG' % fullPathName, colorRGB[0])
    mc.setAttr('%s.overrideColorB' % fullPathName, colorRGB[0])


def applyColorSide(shape, side):
    """
    Applies the color to the supplied shape node based on the side.

    :type shape: Union[om.MObject, om.MDagPath]
    :type side: int
    :rtype: None
    """

    applyColorIndex(shape, COLOR_INDEX[side])


def applyLineWidth(shape, lineWidth):
    """
    Applies the line width to the supplied shape node.

    :type shape: om.MObject
    :type lineWidth: float
    :rtype: None
    """

    fnDagNode = om.MFnDagNode(shape)

    plug = fnDagNode.findPlug('lineWidth', False)
    plug.setFloat(lineWidth)


def colorizeShape(shape, **kwargs):
    """
    Colorizes the supplied shape node based on the supplied arguments.

    :rtype: None
    """

    # Check if a color index was supplied
    #
    colorIndex = kwargs.get('colorIndex', None)

    if colorIndex is not None:

        return applyColorIndex(shape, colorIndex)

    # Check if a color RGB was supplied
    #
    colorRGB = kwargs.get('colorRGB', None)

    if colorRGB is not None:

        return applyColorRGB(shape, colorRGB)

    # Check if a side was supplied
    #
    side = kwargs.get('side', None)

    if side is not None:

        return applyColorSide(shape, side)


def createShapeTemplate(dependNode, filePath):
    """
    Creates a shape template from the supplied dependency node.

    :type dependNode: om.MObject
    :type filePath: str
    :rtype: None
    """

    # Inspect api type
    #
    shapes = None

    if dependNode.hasFn(om.MFn.kTransform):

        shapes = list(dagutils.iterShapes(dependNode))

    elif dependNode.hasFn(om.MFn.kShape):

        shapes = [dependNode]

    else:

        raise TypeError('createShapeTemplate() expects a shape node (%s given)!' % dependNode.apiTypeStr)

    # Save json file
    #
    with open(filePath, 'w') as jsonFile:

        json.dump(shapes, jsonFile, cls=ShapeEncoder)


def applyShapeTemplate(filePath, **kwargs):
    """
    Recreates the shapes from the supplied file path.
    This name will be used to lookup the json file from the shapes directory.

    :type filePath: str
    :keyword scale: float
    :keyword parent: om.MObject
    :rtype: list[om.MObject]
    """

    # Check if file exists
    #
    if not os.path.exists(filePath):

        log.warning('Unable to locate shape template: %s' % filePath)
        return []

    # Iterate through shape nodes
    #
    parent = kwargs.get('parent', om.MObject.kNullObj)
    scale = kwargs.get('scale', 1.0)

    with open(filePath, 'r') as jsonFile:

        return json.load(jsonFile, cls=ShapeDecoder, scale=scale, parent=parent)
