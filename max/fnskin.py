import pymxs

from six import string_types

from . import fnnode
from .decorators.commandpaneloverride import CommandPanelOverride
from ..abstract import afnskin

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

        # Locate skin modifier from object
        #
        obj = self.getMXSWrapper(obj)
        skinModifier = self.findSkinModifier(obj)

        super(FnSkin, self).setObject(skinModifier)

        # Store reference to shape node
        #
        shape = self.getNodeFromModifier(skinModifier)
        handle = pymxs.runtime.getHandleByAnim(shape)

        self._shape = handle

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

                # Collect all skin modifiers
                #
                fnNode = fnnode.FnNode(obj)

                skins = fnNode.getModifiersByType(pymxs.runtime.skin)
                numSkins = len(skins)

                if numSkins == 1:

                    return skins[0]

                else:

                    raise TypeError('findSkinModifier() expects 1 skin modifier (%s given)!' % numSkins)

            elif pymxs.runtime.classOf(obj) == pymxs.runtime.skin:

                return obj

            else:

                raise TypeError('findSkinModifier() expects a node!')

        elif isinstance(obj, string_types):

            return cls.findSkinModifier(cls.getMXSWrapper(obj))

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

    @classmethod
    def convertBitArray(cls, bitArray):
        """
        Converts the supplied bit array to a list of indices.

        :type bitArray: pymxs.MXSWrapperBase
        :rtype: list[int]
        """

        return [x + 1 for x in range(bitArray.count) if bitArray[x]]

    def shape(self):
        """
        Returns the shape node associated with the deformer.

        :rtype: Any
        """

        return pymxs.runtime.getAnimByHandle(self._shape)

    def select(self, replace=True):
        """
        Selects the node associated with this function set.

        :type replace: bool
        :rtype: None
        """

        self.setActiveSelection([self.shape()], replace=replace)

    def iterVertices(self):
        """
        Returns a generator that yields all vertex indices.

        :rtype: iter
        """

        return range(1, self.numControlPoints() + 1, 1)

    def controlPoint(self, vertexIndex):
        """
        Returns a generator that yields control points.

        :type vertexIndex: int
        :rtype: list[float, float, float]
        """

        point = pymxs.runtime.polyOp.getVert(self.shape().baseObject, vertexIndex)
        return point.x, point.y, point.z

    def numControlPoints(self):
        """
        Evaluates the number of control points from the associated shape.

        :rtype: int
        """

        return pymxs.runtime.polyOp.getNumVerts(self.shape().baseObject)

    @CommandPanelOverride('modify')
    def iterSelection(self):
        """
        Returns the selected vertex elements.
        This operation is not super efficient in max...

        :rtype: list[int]
        """

        # Iterate through vertices
        #
        skinModifier = self.object()

        for i in range(1, self.numControlPoints() + 1, 1):

            # Check if vertex is selected
            #
            if pymxs.runtime.skinOps.isVertexSelected(skinModifier, i):

                yield i

            else:

                continue

    @CommandPanelOverride('modify')
    def setSelection(self, vertices):
        """
        Updates the active selection with the supplied vertex elements.

        :type vertices: list[int]
        :rtype: None
        """

        pymxs.runtime.skinOps.selectVertices(self.object(), vertices)

    def iterSoftSelection(self):
        """
        Returns a generator that yields selected vertex and soft value pairs.

        :rtype iter
        """

        return {x: 1.0 for x in self.iterSelection()}

    def getConnectedVertices(self, *args):
        """
        Returns a list of vertices connected to the supplied vertices.
        This should not include the original arguments!

        :rtype: list[int]
        """

        # Convert connected faces back to vertices
        #
        mesh = self.shape()
        edgeIndices = self.convertBitArray(pymxs.runtime.polyOp.getEdgesUsingVert(mesh, args))

        connectedVertices = set()

        for edgeIndex in edgeIndices:

            connectedVertices.update(set(pymxs.runtime.polyOp.getEdgeVerts(mesh, edgeIndex)))

        return list(connectedVertices - set(args))

    @CommandPanelOverride('modify')
    def showColors(self):
        """
        Enables color feedback for the associated shape.

        :rtype: None
        """

        # Enter envelope mode
        #
        pymxs.runtime.subObjectLevel = 1

        # Modify display settings
        #
        skinModifier = self.object()
        skinModifier.drawVertices = True
        skinModifier.shadeWeights = False
        skinModifier.colorAllWeights = False
        skinModifier.draw_all_envelopes = False
        skinModifier.draw_all_vertices = False
        skinModifier.draw_all_gizmos = False
        skinModifier.showNoEnvelopes = True
        skinModifier.showHiddenVertices = False
        skinModifier.crossSectionsAlwaysOnTop = True
        skinModifier.envelopeAlwaysOnTop = True

    @CommandPanelOverride('modify')
    def hideColors(self):
        """
        Disable color feedback for the associated shape.

        :rtype: None
        """

        # Exit envelop mode
        #
        pymxs.runtime.subObjectLevel = 0

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

            # Get bone properties
            #
            boneId = pymxs.runtime.skinOps.getBoneIDByListID(skinModifier, i)
            boneName = pymxs.runtime.skinOps.getBoneName(skinModifier, boneId, 0)

            # Get bone from name
            #
            nodes = pymxs.runtime.getNodeByName(boneName, exact=True, all=True)
            numNodes = nodes.count

            bone = None

            if numNodes == 0:

                raise RuntimeError('iterInfluences() cannot locate bone from name: %s' % boneName)

            elif numNodes == 1:

                bone = nodes[0]

            else:

                dependencies = pymxs.runtime.dependsOn(skinModifier)
                bone = [x for x in nodes if x in dependencies][0]

            yield boneId, bone

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

        return pymxs.runtime.skinOps.getNumberBones(self.object())

    def maxInfluences(self):
        """
        Getter method that returns the max number of influences for this deformer.

        :rtype: int
        """

        return self.object().bone_limit

    @CommandPanelOverride('modify')
    def selectInfluence(self, influenceId):
        """
        Changes the color display to the specified influence id.

        :type influenceId: int
        :rtype: None
        """

        pymxs.runtime.skinOps.selectBone(self.object(), influenceId)

    @CommandPanelOverride('modify')
    def iterVertexWeights(self, *args):
        """
        Returns a generator that yields weights for the supplied vertex indices.
        If no vertex indices are supplied then all weights are yielded instead.

        :rtype: iter
        """

        # Inspect arguments
        #
        numArgs = len(args)

        if numArgs == 0:

            args = range(1, self.numControlPoints() + 1, 1)

        # Iterate through arguments
        #
        for arg in args:

            # Iterate through bones
            #
            skinModifier = self.object()
            numBones = pymxs.runtime.skinOps.getVertexWeightCount(skinModifier, arg)

            vertexWeights = {}

            for i in range(1, numBones + 1, 1):

                boneId = pymxs.runtime.skinOps.getVertexWeightBoneID(skinModifier, arg, i)
                boneWeight = pymxs.runtime.skinOps.getVertexWeight(skinModifier, arg, i)

                vertexWeights[boneId] = boneWeight

            # Yield vertex weights
            #
            yield arg, vertexWeights

    @CommandPanelOverride('modify')
    def applyVertexWeights(self, vertices):
        """
        Assigns the supplied vertex weights to this deformer.

        :type vertices: dict[int:dict[int:float]]
        :rtype: None
        """

        # Define undo chunk
        #
        with pymxs.undo(True, 'Apply Weights'):

            # Bake selected vertices before applying weights
            # This allows for undo support
            #
            skinModifier = self.object()
            pymxs.runtime.skinOps.bakeSelectedVerts(skinModifier)

            # Iterate and replace vertex weights
            #
            for (vertexIndex, vertexWeights) in vertices.items():

                pymxs.runtime.skinOps.replaceVertexWeights(
                    skinModifier,
                    vertexIndex,
                    list(vertexWeights.keys()),
                    list(vertexWeights.values())
                )

        # Force redraw
        # This prevents any zero weights being returned in the same execution thread!
        #
        pymxs.runtime.completeRedraw()
