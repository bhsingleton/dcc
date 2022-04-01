import re
import pymxs

from dcc.max.json import mxsvalueparser
from dcc.max.libs import nodeutils, attributeutils, controllerutils, modifierutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MXSObjectEncoder(mxsvalueparser.MXSValueEncoder):
    """
    Overload of MXSValueEncoder used to serialize MXS objects.
    """

    # region Dunderscores
    __slots__ = (
        'includeProperties',
        'includeSubAnims',
        'includeModifiers',
        'includeCustomAttributes',
        'includeKeys'
    )

    def __init__(self, *args, **kwargs):

        # Declare private variables
        #
        self.includeProperties = kwargs.pop('includeProperties', True)
        self.includeSubAnims = kwargs.pop('includeSubAnims', True)
        self.includeModifiers = kwargs.pop('includeModifiers', True)
        self.includeCustomAttributes = kwargs.pop('includeCustomAttributes', True)
        self.includeKeys = kwargs.pop('includeKeys', True)

        # Call parent method
        #
        super(MXSObjectEncoder, self).__init__(*args, **kwargs)
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

    def serializeProperties(self, maxObject):
        """
        Returns a serializable object for the supplied max object's properties.

        :type maxObject: pymxs.MXSWrapperBase
        :rtype: Dict[str, Any]
        """

        return dict(
            controllerutils.iterProperties(
                maxObject,
                skipAnimatable=True,
                skipComplexValues=True,
                skipDefaultValues=True
            )
        )

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

    def serializeAnimatable(self, animatable):
        """
        Returns a serializable object for the supplied max object.

        :type animatable: pymxs.MXSWrapperBase
        :rtype: dict
        """

        # Serialize reference target
        #
        obj = self.serializeReferenceTarget(animatable)
        obj['name'] = getattr(animatable, 'name', '')
        obj['expression'] = pymxs.runtime.exprForMaxObject(animatable)
        obj['properties'] = {}
        obj['subAnims'] = []

        # Check if properties should be included
        #
        if self.includeProperties:

            obj['properties'].update(self.serializeProperties(animatable))

        # Check if sub-anims should be included
        #
        if self.includeSubAnims:

            obj['subAnims'].extend(list(controllerutils.iterSubAnims(animatable, skipComplexValues=True)))

        return obj

    def serializeINode(self, node):
        """
        Returns a serializable object for the supplied max node.

        :type node: pymxs.runtime.Node
        :rtype: dict
        """

        # Serialize animatable
        #
        obj = self.serializeAnimatable(node)
        obj['handle'] = node.handle

        # Check if modifiers should be included
        #
        if self.includeModifiers:

            obj['modifiers'] = list(node.modifiers)

        # Check if custom attributes should be included
        #
        if self.includeCustomAttributes:

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

        # Serialize controller
        #
        obj = self.serializeReferenceTarget(controller)
        obj['expression'] = pymxs.runtime.exprForMaxObject(controller)
        obj['properties'] = self.serializeProperties()
        obj['subAnims'] = []
        obj['value'] = controller.value
        obj['keys'] = []

        if controllerutils.isConstraint(controller):

            numTargets = controller.getNumTargets()
            obj['targets'] = [{'name': controller.getNode(x).name, 'weight': controller.getWeight(x)} for x in range(1, numTargets + 1, 1)]

        elif controllerutils.isListController(controller):

            controllers = controller.list
            controllerCount = controllers.getCount()
            obj['active'] = controllers.getActive()
            obj['list'] = [{'name': controllers.getName(x), 'controller': controllers.getSubCtrl(x), 'weight': controllers.getSubCtrlWeight(x)} for x in range(1, controllerCount + 1, 1)]

        else:

            obj['subAnims'].extend(list(controllerutils.iterSubAnims(controller, skipComplexValues=True)))

        # Check if keys should be included
        #
        if self.includeKeys and hasattr(controller, 'keys'):

            obj['keys'].extend(list(controllerutils.iterMaxKeys(controller)))

        return obj
    # endregion


