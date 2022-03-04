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

                return self.serializeINode(obj)

            elif controllerutils.isValidController(obj):

                return self.serializeController(obj)

            elif modifierutils.isValidModifier(obj):

                return self.serializeAnimatable(obj)

            else:

                return super(MXSObjectEncoder, self).default(obj)

        else:

            return super(MXSObjectEncoder, self).default(obj)

    def serializeReferenceTarget(self, referenceTarget):
        """
        Returns a serializable object for the supplied reference target.

        :type referenceTarget: pymxs.MXSWrapperBase
        :rtype: dict
        """

        return {
            'class': str(pymxs.runtime.classOf(referenceTarget)),
            'superClass': str(pymxs.runtime.superClassOf(referenceTarget))
        }

    def serializeAnimatable(self, animatable):
        """
        Returns a serializable object for the supplied max object.

        :type animatable: pymxs.MXSWrapperBase
        :rtype: dict
        """

        obj = self.serializeReferenceTarget(animatable)
        obj['name'] = animatable.name if pymxs.runtime.isProperty(animatable, 'name') else ''
        obj['properties'] = {key: value for (key, value) in controllerutils.iterProperties(animatable, skipAnimatable=True, skipComplexValues=True, skipDefaultValues=True)}
        obj['subAnims'] = [self.serializeSubAnim(x) for x in controllerutils.iterSubAnims(animatable, skipComplexValues=True)]

        return obj

    def serializeINode(self, node):
        """
        Returns a serializable object for the supplied max node.

        :type node: pymxs.runtime.Node
        :rtype: dict
        """

        obj = self.serializeAnimatable(node)
        obj['handle'] = node.handle
        obj['modifiers'] = [self.serializeAnimatable(x) for x in node.modifiers]
        obj['customAttributes'] = [self.serializeAnimatable(x) for x in attributeutils.iterDefinitions(node)]

        return obj

    def serializeController(self, controller):
        """
        Returns a serializable object for the supplied max controller.

        :type controller: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Check if controller is valid
        #
        if not controllerutils.isValidController(controller):

            return None

        # Serialize animatable
        #
        obj = self.serializeAnimatable(controller)
        obj['keys'] = list(controllerutils.iterMaxKeys(controller))

        if controllerutils.isConstraint(controller):

            numTargets = controller.getNumTargets()
            obj['targets'] = [controller.getNode(x+1).name for x in range(numTargets)]
            obj['weights'] = [controller.getWeight(x+1) for x in range(numTargets)]

        return obj

    def serializeSubAnim(self, subAnim):
        """
        Returns a serializable object for the supplied max subanim.

        :type subAnim: pymxs.runtime.SubAnim
        :rtype: dict
        """

        obj = self.serializeReferenceTarget(subAnim)
        obj['name'] = subAnim.name.replace(' ', '_')
        obj['index'] = subAnim.index
        obj['value'] = subAnim.value
        obj['isAnimated'] = subAnim.isAnimated if pymxs.runtime.isProperty(subAnim, 'isAnimated') else False
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
