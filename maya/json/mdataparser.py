import json

from maya.api import OpenMaya as om
from six.moves import collections_abc
from itertools import chain
from ..libs import dagutils
from ...python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def findDataFunctionSet(apiType):
    """
    Returns a function set compatible with the supplied data object.

    :type apiType: int
    :rtype: om.MFnData
    """

    classes = [subclass for subclass in om.MFnData.__subclasses__() if subclass().hasObj(apiType)]
    numClasses = len(classes)

    if numClasses == 0:

        return None

    elif numClasses == 1:

        return classes[0]

    else:

        raise TypeError('findDataFunctionSet() expects a unique api type (%s given)!' % apiType)


class MDataEncoder(json.JSONEncoder):
    """
    Overload of `JSONEncoder` used to serialize Maya data.
    """

    # region Dunderscores
    __slots__ = ()

    __value_types__ = {
        'MObject': 'serializeObject',
        'MObjectArray': 'serializeArray',
        'MDagPath': 'serializeDagPath',
        'MDagPathArray': 'serializeArray',
        'MDistance': 'serializeDistance',
        'MAngle': 'serializeAngle',
        'MTime': 'serializeTime',
        'MTimeArray': 'serializeArray',
        'MStringArray': 'serializeArray',
        'MIntArray': 'serializeArray',
        'MInt64Array': 'serializeArray',
        'MFloatArray': 'serializeArray',
        'MDoubleArray': 'serializeArray',
        'MVector': 'serializeVector',
        'MVectorArray': 'serializeArray',
        'MFloatVector': 'serializeVector',
        'MFloatVectorArray': 'serializeArray',
        'MPoint': 'serializePoint',
        'MPointArray': 'serializeArray',
        'MFloatPoint': 'serializePoint',
        'MFloatPointArray': 'serializeArray',
        'MEulerRotation': 'serializeEulerRotation',
        'MQuaternion': 'serializeQuaternion',
        'MBoundingBox': 'serializeBoundingBox',
        'MMatrix': 'serializeMatrix',
        'MFloatMatrix': 'serializeMatrix',
        'MMatrixArray': 'serializeArray',
        'MTransformationMatrix': 'serializeTransformationMatrix',
        'MColor': 'serializeColor',
        'MColorArray': 'serializeArray',
        'MUuid': 'serializeUUID'
    }

    __data_types__ = {
        om.MFn.kStringArrayData: 'serializeArrayData',
        om.MFn.kIntArrayData: 'serializeArrayData',
        om.MFn.kInt64ArrayData: 'serializeArrayData',
        om.MFn.kFloatArrayData: 'serializeArrayData',
        om.MFn.kDoubleArrayData: 'serializeArrayData',
        om.MFn.kVectorArrayData: 'serializeArrayData',
        om.MFn.kPointArrayData: 'serializeArrayData',
        om.MFn.kMatrixArrayData: 'serializeArrayData',
        om.MFn.kMatrixData: 'serializeMatrixData',
        om.MFn.kNurbsCurveData: 'serializeNurbsCurveData',
        om.MFn.kNurbsSurfaceData: 'serializeNurbsSurfaceData',
        om.MFn.kMeshData: 'serializeMeshData'
    }

    __builtin_types__ = (bool, int, float, str, collections_abc.Sequence, collections_abc.Mapping)
    # endregion

    # region Methods
    def default(self, obj):
        """
        Returns a serializable object for the supplied value.

        :type obj: Any
        :rtype: Any
        """

        # Check if this object has delegate
        #
        className = type(obj).__name__
        funcName = self.__value_types__.get(className, '')
        delegate = getattr(self, funcName, None)

        if callable(delegate):

            return delegate(obj)

        elif isinstance(obj, self.__builtin_types__) or obj is None:

            return obj

        else:

            return super(MDataEncoder, self).default(obj)

    def serializeClass(self, wrapper):
        """
        Returns a serializable object for the supplied class.

        :type wrapper: om.MObject
        :rtype: dict
        """

        cls = type(wrapper)
        return {'__class__': cls.__name__, '__module__': f'maya.api.{cls.__module__}'}  # TODO: Find a cleaner way to get the module path!

    def serializeObject(self, obj):
        """
        Serializes the supplied Maya object into a json object.

        :type obj: om.MObject
        :rtype: dict
        """

        # Check if object is valid
        #
        if obj.isNull():

            return None

        # Evaluate object type
        #
        if obj.hasFn(om.MFn.kDependencyNode):

            return self.serializeNode(obj)

        elif obj.hasFn(om.MFn.kData):

            return self.serializeData(obj)

        else:

            raise TypeError(f'serializeObject() no delegate found for "%s" type!' % obj.apiTypeStr)

    def serializeNode(self, node):
        """
        Serializes the supplied node into a json object.

        :type node: om.MObject
        :rtype: dict
        """

        obj = self.serializeClass(node)
        obj['args'] = [dagutils.getNodeName(node, includePath=True, includeNamespace=True)]
        obj['kwargs'] = {}

        return obj

    def serializeDagPath(self, dagPath):
        """
        Serializes the supplied dag path into a json object.

        :type dagPath: om.MDagPath
        :rtype: dict
        """

        obj = self.serializeClass(dagPath)
        obj['args'] = [dagPath.fullPathName()]
        obj['kwargs'] = {}

        return obj

    def serializeDistance(self, distance):
        """
        Serializes the supplied distance into a json object.

        :type distance: om.MDistance
        :rtype: dict
        """

        obj = self.serializeClass(distance)
        obj['args'] = [distance.value]
        obj['kwargs'] = {'unit': distance.unit}

        return obj

    def serializeAngle(self, angle):
        """
        Serializes the supplied angle into a json object.

        :type angle: om.MAngle
        :rtype: dict
        """

        obj = self.serializeClass(angle)
        obj['args'] = [angle.value]
        obj['kwargs'] = {'unit': angle.unit}

        return obj

    def serializeTime(self, time):
        """
        Serializes the supplied distance into a json object.

        :type time: om.MTime
        :rtype: dict
        """

        obj = self.serializeClass(time)
        obj['args'] = [time.value]
        obj['kwargs'] = {'unit': time.unit}

        return obj

    def serializeArray(self, array):
        """
        Serializes the supplied array into a json object.

        :type array: Union[om.MVectorArray, om.MPointArray, om.MMatrixArray]
        :rtype: dict
        """

        obj = self.serializeClass(array)
        obj['args'] = [self.default(obj) for obj in array]
        obj['kwargs'] = {}

        return obj

    def serializeVector(self, vector):
        """
        Serializes the supplied vector into a json object.

        :type vector: om.MVector
        :rtype: dict
        """

        obj = self.serializeClass(vector)
        obj['args'] = list(vector)
        obj['kwargs'] = {}

        return obj

    def serializePoint(self, point):
        """
        Serializes the supplied point into a json object.

        :type point: om.MPoint
        :rtype: dict
        """

        obj = self.serializeClass(point)
        obj['args'] = list(point)
        obj['kwargs'] = {}

        return obj

    def serializeEulerRotation(self, eulerRotation):
        """
        Serializes the supplied euler rotation into a json object.

        :type eulerRotation: om.MEulerRotation
        :rtype: dict
        """

        obj = self.serializeClass(eulerRotation)
        obj['args'] = list(eulerRotation)
        obj['kwargs'] = {'order': eulerRotation.order}

        return obj

    def serializeQuaternion(self, quat):
        """
        Serializes the supplied quaternion into a json object.

        :type quat: om.MQuaternion
        :rtype: dict
        """

        obj = self.serializeClass(quat)
        obj['args'] = list(quat)
        obj['kwargs'] = {}

        return obj

    def serializeBoundingBox(self, boundingBox):
        """
        Serializes the supplied bounding box into a json object.

        :type boundingBox: om.MBoundingBox
        :rtype: dict
        """

        obj = self.serializeClass(boundingBox)
        obj['args'] = [boundingBox.min, boundingBox.max]
        obj['kwargs'] = {}

        return obj

    def serializeMatrix(self, matrix):
        """
        Serializes the supplied matrix into a json object.

        :type matrix: om.MMatrix
        :rtype: dict
        """

        obj = self.serializeClass(matrix)
        obj['args'] = [
            (matrix.getElement(0, 0), matrix.getElement(0, 1), matrix.getElement(0, 2), matrix.getElement(0, 3)),
            (matrix.getElement(1, 0), matrix.getElement(1, 1), matrix.getElement(1, 2), matrix.getElement(1, 3)),
            (matrix.getElement(2, 0), matrix.getElement(2, 1), matrix.getElement(2, 2), matrix.getElement(2, 3)),
            (matrix.getElement(3, 0), matrix.getElement(3, 1), matrix.getElement(3, 2), matrix.getElement(3, 3))
        ]
        obj['kwargs'] = {}

        return obj

    def serializeTransformationMatrix(self, transform):
        """
        Serializes the supplied transformation matrix into a json object.

        :type transform: om.MTransformationMatrix
        :rtype: dict
        """

        obj = self.serializeClass(transform)
        obj['args'] = []
        obj['kwargs'] = {
            'translation': transform.translation(),
            'rotation': transform.rotation(),
            'orientation': transform.rotationOrientation(),
            'rotatePivot': transform.rotatePivot(),
            'rotatePivotTranslation': transform.rotatePivotTranslation(),
            'scalePivot': transform.scalePivot(),
            'scalePivotTranslation': transform.scalePivotTranslation(),
            'shear': transform.shear()
        }

        return obj

    def serializeColor(self, color):
        """
        Serializes the supplied color into a json object.
        TODO: Find a way to serialize the color model and data type!

        :type color: om.MColor
        :rtype: dict
        """

        obj = self.serializeClass(color)
        obj['args'] = list(color)
        obj['kwargs'] = {}

        return obj

    def serializeUUID(self, uuid):
        """
        Serializes the supplied UUID into a json object.

        :type uuid: om.MUuid
        :rtype: dict
        """

        obj = self.serializeClass(uuid)
        obj['args'] = [uuid.asString()]
        obj['kwargs'] = {}

        return obj

    def serializeData(self, data):
        """
        Serializes the supplied Maya data object into a json object.

        :type data: om.MObject
        :rtype: dict
        """

        # Check if delegate exists
        #
        apiType = data.apiType()
        funcName = self.__data_types__.get(apiType, '')
        delegate = getattr(self, funcName, None)

        if callable(delegate):

            state = delegate(data)
            state['__api_type__'] = apiType

            return state

        else:

            raise TypeError(f'serializeData() no delegate found for "%s" type!' % data.apiTypeStr)

    def serializeArrayData(self, array):
        """
        Serializes the supplied string array data into a json object.

        :type array: om.MObject
        :rtype: dict
        """

        # Serialize class
        #
        obj = self.serializeClass(array)

        # Serialize curve parameters
        #
        fnArray = findDataFunctionSet(array.apiType())
        fnArray.setObject(array)

        obj['array'] = fnArray.array()

        return obj

    def serializeMatrixData(self, matrix):
        """
        Serializes the supplied curve data into a json object.

        :type matrix: om.MObject
        :rtype: dict
        """

        # Serialize class
        #
        obj = self.serializeClass(matrix)

        # Serialize curve parameters
        #
        fnMatrixData = om.MFnMatrixData(matrix)
        isTransformation = fnMatrixData.isTransformation()

        if isTransformation:

            obj['transformation'] = fnMatrixData.transformation()

        else:

            obj['matrix'] = fnMatrixData.matrix()

        return obj

    def serializeNurbsCurveData(self, curve):
        """
        Serializes the supplied curve data into a json object.

        :type curve: om.MObject
        :rtype: dict
        """

        # Serialize class
        #
        obj = self.serializeClass(curve)

        # Serialize curve parameters
        #
        fnNurbsCurve = om.MFnNurbsCurve(curve)
        obj['controlPoints'] = fnNurbsCurve.cvPositions()
        obj['knots'] = fnNurbsCurve.knots()
        obj['degree'] = fnNurbsCurve.degree
        obj['form'] = fnNurbsCurve.form

        return obj

    def serializeNurbsSurfaceData(self, surface):
        """
        Serializes the supplied surface data into a json object.

        :type surface: om.MObject
        :rtype: dict
        """

        # Serialize class
        #
        obj = self.serializeClass(surface)

        # Serialize surface parameters
        #
        fnNurbsSurface = om.MFnNurbsSurface(surface)
        obj['controlPoints'] = fnNurbsSurface.cvPositions()
        obj['uKnots'] = fnNurbsSurface.knotsInU()
        obj['vKnots'] = fnNurbsSurface.knotsInV()
        obj['uDegree'] = fnNurbsSurface.degreeInU
        obj['vDegree'] = fnNurbsSurface.degreeInV
        obj['uForm'] = fnNurbsSurface.formInU
        obj['vForm'] = fnNurbsSurface.formInV

        return obj

    def serializeMeshData(self, mesh):
        """
        Serializes the supplied mesh data into a json object.

        :type mesh: om.MObject
        :rtype: dict
        """

        # Serialize class
        #
        obj = self.serializeClass(mesh)

        # Serialize mesh parameters
        #
        fnMesh = om.MFnMesh(mesh)
        obj['controlPoints'] = fnMesh.getPoints()
        obj['polygonCounts'] = [fnMesh.polygonVertexCount(x) for x in range(fnMesh.numPolygons)]
        obj['polygonConnects'] = [fnMesh.getPolygonVertices(x) for x in range(fnMesh.numPolygons)]
        obj['faceVertexNormals'] = [fnMesh.getFaceVertexNormals(x) for x in range(fnMesh.numPolygons)]
        obj['edgeSmoothings'] = [fnMesh.isEdgeSmooth(x) for x in range(fnMesh.numEdges)]

        return obj
    # endregion