class MXSObjectDecoder(mxsvalueparser.MXSValueDecoder):
    """
    Overload of MXSValueDecoder used to deserialize MXS objects.
    """

    __slots__ = ()
    __propertyparser__ = re.compile(r'([a-zA-Z_]+)(?:\[(#?[a-zA-Z0-9]+)\])?')

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
        if superClassName in nodeutils.BASE_TYPES.keys():

            return self.deserializeINode(obj)

        elif superClassName in modifierutils.BASE_TYPES.keys():

            return self.deserializeModifier(obj)

        elif superClassName in controllerutils.BASE_TYPES.keys():

            return self.deserializeController(obj)

        else:

            return super(MXSObjectDecoder, self).default(obj)

    def traceMaxObjectExpression(self, expression):
        """
        Returns the max object associated with the given expression.

        :type expression: str
        :rtype: pymxs.MXSWrapperBase
        """

        # Split expression using delimiter
        #
        strings = expression.split('.')
        numStrings = len(strings)

        if numStrings == 0:

            raise TypeError('traceMaxObjectExpression() expects a valid expression!')

        # Iterate through delimited strings
        #
        obj = pymxs.runtime.getNodeByName(strings[0].lstrip('$'))

        for i in range(1, numStrings, 1):

            # Get property value
            #
            string, index = self.__propertyparser__.findall(strings[i])[0]
            name = pymxs.runtime.Name(string)

            if pymxs.runtime.isAnimated(obj, name):

                obj = pymxs.runtime.getSubAnim(obj, name)

            elif pymxs.runtime.isProperty(obj, name):

                obj = pymxs.runtime.getProperty(obj, name)

            else:

                raise TypeError('traceMaxObjectExpression() unable to locate property: %s' % name)

            # Get indexed property
            #
            if len(index) > 0:

                index = pymxs.runtime.execute(index)
                obj = obj[index]

        return obj

    def deserializeProperties(self, properties, maxObject=None):
        """
        Overwrites the properties on the supplied max object.

        :type properties: Dict[str, Any]
        :type maxObject: pymxs.MXSWrapperBase
        :rtype: None
        """

        # Assign properties to controller
        #
        for (key, value) in properties.items():

            pymxs.runtime.setProperty(maxObject, pymxs.runtime.Name(key), value)

    def deserializeSubAnims(self, subAnims, maxObject=None):
        """
        Overwrites the sub-anim controllers on the supplied max object.

        :type subAnims: List[dict]
        :type maxObject: pymxs.MXSWrapperBase
        :rtype: None
        """

        # Iterate through sub-anims
        #
        for obj in subAnims:

            subAnim = pymxs.runtime.getSubAnim(maxObject, obj['index'])

            if subAnim.controller != obj['controller']:

                subAnim.controller = obj['controller']

            else:

                continue

    def deserializeCustomAttributes(self, customAttributes, maxObject=None):

        pass

    def deserializeINode(self, obj):

        try:

            node = self.traceMaxObjectExpression(obj['name'])
            self.deserializeProperties(obj['properties'], maxObject=node)
            self.deserializeSubAnims(obj['subAnims'], maxObject=node)

            return node

        except TypeError:

            log.warning('Unable to locate node: %s' % obj['name'])
            return

    def deserializeModifier(self, obj):

        pass

    def deserializeController(self, obj):
        """
        Returns a deserialized controller from the supplied object.

        :type obj: dict
        :rtype: pymxs.MXSWrapperBase
        """

        # Get controller
        #
        controller = None

        try:

            controller = self.traceMaxObjectExpression(obj['expression'])

        except TypeError:

            cls = getattr(pymxs.runtime, obj['class'])
            controller = cls()

        # Assign controller value
        #
        controller.value = obj['value']

        # Deserialize controller components
        #
        self.deserializeProperties(obj['properties'], maxObject=controller)
        self.deserializeSubAnims(obj['subAnims'], maxObject=controller)
        self.deserializeMaxKeyArray(obj['keys'], controller=controller)

        # Check if controller has sub-controllers
        #
        if obj['class'] in controllerutils.LIST_TYPES.keys():

            self.deserializeControllerList(obj['list'], controller=controller)

        # Check if controller has targets
        #
        if obj['class'] in controllerutils.CONSTRAINT_TYPES.keys():

            self.deserializeConstraintTargets(obj['targets'], constraint=controller)

        return controller

    def deserializeControllerList(self, obj, controller=None):
        """
        Returns a deserialized list controller from the supplied object.

        :type obj: dict
        :type controller: pymxs.MXSWrapperBase
        :rtype: None
        """

        # Assign list controllers
        #
        available = pymxs.runtime.getSubAnim(controller, pymxs.runtime.Name('available'))
        subController = None

        for (i, item) in enumerate(obj['list']):

            # Get sub-controller
            #
            listCount = controller.list.getCount()

            if i == listCount:

                available.controller = item['controller']
                controller.setName(i, item['name'])
                controller.weight[i] = item['weight']

            else:

                subController = controller.list.getSubCtrl(i + 1)

                if subController != item['controller']:

                    pass

        # Assign list weights and set active
        #
        controller.setActive(obj['active'])

        return controller

    def deserializeConstraintTargets(self, obj, constraint=None):
        """
        Returns a deserialized constraint controller from the supplied object.

        :type obj: dict
        :type constraint: pymxs.MXSWrapperBase
        :rtype: None
        """

        # Assign target nodes
        #
        for (index, item) in enumerate(obj['targets']):

            target = self.traceMaxObjectExpression(item['name'])

            constraint.appendTarget(target)
            constraint.setWeight(index, item['weight'])

        return constraint
