from maya.api import OpenMaya as om, OpenMayaAnim as oma
from . import mdataparser
from ..libs import dagutils, plugutils, plugmutators, transformutils, animutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MAnimEncoder(mdataparser.MDataEncoder):
    """
    Overload of `MDataEncoder` used to serialize Maya keyframe data.
    """

    __slots__ = ('skipKeys', 'skipLayers')

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

        # Check if this is a dependency node
        #
        if obj.hasFn(om.MFn.kTransform):

            return self.serializeNode(obj)

        elif obj.hasFn(om.MFn.kAnimCurve):

            return self.serializeAnimCurve(obj)

        elif obj.hasFn(om.MFn.kAnimLayer):

            return self.serializeAnimLayer(obj)

        else:

            return super(MAnimEncoder, self).serializeObject(obj)

    def serializeNode(self, node):
        """
        Serializes the supplied node into a json object.

        :type node: om.MObject
        :rtype: dict
        """

        return {
            'name': dagutils.getNodeName(node),
            'namespace': dagutils.getNodeNamespace(node),
            'uuid': dagutils.getNodeUUID(node, asString=True),
            'path': dagutils.getMDagPath(node).fullPathName(),
            'plugs': self.serializeChannelBox(node),
            'matrix': transformutils.getMatrix(node),
            'worldMatrix': transformutils.getWorldMatrix(node)
        }

    def serializeChannelBox(self, node):
        """
        Serializes the channel-box values from the supplied node.

        :type node: om.MObject
        :rtype: dict
        """

        # Iterate through channel-box plugs
        #
        data = {}

        for plug in plugutils.iterChannelBoxPlugs(node):

            # Store plug value
            #
            name = plug.partialName(useLongNames=True)
            data[name] = {'name': name, 'value': plugmutators.getValue(plug), 'source': None}

            # Check if plug is animated
            #
            if animutils.isAnimated(plug):

                data[name]['source'] = self.serializeAnimCurve(plug.source().node())

        return data

    def serializeAnimCurve(self, animCurve):
        """
        Serializes the supplied anim curve into a json object.

        :type animCurve: om.MObject
        :rtype: dict
        """

        fnAnimCurve = oma.MFnAnimCurve(animCurve)

        keys = [None] * fnAnimCurve.numKeys
        obj = {'preInfinityType': fnAnimCurve.preInfinityType, 'postInfinityType': fnAnimCurve.postInfinityType, 'keys': keys}

        for i in range(fnAnimCurve.numKeys):

            keys[i] = {
                'time': fnAnimCurve.input(i),
                'value': fnAnimCurve.value(i),
                'locked': fnAnimCurve.tangentsLocked(i),
                'inTangent': fnAnimCurve.getTangentXY(i, True),
                'inTangentType': fnAnimCurve.inTangentType(i),
                'outTangent': fnAnimCurve.getTangentXY(i, False),
                'outTangentType': fnAnimCurve.outTangentType(i)
            }

        return obj

    def serializeAnimLayer(self, animLayer):
        """
        Serializes the animation layer into a json object.

        :type animLayer: om.MObject
        :rtype: dict
        """

        # Serialize anim layer plugs
        #
        obj = {'name': dagutils.getNodeName(animLayer)}

        for plug in plugutils.iterChannelBoxPlugs(animLayer):

            name = plug.partialName(useLongNames=True)
            obj[name] = plugmutators.getValue(plug)

        # Serialize anim layer members
        #
        members = animutils.getAnimLayerMembers(animLayer)
        animCurves = animLayer.getAnimLayerCurves(animLayer)

        obj['members'] = {}

        for (member, animCurve) in zip(members, animCurves):

            name = member.partialName(includeNodeName=True, useLongNames=True)
            obj['members'][name] = self.serializeAnimCurve(animCurve)

        # Serialize anim layer children
        #
        obj['children'] = list(animutils.getAnimLayerChildren(animLayer))

        return obj
