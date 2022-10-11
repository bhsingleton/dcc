import json
import pymxs

from six.moves import collections_abc
from ..libs import propertyutils, wrapperutils
from ...python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MXSValueEncoder(json.JSONEncoder):
    """
    Overload of JSONEncoder used to serialize MXS values.
    """

    # region Dunderscores
    __slots__ = ()

    __value_types__ = {
        'Name': 'serializeName',
        'Time': 'serializeTime',
        'Interval': 'serializeInterval',
        'Point2': 'serializePoint2',
        'Point3': 'serializePoint3',
        'Point4': 'serializePoint4',
        'Color': 'serializeColor',
        'EulerAngles': 'serializeEulerAngles',
        'Quat': 'serializeQuat',
        'Matrix3': 'serializeMatrix3',
        'MAXKey': 'serializeMAXKey',
        'MAXAKey': 'serializeMAXKey',
        'MAXKeyArray': 'serializeArray',
        'NoteTrack': 'serializeNoteTrack',
        'MAXNoteKey': 'serializeMAXNoteKey',
        'MAXNoteKeyArray': 'serializeArray',
        'Array': 'serializeArray',
        'BitArray': 'serializeArray',
        'ObjectSet': 'serializeArray',
        'SelectionSet': 'serializeSelectionSet',
        'SelectionSetArray': 'serializeArray',
        'NodeChildrenArray': 'serializeArray',
        'MaterialLibrary': 'serializeArray',
        'Dictionary': 'serializeDictionary',
        'BitMap': 'serializeBitMap'
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

        # Check if this is a mxs wrapper
        #
        if isinstance(obj, (pymxs.MXSWrapperBase, pymxs.MXSWrapperObjectSet)):

            # Check if mxs value delegate exists
            #
            className = str(pymxs.runtime.classOf(obj))
            delegate = self.__value_types__.get(className, '')

            func = getattr(self, delegate, None)

            if callable(func):

                return func(obj)

            else:

                log.warning('Unable to serialize MXS "%s" value!' % str(pymxs.runtime.classOf(obj)))
                return None

        elif isinstance(obj, self.__builtin_types__) or obj is None:

            return obj

        else:

            return super(MXSValueEncoder, self).default(obj)

    def serializeInheritance(self, wrapper):
        """
        Returns a serializable object for the supplied reference target.

        :type wrapper: pymxs.MXSWrapperBase
        :rtype: dict
        """

        maxClass = pymxs.runtime.classOf(wrapper)
        superClasses = tuple(wrapperutils.iterBases(maxClass))

        return {'__class__': str(maxClass), '__mro__': tuple(map(str, (maxClass,) + superClasses))}

    def serializeName(self, name):
        """
        Serializes the supplied Name object into a json object.

        :type name: pymxs.runtime.Name
        :rtype: dict
        """

        obj = self.serializeInheritance(name)
        obj['args'] = [stringutils.slugify(str(name), whitespace='_', illegal='_')]
        obj['kwargs'] = {}

        return obj

    def serializeTime(self, time):
        """
        Serializes the supplied time value into a json object.

        :type time: pymxs.runtime.Time
        :rtype: int
        """

        return int(time)

    def serializeInterval(self, interval):
        """
        Serializes the supplied interval value into a json object.

        :type interval: pymxs.runtime.Interval
        :rtype: Tuple[int, int]
        """

        return interval.start, interval.end

    def serializePoint2(self, point2):
        """
        Serializes the supplied Point2 object into a json object.

        :type point2: pymxs.runtime.Point2
        :rtype: dict
        """

        obj = self.serializeInheritance(point2)
        obj['args'] = [point2.x, point2.y]
        obj['kwargs'] = {}

        return obj

    def serializePoint3(self, point3):
        """
        Serializes the supplied Point3 object into a json object.

        :type point3: pymxs.runtime.Point3
        :rtype: dict
        """

        obj = self.serializeInheritance(point3)
        obj['args'] = [point3.x, point3.y, point3.z]
        obj['kwargs'] = {}

        return obj

    def serializePoint4(self, point4):
        """
        Serializes the supplied Point4 object into a json object.

        :type point4: pymxs.runtime.Point4
        :rtype: dict
        """

        obj = self.serializeInheritance(point4)
        obj['args'] = [point4.x, point4.y, point4.z, point4.w]
        obj['kwargs'] = {}

        return obj

    def serializeColor(self, color):
        """
        Serializes the supplied Color object into a json object.

        :type color: pymxs.runtime.Color
        :rtype: dict
        """

        obj = self.serializeInheritance(color)
        obj['args'] = [color.r, color.g, color.b, color.a]
        obj['kwargs'] = {}

        return obj

    def serializeEulerAngles(self, eulerAngles):
        """
        Serializes the supplied EulerAngles object into a json object.

        :type eulerAngles: pymxs.runtime.EulerAngles
        :rtype: dict
        """

        obj = self.serializeInheritance(eulerAngles)
        obj['args'] = [eulerAngles.x, eulerAngles.y, eulerAngles.z]
        obj['kwargs'] = {}

        return obj

    def serializeQuat(self, quat):
        """
        Serializes the supplied Quat object into a json object.

        :type quat: pymxs.runtime.Quat
        :rtype: dict
        """

        obj = self.serializeInheritance(quat)
        obj['args'] = [quat.x, quat.y, quat.z, quat.w]
        obj['kwargs'] = {}

        return obj

    def serializeMatrix3(self, matrix3):
        """
        Serializes the supplied matrix3 object into a json object.

        :type matrix3: pymxs.runtime.Matrix3
        :rtype: dict
        """

        obj = self.serializeInheritance(matrix3)
        obj['args'] = [matrix3.row1, matrix3.row2, matrix3.row3, matrix3.row4]
        obj['kwargs'] = {}

        return obj

    def serializeMAXKey(self, maxKey):
        """
        Serializes the supplied MAXKey object into a json object.

        :type maxKey: pymxs.runtime.MAXKey
        :rtype: dict
        """

        obj = self.serializeInheritance(maxKey)
        obj['args'] = []
        obj['kwargs'] = {key: value for (key, value) in propertyutils.iterDynamicProperties(maxKey)}

        return obj

    def serializeMAXNoteKey(self, noteKey):
        """
        Serializes the supplied MAXKey object into a json object.
        For some reason the dynamic properties are not exposed for this class?

        :type noteKey: pymxs.runtime.MAXNoteKey
        :rtype: dict
        """

        obj = self.serializeInheritance(noteKey)
        obj['args'] = []
        obj['kwargs'] = {'time': noteKey.time, 'selected': noteKey.selected, 'value': noteKey.value}

        return obj

    def serializeNoteTrack(self, noteTrack):
        """
        Serializes the supplied NoteTrack object into a json object.

        :type noteTrack: pymxs.runtime.NoteTrack
        :rtype: dict
        """

        obj = self.serializeInheritance(noteTrack)
        obj['args'] = []
        obj['kwargs'] = {'name': noteTrack.name, 'keys': noteTrack.keys}

        return obj

    def serializeSelectionSet(self, selectionSet):
        """
        Serializes the supplied selection set into a json object.

        :type selectionSet: pymxs.runtime.SelectionSet
        :rtype: List[str]
        """

        return [selectionSet[i].name for i in range(0, selectionSet.count, 1)]

    def serializeSelectionSetArray(self, selectionSets):
        """
        Serializes the supplied selection set array into a json object.

        :type selectionSets: pymxs.runtime.SelectionSetArray
        :rtype: Dict[str, List[str]]
        """

        return {selectionSets[i].name: self.serializeSelectionSet(selectionSets[i]) for i in range(0, selectionSets.count, 1)}

    def serializeArray(self, array):
        """
        Serializes the supplied array object into a json object.

        :type array: pymxs.runtime.Array
        :rtype: List[Any]
        """

        return [array[i] for i in range(0, array.count, 1)]

    def serializeDictionary(self, dictionary):
        """
        Serializes the supplied dictionary object into a json object.

        :type dictionary: pymxs.runtime.Dictionary
        :rtype: Dict[str, Any]
        """

        return {key: dictionary[key] for key in dictionary.keys}

    def serializeBitMap(self, bitmap):
        """
        Serializes the supplied bitmap object into a json object.

        :type bitmap: pymxs.MXSWrapperBase
        :rtype: dict
        """

        obj = self.serializeInheritance(bitmap)
        obj['args'] = []
        obj['kwargs'] = {key: value for (key, value) in propertyutils.iterStaticProperties(bitmap)}

        return obj
    # endregion


class MXSValueDecoder(json.JSONDecoder):
    """
    Overload of JSONDecoder used to deserialize MXS values.
    """

    # region Dunderscores
    __slots__ = ()
    __ignore__ = ('MAXKey',)  # Values that have no constructors

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        kwargs['object_hook'] = self.default
        super(MXSValueDecoder, self).__init__(*args, **kwargs)
    # endregion

    # region Methods
    def default(self, obj):
        """
        Returns a deserialized object from the supplied dictionary.

        :type obj: dict
        :rtype: Any
        """

        # Inspect class name
        #
        className = obj.get('__class__', '')
        superClasses = obj.get('__mro__', [])

        if (hasattr(pymxs.runtime, className) and 'Value' in superClasses) and className not in MXSValueDecoder.__ignore__:

            return self.deserializeValue(obj)

        else:

            return obj

    def deserializeValue(self, obj):
        """
        Returns a deserialized mxs value from the supplied object.

        :type obj: dict
        :rtype: pymxs.MXSWrapperBase
        """

        # Get class name from object
        #
        name = obj.get('__class__', '')

        if stringutils.isNullOrEmpty(name):

            raise TypeError('deserializeValue() expects a compatible object!')

        # Get associated class
        #
        cls = getattr(pymxs.runtime, name, None)

        if callable(cls):

            return cls(*obj['args'], **obj['kwargs'])

        else:

            raise TypeError('deserializeValue() expects a valid class (%s given)!' % name)

    def deserializeMaxKeyArray(self, maxKeyArray, controller=None):
        """
        Overwrites the keys on the supplied controller.

        :type maxKeyArray: List[dict]
        :type controller: pymxs.MXSWrapperBase
        :rtype: None
        """

        # Iterate through array
        #
        maxKey = None

        for (i, obj) in enumerate(maxKeyArray):

            # Retrieve indexed max key
            #
            numKeys = pymxs.runtime.numKeys(controller)

            if i == numKeys:

                maxKey = pymxs.runtime.addNewKey(controller, obj['kwargs']['time'])

            else:

                maxKey = pymxs.runtiume.getKey(controller, i + 1)

            # Assign max key properties
            #
            for (key, value) in obj['kwargs'].items():

                pymxs.runtime.setProperty(maxKey, pymxs.runtime.Name(key), value)

        # Resort keys to prevent any index errors
        #
        pymxs.runtime.sortKeys(controller)
    # endregion
