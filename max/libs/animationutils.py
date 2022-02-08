import pymxs
import json

from datetime import date
from . import controllerutils, modifierutils, attributeutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AnimationEncoder(json.JSONEncoder):
    """
    Overload of JSONEncoder used to store animation data from a MXSWrapperBase object.
    """

    __slots__ = ()
    __builtins__ = (bool, int, float, str, list, tuple)

    def dumpNode(self, node):
        """
        Returns an object state for the supplied node.

        :type node: pymxs.runtime.Node
        :rtype: dict
        """

        # Check if node is valid
        #
        if not pymxs.runtime.isValidNode(node):

            return None

        # Dump node to dictionary
        #
        log.debug('Dumping node: %s' % node.name)

        return {
            'name': node.name,
            'type': str(pymxs.runtime.classOf(node)),
            'baseObject': [self.dumpSubAnim(x) for x in controllerutils.iterSubAnims(node.baseObject)],
            'modifiers': [self.dumpModifier(x) for x in node.modifiers],
            'controller': self.dumpController(pymxs.runtime.getTMController(node)),
            'customAttributes': [self.dumpCustomAttribute(x) for x in attributeutils.iterDefinitions(node)]
        }

    def dumpController(self, controller):
        """
        Returns an object state for the supplied controller.

        :type controller: pymxs.runtime.MXSWrapperBase
        :rtype: dict
        """

        # Check if controller is valid
        #
        if not controllerutils.isValidController(controller):

            return None

        # Dump controller to dictionary
        #
        log.debug('Dumping controller: %s' % controller)

        return {
            'type': str(pymxs.runtime.classOf(controller)),
            'value': self.dumpValue(controller.value),
            'subAnims': [self.dumpSubAnim(x) for x in controllerutils.iterSubAnims(controller)],
            'keys': [self.dumpMaxKey(x) for x in controllerutils.iterMaxKeys(controller)]
        }

    def dumpModifier(self, modifier):
        """
        Returns an object state for the supplied modifier.

        :type modifier: pymxs.runtime.MXSWrapperBase
        :rtype: dict
        """

        # Check if modifier is valid
        #
        if not modifierutils.isValidModifier(modifier):

            return None

        # Dump modifier to dictionary
        #
        log.debug('Dumping modifier: %s' % modifier)

        return {
            'name': modifier.name,
            'type': str(pymxs.runtime.classOf(modifier)),
            'subAnims': [self.dumpSubAnim(x) for x in controllerutils.iterSubAnims(modifier)],
            'customAttributes': [self.dumpCustomAttribute(x) for x in attributeutils.iterDefinitions(modifier)]
        }

    def dumpCustomAttribute(self, definition):
        """
        Returns an object state for the supplied attribute defition.

        :type definition: pymxs.runtime.AttributeDef
        :rtype: dict
        """

        return {
            'name': definition.name,
            'type': str(pymxs.runtime.classOf(definition)),
            'subAnims': [self.dumpSubAnim(x) for x in controllerutils.iterSubAnims(definition)]
        }

    def dumpSubAnim(self, subAnim):
        """
        Returns an object state for the supplied sub anim.

        :type subAnim: pymxs.runtime.SubAnim
        :rtype: dict
        """

        return {
            'name': subAnim.name,
            'type': str(pymxs.runtime.classOf(subAnim)),
            'index': subAnim.index,
            'value': self.dumpValue(subAnim.value),
            'controller': self.dumpController(subAnim.controller)
        }

    def dumpMaxKey(self, maxKey):
        """
        Returns an object state for the supplied keyframe.

        :type maxKey: pymxs.runtime.MAXKey
        :rtype: dict
        """

        return {
            'type': str(pymxs.runtime.classOf(maxKey)),
            'time': str(maxKey.time),
            'value': self.dumpValue(maxKey.value),
            'inTangent': self.dumpValue(maxKey.inTangent),
            'inTangentType': '#{name}'.format(name=str(maxKey.inTangentType)),
            'inTangentLength': self.dumpValue(maxKey.inTangentLength),
            'outTangent': self.dumpValue(maxKey.outTangent),
            'outTangentType': '#{name}'.format(name=str(maxKey.outTangentType)),
            'outTangentLength': self.dumpValue(maxKey.outTangentLength),
            'freeHandle': maxKey.freeHandle,
            'x_locked': maxKey.x_locked,
            'y_locked': maxKey.y_locked,
            'z_locked': maxKey.z_locked,
            'constantVelocity': maxKey.constantVelocity
        }

    def dumpValue(self, value):
        """
        Returns a json compatible object from the supplied value.

        :type value: Any
        :rtype: Any
        """

        if isinstance(value, pymxs.MXSWrapperBase):

            return str(value)

        elif isinstance(value, self.__builtins__):

            return value

        else:

            raise TypeError('dumpValue() expects a MXSWrapperBase (%s given)!' % type(value).__name__)

    def default(self, obj):
        """
        Returns a json compatible object for the supplied object.

        :type obj: Any
        :rtype: Any
        """

        # Check if this is a maxscript wrapper
        #
        if isinstance(obj, pymxs.MXSWrapperBase):

            # Evaluate wrapper type
            #
            if pymxs.runtime.isValidNode(obj):

                return self.dumpNode(obj)

            elif controllerutils.isValidController(obj):

                return self.dumpController(obj)

            elif modifierutils.isValidModifier(obj):

                return self.dumpModifier(obj)

            else:

                raise TypeError('Unable to encode maxscript object: %s' % obj)

        else:

            return super(AnimationEncoder, self).default(obj)


def saveAnimation(filePath, nodes):
    """
    Exports all of the animation from the supplied nodes to the specified path.

    :type filePath: str
    :type nodes: list[pymxs.runtime.Node]
    :rtype: None
    """

    today = date.today()

    document = {
        'filename': pymxs.runtime.maxFilename,
        'date': today.strftime('%m/%d/%Y'),
        'time': today.strftime('%H:%M:%S'),
        'frameRate': pymxs.runtime.frameRate,
        'ticksPerFrame': pymxs.runtime.ticksPerFrame,
        'nodes': nodes
    }

    with open(filePath, 'wt') as jsonFile:

        log.info('Saving animation to: %s' % filePath)
        json.dump(document, jsonFile, indent=4, cls=AnimationEncoder)
