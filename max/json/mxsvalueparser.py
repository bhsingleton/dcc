import json
import pymxs

from dcc.max.libs import controllerutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MXSValueEncoder(json.JSONEncoder):
    """
    Overload of JSONEncoder used to serialize mxs values.
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
        'MAXKeyArray': 'serializeArray',
        'Array': 'serializeArray',
        'ObjectSet': 'serializeArray',
        'NodeChildrenArray': 'serializeArray',
        'MaterialLibrary': 'serializeArray',
        'Dictionary': 'serializeDictionary',
        'ArrayParameter': 'serializeArray',
    }
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

            # Check if mxs value is serializable
            #
            className = str(pymxs.runtime.classOf(obj))
            delegate = self.__value_types__.get(className, '')
            func = getattr(self, delegate, None)

            if callable(func):

                return func(obj)

            else:

                log.warning('Unable to serialize MXS "%s" value!' % str(pymxs.runtime.classOf(obj)))
                return None

        else:

            return super(MXSValueEncoder, self).default(obj)

    def serializeName(self, name):
        """
        Serializes the supplied Name object into a json object.

        :type name: pymxs.runtime.Name
        :rtype: dict
        """

        return {
            'class': 'Name',
            'superClass': 'Value',
            'args': [str(name).replace(' ', '_')],
            'kwargs': {}
        }

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

        return {
            'class': 'Point2',
            'superClass': 'Value',
            'args': [point2.x, point2.y],
            'kwargs': {}
        }

    def serializePoint3(self, point3):
        """
        Serializes the supplied Point3 object into a json object.

        :type point3: pymxs.runtime.Point3
        :rtype: dict
        """

        return {
            'class': 'Point3',
            'superClass': 'Value',
            'args': [point3.x, point3.y, point3.z],
            'kwargs': {}
        }

    def serializePoint4(self, point4):
        """
        Serializes the supplied Point4 object into a json object.

        :type point4: pymxs.runtime.Point4
        :rtype: dict
        """

        return {
            'class': 'Point4',
            'superClass': 'Value',
            'args': [point4.x, point4.y, point4.z, point4.w],
            'kwargs': {}
        }

    def serializeColor(self, color):
        """
        Serializes the supplied Color object into a json object.

        :type color: pymxs.runtime.Color
        :rtype: dict
        """

        return {
            'class': 'Color',
            'superClass': 'Value',
            'args': [color.r, color.g, color.b, color.a],
            'kwargs': {}
        }

    def serializeEulerAngles(self, eulerAngles):
        """
        Serializes the supplied EulerAngles object into a json object.

        :type eulerAngles: pymxs.runtime.EulerAngles
        :rtype: dict
        """

        return {
            'class': 'EulerAngles',
            'superClass': 'Value',
            'args': [eulerAngles.x, eulerAngles.y, eulerAngles.z],
            'kwargs': {}
        }

    def serializeQuat(self, quat):
        """
        Serializes the supplied Quat object into a json object.

        :type quat: pymxs.runtime.Quat
        :rtype: dict
        """

        return {
            'class': 'Quat',
            'superClass': 'Value',
            'args': [quat.x, quat.y, quat.z, quat.w],
            'kwargs': {}
        }

    def serializeMatrix3(self, matrix3):
        """
        Serializes the supplied matrix3 object into a json object.

        :type matrix3: pymxs.runtime.matrix3
        :rtype: dict
        """

        return {
            'class': 'Matrix3',
            'superClass': 'Value',
            'args': [
                self.serializePoint3(matrix3.row1),
                self.serializePoint3(matrix3.row2),
                self.serializePoint3(matrix3.row3),
                self.serializePoint3(matrix3.row4)
            ],
            'kwargs': {}
        }

    def serializeMAXKey(self, maxKey):
        """
        Serializes the supplied MAXKey object into a json object.

        :type maxKey: pymxs.runtime.MAXKey
        :rtype: dict
        """

        return {
            'class': 'MAXKey',
            'superClass': 'Value',
            'args': [],
            'kwargs': {key: value for (key, value) in controllerutils.iterDynamicProperties(maxKey)}
        }

    def serializeArray(self, array):
        """
        Serializes the supplied array object into a json object.

        :type array: pymxs.runtime.Array
        :rtype: dict
        """

        return [array[i] for i in range(0, array.count, 1)]

    def serializeDictionary(self, dictionary):
        """
        Serializes the supplied dictionary object into a json object.

        :type dictionary: pymxs.runtime.Dictionary
        :rtype: dict
        """

        return {key: dictionary[key] for key in dictionary.keys}
    # endregion


class MXSValueDecoder(json.JSONDecoder):
    """
    Overload of JSONDecoder used to deserialize mxs values.
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
        className = obj.get('class', '')
        superClassName = obj.get('superClass', '')

        if (hasattr(pymxs.runtime, className) and superClassName == 'Value') and className not in MXSValueDecoder.__ignore__:

            return self.deserializeValue(obj)

        else:

            return obj

    def deserializeValue(self, obj):
        """
        Returns a deserialized mxs value from the supplied object.

        :type obj: dict
        :rtype: pymxs.MXSWrapperBase
        """

        cls = getattr(pymxs.runtime, obj['class'])
        return cls(*obj['args'], **obj['kwargs'])

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
