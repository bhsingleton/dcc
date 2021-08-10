import pymxs

from six import string_types

from . import fnnode
from ..abstract import afnskin
from ..decorators.commandpaneloverride import CommandPanelOverride

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnSkin(afnskin.AFnSkin, fnnode.FnNode):
    """
    Overload of AFnSkin that outlines function set behaviour for skin weighting in 3ds Max.
    This class also inherits from FnNode but be aware not all functions will be compatible.
    Because of the UI dependency in 3ds Max we have to actively make sure we're in the modify panel.
    """

    __slots__ = ('_shape',)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.
        """

        # Declare class variables
        #
        self._shape = None

        # Call parent method
        #
        super(FnSkin, self).__init__(*args, **kwargs)

    def setObject(self, obj):
        """
        Assigns an object to this function set for manipulation.

        :type obj: Union[str, int, pymxs.MXSWrapperBase]
        :rtype: None
        """

        try:

            # Locate skin modifier
            #
            obj = self.getMXSWrapper(obj)
            skinModifier = self.findSkinModifier(obj)

            super(FnSkin, self).setObject(skinModifier)

            # Store reference to shape node
            #
            shape = self.getNodeFromModifier(skinModifier)
            handle = pymxs.runtime.getHandleByAnim(shape)

            self._shape = handle

        except TypeError as exception:

            log.error(exception)
            return

    @classmethod
    def findSkinModifier(cls, obj):
        """
        Finds the skin modifier from the given object.

        :type obj: Union[str, pymxs.MXSWrapperBase]
        :rtype: pymxs.MXSWrapperBase
        """

        # Check object type
        #
        if isinstance(obj, pymxs.MXSWrapperBase):

            # Check wrapper type
            #
            if pymxs.runtime.isValidNode(obj):

                fnNode = fnnode.FnNode(obj)

                skins = fnNode.getModifiersByType(pymxs.runtime.skin)
                numSkins = len(skins)

                if numSkins == 1:

                    return skins[0]

                else:

                    raise TypeError('findSkinModifier() expects 1 skin modifier (%s given)!' % numSkins)

            elif pymxs.runtime.isValidModifier(obj):

                return obj

            else:

                raise TypeError('findSkinModifier() expects a node or modifier!')

        elif isinstance(obj, string_types):

            return cls.findSkinModifier(fnnode.FnNode.getMXSWrapper(obj))

        else:

            raise TypeError('findSkinModifier() expects a MXSWrapper (%s given)!' % type(obj).__name__)

    @classmethod
    def getNodeFromModifier(cls, modifier):
        """
        Returns the node associated with the given modifier.

        :type modifier: pymxs.MXSWrapperBase
        :rtype: pymxs.MXSWrapperBase
        """

        return pymxs.runtime.refs.dependentNodes(modifier)[0]

    def shape(self):
        """
        Returns the shape node associated with the deformer.

        :rtype: Any
        """

        return pymxs.runtime.getAnimByHandle(self._shape)

    def iterControlPoints(self, *args):
        """
        Returns a generator that yields control points.

        :rtype: iter
        """

        # Evaluate arguments
        #
        vertexIndices = args
        numVertexIndices = len(vertexIndices)

        if numVertexIndices == 0:

            vertexIndices = range(self.numControlPoints())

        # Iterate through elements
        #
        shape = self.shape()

        for vertexIndex in vertexIndices:

            point = shape.verts[vertexIndex].pos
            yield point.x, point.y, point.z

    def numControlPoints(self):
        """
        Evaluates the number of control points from the associated shape.

        :rtype: int
        """

        return pymxs.runtime.skinOps.getNumberVertices(self.object())

    @CommandPanelOverride('modify')
    def iterInfluences(self):
        """
        Returns a generator that yields all of the influence object from this deformer.

        :rtype: iter
        """

        # Iterate through bones
        #
        skinModifier = self.object()
        numBones = pymxs.runtime.skinOps.getNumberBones(skinModifier)

        for i in range(1, numBones + 1, 1):

            boneId = pymxs.runtime.skinOps.getBoneIDByListID(skinModifier, i)
            boneName = pymxs.runtime.skinOps.getBoneName(skinModifier, boneId)

            yield boneId, boneName

    @CommandPanelOverride('modify')
    def addInfluence(self, influence):
        """
        Adds an influence to this deformer.

        :type influence: pymxs.MXSWrapperBase
        :rtype: bool
        """

        pymxs.runtime.skinOps.addBone(self.object(), influence, 0)

    @CommandPanelOverride('modify')
    def removeInfluence(self, influenceId):
        """
        Removes an influence from this deformer.

        :type influenceId: int
        :rtype: bool
        """

        pymxs.runtime.skinOps.removeBone(self.object(), influenceId)

    @CommandPanelOverride('modify')
    def numInfluences(self):
        """
        Returns the number of influences being use by this deformer.

        :rtype: int
        """

        return pymxs.runtime.getNumberBones(self.object())

    def maxInfluences(self):
        """
        Getter method that returns the max number of influences for this deformer.

        :rtype: int
        """

        return self.object().bone_limit

    def findRoot(self):
        """
        Returns the skeleton root associated with this deformer.

        :rtype: pymxs.MXSWrapperBase
        """

        pass

    @CommandPanelOverride('modify')
    def iterWeights(self, *args):
        """
        Returns a generator that yields skin weights.
        If no vertex indices are supplied then all of the skin weights should be yielded.

        :rtype: iter
        """

        # Evaluate arguments
        #
        vertexIndices = args
        numVertexIndices = len(vertexIndices)

        if numVertexIndices == 0:

            vertexIndices = range(1, self.numControlPoints() + 1, 1)

        # Iterate through vertices
        #
        skinModifier = self.object()

        for vertexIndex in vertexIndices:

            numBones = pymxs.runtime.skinOps.getVertexWeightCount(skinModifier, vertexIndex)
            vertexWeights = {}

            for i in range(1, numBones + 1, 1):

                boneId = pymxs.runtime.skinOps.getVertexWeightBoneID(skinModifier, vertexIndex, i)
                boneWeight = pymxs.runtime.skinOps.getVertexWeight(skinModifier, vertexIndex, i)

                vertexWeights[boneId] = boneWeight

            yield vertexIndex, vertexWeights