class MDataDecoder(json.JSONDecoder):
    """
    Overload of `JSONDecoder` used to deserialize Maya data.
    """

    # region Dunderscores
    __slots__ = ()

    __value_types__ = {
        'MDagPath': 'deserializeDagPath',
        'MTransformationMatrix': 'deserializeTransformationMatrix',
    }

    __data_types__ = {
        om.MFn.kStringArrayData: 'deserializeArrayData',
        om.MFn.kIntArrayData: 'deserializeArrayData',
        om.MFn.kInt64ArrayData: 'deserializeArrayData',
        om.MFn.kFloatArrayData: 'deserializeArrayData',
        om.MFn.kDoubleArrayData: 'deserializeArrayData',
        om.MFn.kVectorArrayData: 'deserializeArrayData',
        om.MFn.kPointArrayData: 'deserializeArrayData',
        om.MFn.kMatrixArrayData: 'deserializeArrayData',
        om.MFn.kMatrixData: 'deserializeMatrixData',
        om.MFn.kNurbsCurveData: 'deserializeNurbsCurveData',
        om.MFn.kNurbsSurfaceData: 'deserializeNurbsSurfaceData',
        om.MFn.kMeshData: 'deserializeMeshData'
    }

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        kwargs['object_hook'] = self.default
        super(MDataDecoder, self).__init__(*args, **kwargs)
    # endregion

    # region Methods
    def default(self, obj):
        """
        Returns a deserialized object from the supplied dictionary.

        :type obj: dict
        :rtype: Any
        """

        # Inspect api type
        #
        apiType = obj.get('__api_type__', None)

        if apiType is not None:

            return self.deserializeObject(obj)

        else:

            return self.deserializeValue(obj)

    def deserializeValue(self, obj):
        """
        Returns a deserialized value from the supplied object.

        :type obj: dict
        :rtype: Any
        """

        # Get class name from object
        #
        className = obj.get('__class__', '')

        if stringutils.isNullOrEmpty(className):

            return obj

        # Check if class has delegate
        #
        func = self.__value_types__.get(className, None)

        if callable(func):

            return func(obj)

        # Get associated constructor
        #
        cls = getattr(om, className, None)

        if callable(cls):

            return cls(*obj['args'], **obj['kwargs'])

        else:

            raise TypeError('deserializeValue() expects a valid class (%s given)!' % className)

    def deserializeDagPath(self, obj):
        """
        Returns a deserialized dag path from the supplied object.

        :type obj: dict
        :rtype: om.MDagPath
        """

        return dagutils.getMDagPath(obj['args'][0])

    def deserializeTransformationMatrix(self, obj):
        """
        Returns a deserialized transformation matrix from the supplied object.

        :type obj: dict
        :rtype: om.MTransformationMatrix
        """

        transform = om.MTransformationMatrix()
        transform.setTranslation(obj['kwargs']['translation'])
        transform.setRotation(obj['kwargs']['rotation'])
        transform.setScale(obj['kwargs']['scale'])
        transform.setRotationOrientation(obj['kwargs']['orientation'])
        transform.setRotatePivot(obj['kwargs']['rotatePivot'])
        transform.setRotatePivotTranslation(obj['kwargs']['rotatePivotTranslation'])
        transform.setScalePivot(obj['kwargs']['scalePivot'])
        transform.setScalePivotTranslation(obj['kwargs']['scalePivotTranslation'])
        transform.setShear(obj['kwargs']['shear'])

        return transform

    def deserializeObject(self, obj):
        """
        Returns a deserialized Maya object from the supplied object.

        :type obj: dict
        :rtype: om.MObject
        """

        # Check if delegate exists
        #
        apiType = obj.get('__api_type__', -1)
        func = self.__data_types__.get(apiType, None)

        if callable(func):

            return func(obj)

        elif dagutils.isDGType(apiType):

            self.deserializeNode(obj)

        else:

            raise TypeError('deserializeObject() no delegate found for "%s" type!' % apiType)

    def deserializeNode(self, obj):
        """
        Returns a deserialized node from the supplied object.

        :type obj: dict
        :rtype: om.MObject
        """

        return dagutils.getMObject(obj['args'][0])

    def deserializeArrayData(self, obj):
        """
        Returns a deserialized array object from the supplied object.

        :type obj: dict
        :rtype: om.MObject
        """

        # Find associated function set
        #
        cls = findDataFunctionSet(obj['__api_type__'])
        fnArray = cls()

        # Create new data object and populate
        #
        array = fnArray.create()
        fnArray.set(obj['array'])

        return array

    def deserializeMatrixData(self, obj):
        """
        Returns a deserialized matrix data object from the supplied object.

        :type obj: dict
        :rtype: om.MObject
        """

        isTransformation = 'transformation' in obj.keys()

        fnMatrixData = om.MFnMatrixData()
        data = fnMatrixData.create(obj['transformation'] if isTransformation else obj['matrix'])

        return data

    def deserializeNurbsCurveData(self, obj):
        """
        Returns a deserialized nurbs curve data object from the supplied object.

        :type obj: dict
        :rtype: om.MObject
        """

        fnNurbsCurveData = om.MFnNurbsCurveData()
        data = fnNurbsCurveData.create()

        fnNurbsCurve = om.MFnNurbsCurve()
        fnNurbsCurve.create(obj['controlPoints'], obj['knots'], obj['degree'], obj['form'], False, True, parent=data)

        return data

    def deserializeNurbsSurfaceData(self, obj):
        """
        Returns a deserialized nurbs surface data object from the supplied object.

        :type obj: dict
        :rtype: om.MObject
        """

        fnNurbsCurveData = om.MFnNurbsSurfaceData()
        data = fnNurbsCurveData.create()

        fnNurbsSurface = om.MFnNurbsSurface()
        fnNurbsSurface.create(obj['controlPoints'], obj['uKnots'], obj['vKnots'], obj['uDegree'], obj['vDegree'], obj['uForm'], obj['vForm'], True, parent=data)

        return data

    def deserializeMeshData(self, obj):
        """
        Returns a deserialized mesh data object from the supplied object.
        TODO: Assign face-vertex normals!

        :type obj: dict
        :rtype: om.MObject
        """

        fnMeshData = om.MFnMeshData()
        data = fnMeshData.create()

        fnMesh = om.MFnMesh()
        fnMesh.create(obj['controlPoints'], obj['polygonCounts'], list(chain(*obj['polygonConnects'])), parent=data)
        fnMesh.setEdgeSmoothings(list(range(fnMesh.numEdges)), obj['edgeSmoothings'])

        return data
    # endregion
