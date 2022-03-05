import pymxs

from dcc.max.json import mxsvalueparser
from dcc.max.libs import controllerutils, modifierutils, attributeutils, arrayutils

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

            elif controllerutils.isValidSubAnim(obj):

                return self.serializeSubAnim(obj)

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
        obj['name'] = getattr(animatable, 'name', '')
        obj['properties'] = dict(controllerutils.iterProperties(animatable, skipAnimatable=True, skipComplexValues=True, skipDefaultValues=True))
        obj['subAnims'] = list(controllerutils.iterSubAnims(animatable, skipComplexValues=True))

        return obj

    def serializeINode(self, node):
        """
        Returns a serializable object for the supplied max node.

        :type node: pymxs.runtime.Node
        :rtype: dict
        """

        obj = self.serializeAnimatable(node)
        obj['handle'] = node.handle
        obj['modifiers'] = list(node.modifiers)
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
        obj = self.serializeReferenceTarget(controller)
        obj['properties'] = dict(controllerutils.iterProperties(controller, skipAnimatable=True, skipComplexValues=True, skipDefaultValues=True))
        obj['subAnims'] = []
        obj['value'] = controller.value
        obj['keys'] = []

        if controllerutils.isConstraint(controller):

            numTargets = controller.getNumTargets()
            obj['targets'] = [{'name': controller.getNode(x).name, 'weight': controller.getWeight(x)} for x in range(1, numTargets + 1, 1)]

        elif controllerutils.isListController(controller):

            controllers = controller.list
            controllerCount = controllers.count

            obj['active'] = controller.getActive()
            obj['list'] = [{'name': controllers.getName(x), 'controller': controllers.getSubCtrl(x)} for x in range(1, controllerCount + 1, 1)]
            obj['weight'] = [controllers.getSubCtrlWeight(x) for x in range(1, controllerCount + 1, 1)]

        elif controllerutils.isBezierController(controller):

            obj['keys'].extend(list(controllerutils.iterMaxKeys(controller)))

        else:

            obj['subAnims'].extend(list(controllerutils.iterSubAnims(controller, skipComplexValues=True)))

        return obj

    def serializeSubAnim(self, subAnim):
        """
        Returns a serializable object for the supplied max sub anim.

        :type subAnim: pymxs.runtime.SubAnim
        :rtype: dict
        """

        obj = self.serializeReferenceTarget(subAnim)
        obj['name'] = subAnim.name.replace(' ', '_')
        obj['index'] = subAnim.index
        obj['value'] = subAnim.value
        obj['isAnimated'] = getattr(subAnim, 'isAnimated', False)
        obj['controller'] = subAnim.controller

        return obj


class MXSObjectDecoder(mxsvalueparser.MXSValueDecoder):
    """
    Overload of MXSValueDecoder used to deserialize MXS objects.
    """

    __slots__ = ()

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

        if not hasattr(pymxs.runtime, className):

            return super(MXSObjectDecoder, self).default(obj)

        # Delegate controller type to correct method
        #
        if className in controllerutils.LIST_TYPES.keys():

            return self.deserializeListController(obj)

        elif className in controllerutils.CONSTRAINT_TYPES.keys():

            return self.deserializeConstraint(obj)

        elif superClassName in controllerutils.BASE_TYPES.keys():

            return self.deserializeController(obj)

        else:

            return super(MXSObjectDecoder, self).default(obj)

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

        # Assign properties to controller
        #
        for (key, value) in obj['properties'].items():

            pymxs.runtime.setProperty(controller, pymxs.runtime.Name(key), value)

        # Assign sub-anim controllers
        #
        for subAnim in obj['subAnims']:

            subAnim = pymxs.runtime.getSubAnim(controller, subAnim['name'])
            subAnim.controller = subAnim['controller']

        # Assign max keys
        #
        for (index, keyframe) in enumerate(obj['keys']):

            pymxs.runtime.addNewKey(controller, keyframe['kwargs']['time'])

            for (key, value) in keyframe['kwargs'].items():

                pymxs.runtime.setProperty(controller.keys[index], pymxs.runtime.Name(key), value)

        return controller

    def deserializeListController(self, obj):
        """
        Returns a deserialized list controller from the supplied object.

        :type obj: dict
        :rtype: pymxs.MXSWrapperBase
        """

        # Assign list controllers
        #
        controller = self.deserializeController(obj)
        available = pymxs.runtime.getSubAnim(controller, 'available')

        for (index, item) in enumerate(obj['list']):

            available.controller = item['controller']
            controller.setName(index, item['name'])

        # Assign list weights and set active
        #
        controller.weight = obj['weight']
        controller.setActive(obj['active'])

        return controller

    def deserializeConstraint(self, obj):
        """
        Returns a deserialized constraint controller from the supplied object.

        :type obj: dict
        :rtype: pymxs.MXSWrapperBase
        """

        # Assign target nodes
        #
        controller = self.deserializeController(obj)

        for (index, item) in enumerate(obj['targets']):

            target = pymxs.runtime.getNodeByName(item['name'])

            controller.appendTarget(target)
            controller.setWeight(index, item['weight'])

        return controller
