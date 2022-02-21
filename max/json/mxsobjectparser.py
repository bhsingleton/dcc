import pymxs

from dcc.max.json import mxsvalueparser
from dcc.max.libs import controllerutils, modifierutils, attributeutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MXSObjectEncoder(mxsvalueparser.MXSValueEncoder):
    """
    Overload of MXSValueEncoder used to serialize MXS objects.
    """

    __slots__ = ()

    def default(self, obj):
        """
        Returns a serializable object for the supplied value.

        :type obj: Any
        :rtype: Any
        """

        # Check if this is a mxs wrapper
        #
        if isinstance(obj, pymxs.MXSWrapperBase):

            # Evaluate mxs object type
            #
            if pymxs.runtime.isValidNode(obj):

                return self.serializeNode(obj)

            elif controllerutils.isValidController(obj):

                return self.serializeController(obj)

            elif modifierutils.isValidModifier(obj):

                return self.serializeAnimatableObject(obj)

            else:

                return super(MXSObjectEncoder, self).default(obj)

        else:

            return super(MXSObjectEncoder, self).default(obj)

    def serializeMaxObject(self, maxObject):
        """
        Returns a serializable object for the supplied max object.

        :type maxObject: pymxs.MXSWrapperBase
        :rtype: dict
        """

        return {
            'class': str(pymxs.runtime.classOf(maxObject)),
            'superClass': str(pymxs.runtime.superClassOf(maxObject)),
            'properties': {key: value for (key, value) in controllerutils.iterProperties(maxObject, skipAnimatable=True, skipComplexValues=True)}
        }

    def serializeAnimatableObject(self, maxObject):
        """
        Returns a serializable object for the supplied animatable max object.

        :type maxObject: pymxs.MXSWrapperBase
        :rtype: dict
        """

        obj = self.serializeMaxObject(maxObject)
        obj['subAnims'] = [self.serializeSubAnim(x) for x in controllerutils.iterSubAnims(maxObject, skipComplexValues=True)]

        return obj

    def serializeNode(self, node):
        """
        Returns a serializable object for the supplied max node.

        :type node: pymxs.runtime.Node
        :rtype: dict
        """

        obj = self.serializeAnimatableObject(node)
        obj['name'] = node.name
        obj['handle'] = node.handle
        obj['modifiers'] = [self.serializeAnimatableObject(x) for x in node.modifiers]
        obj['customAttributes'] = [self.serializeAnimatableObject(x) for x in attributeutils.iterDefinitions(node)]

        return obj

    def serializeController(self, controller):
        """
        Returns a serializable object for the supplied max controller.

        :type controller: pymxs.MXSWrapperBase
        :rtype: dict
        """

        if controllerutils.isValidController(controller):

            obj = self.serializeAnimatableObject(controller)
            obj['keys'] = list(controllerutils.iterMaxKeys(controller))

            return obj

        else:

            return None

    def serializeSubAnim(self, subAnim):
        """
        Returns a serializable object for the supplied max subanim.

        :type subAnim: pymxs.runtime.SubAnim
        :rtype: dict
        """

        obj = self.serializeMaxObject(subAnim)
        obj['name'] = subAnim.name.replace(' ', '_')
        obj['index'] = subAnim.index
        obj['value'] = subAnim.value
        obj['controller'] = self.serializeController(subAnim.controller)

        return obj


class MXSObjectDecoder(mxsvalueparser.MXSValueDecoder):
    """
    Overload of MXSValueDecoder used to deserialize MXS objects.
    """

    __slots__ = ()
    __dummies__ = ['position_ListDummyEntry', 'rotation_ListDummyEntry', 'scale_ListDummyEntry']

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

        if hasattr(pymxs.runtime, className):

            # Check if this is a dummy controller
            #
            if className in MXSObjectDecoder.__dummies__:

                return obj

            # Delegate controller type to correct method
            #
            if className in controllerutils.LIST_TYPES.keys():

                return self.deserializeListController(obj)

            elif superClassName in controllerutils.BASE_TYPES.keys():

                return self.deserializeController(obj)

            else:

                return super(MXSObjectDecoder, self).default(obj)

        else:

            return super(MXSObjectDecoder, self).default(obj)

    def deserializeListController(self, obj):
        """
        Returns a deserialized list controller from the supplied object.
        List controllers have too many caveats to be allowed to pass through deserializeController().

        :type obj: dict
        :rtype: pymxs.MXSWrapperBase
        """

        # Create new controller
        #
        cls = getattr(pymxs.runtime, obj['class'])
        controller = cls()

        # Assign sub-anim controllers
        #
        available = [x for x in obj['subAnims'] if x['name'] != 'Available']

        for subAnim in available:

            pymxs.runtime.setPropertyController(controller, 'Available', subAnim['controller'])
            controller.setName(subAnim['index'], subAnim['name'])

        # Assign properties to controller
        #
        for (key, value) in obj['properties'].items():

            pymxs.runtime.setProperty(controller, pymxs.runtime.Name(key), value)

        return controller

    def deserializeController(self, obj):
        """
        Returns a deserialized controller from the supplied object.

        :type obj: dict
        :rtype: pymxs.MXSWrapperBase
        """

        # Create new controller
        #
        cls = getattr(pymxs.runtime, obj['class'])
        controller = cls()
        print('%s at %s' % (controller, hex(id(controller))))

        # Assign properties to controller
        #
        for (key, value) in obj['properties'].items():

            pymxs.runtime.setProperty(controller, pymxs.runtime.Name(key), value)

        # Assign sub-anim controllers
        #
        for subAnim in obj['subAnims']:

            print('Assigning %s.%s = %s' % (controller, subAnim['name'], subAnim['controller']))
            pymxs.runtime.setPropertyController(controller, subAnim['name'], subAnim['controller'])

        # Assign max keys
        #
        for (index, keyframe) in enumerate(obj['keys']):

            pymxs.runtime.addNewKey(controller, keyframe['kwargs']['time'])

            for (key, value) in keyframe['kwargs'].items():

                pymxs.runtime.setProperty(controller.keys[index], pymxs.runtime.Name(key), value)

        return controller
