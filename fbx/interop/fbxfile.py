import os
import fbx
import FbxCommon

from collections import deque

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxFile(object):
    """
    Base class used to interface with fbx files.
    """

    # region Dunderscores
    __slots__ = ('_filePath', '_fbxManager', '_fbxScene', '_fbxNodes')

    def __init__(self, filePath, **kwargs):
        """
        Private method called after a new instance has been created.

        :type filePath: str
        :rtype: None
        """

        # Call parent method
        #
        super(FbxFile, self).__init__()

        # Check if file path is valid
        #
        if not os.path.isfile(filePath) or not os.path.exists(filePath):

            raise TypeError('__init__() expects a valid file (%s given)!' % filePath)

        # Check if this file contains the fbx extension
        #
        name, extension = os.path.splitext(filePath)

        if extension.lower() != '.fbx':

            raise TypeError('__init__() expects a .fbx extension (%s given)!' % extension)

        # Declare class variables
        #
        self._filePath = filePath
        self._fbxManager, self._fbxScene = FbxCommon.InitializeSdkObjects()
        self._fbxNodes = {}

        # Load fbx scene file
        #
        FbxCommon.LoadScene(self._fbxManager, self._fbxScene, self._filePath)

    def __del__(self):
        """
        Private method called before this instance is sent to the garbage collector.

        :rtype: None
        """

        self._fbxManager.Destroy()
    # endregion

    # region Properties
    @property
    def filePath(self):
        """
        Getter method used to retrieve the file path associated with this fbx.
        :rtype: unicode
        """

        return self._filePath

    @property
    def fbxManager(self):
        """
        Getter method that returns the fbx manager.

        :rtype: fbx.FbxManager
        """

        return self._fbxManager

    @property
    def fbxScene(self):
        """
        Getter method that returns the fbx scene object.

        :rtype: fbx.FbxScene
        """

        return self._fbxScene
    # endregion

    # region Methods
    def rootNode(self):
        """
        Returns the fbx scene file root.

        :rtype: fbx.FbxNode
        """

        return self._fbxScene.GetRootNode()

    def getNativeWriterFormats(self):
        """
        Method used to collect all the native file formats available for use:
        [0] FBX binary (*.fbx)
        [1] FBX ascii (*.fbx)
        [2] FBX encrypted (*.fbx)
        [3] FBX 6.0 binary (*.fbx)
        [4] FBX 6.0 ascii (*.fbx)
        [5] FBX 6.0 encrypted (*.fbx)
        [6] AutoCAD DXF (*.dxf)
        [7] Alias OBJ (*.obj)
        [8] Collada DAE (*.dae)
        [9] Biovision BVH (*.bvh)
        [10] Motion Analysis HTR (*.htr)
        [11] Motion Analysis TRC (*.trc)
        [12] Acclaim ASF (*.asf)
        [13] Acclaim AMC (*.amc)
        [14] Vicon C3D (*.c3d)
        [15] Adaptive Optics AOA (*.aoa)
        [16] Superfluo MCD (*.mcd)

        :rtype: List[str]
        """

        # Collect native writer formats
        #
        pluginRegistry = self._fbxManager.GetIOPluginRegistry()
        count = pluginRegistry.GetWriterFormatCount()

        return [pluginRegistry.GetNativeWriterFormat(x) for x in range(count)]

    def iterObjects(self):
        """
        Returns a generator that yields all fbx objects.

        :rtype: iter
        """

        # Iterate through source objects
        #
        objectCount = self._fbxScene.RootProperty.GetSrcObjectCount()

        for i in range(objectCount):

            yield self._fbxScene.RootProperty.GetSrcObject(i)

    @staticmethod
    def iterChildren(fbxNode):
        """
        Returns a generator that yields the children belonging to the supplied fbx node.

        :type fbxNode: fbx.FbxNode
        :rtype: iter
        """

        # Iterate through children
        #
        childCount = fbxNode.GetChildCount()

        for i in range(childCount):

            yield fbxNode.GetChild(i)

    def walk(self, *args, **kwargs):
        """
        Returns a generator that yields all the descendants from the root node.
        A list of node names can be supplied in order to limit the search depth.

        :key exclusions: List[str]
        :rtype: iter
        """

        # Check if an fbx node was supplied
        #
        fbxNode = None
        numArgs = len(args)

        if numArgs == 0:

            fbxNode = self.rootNode()

        elif numArgs == 1:

            fbxNode = args[0]

        else:

            raise TypeError('walk() takes at most 1 argument (%s given)!' % numArgs)

        # Consume items in queue
        # Make sure not to include itself in the queue
        #
        exclusions = kwargs.get('exclusions', [])
        queue = deque([fbxNode for fbxNode in self.iterChildren(fbxNode) if fbxNode.GetName() not in exclusions])

        while len(queue) > 0:

            # Pop fbx node from queue
            #
            fbxNode = queue.popleft()
            yield fbxNode

            # Extend queue using popped item
            #
            queue.extend([fbxNode for fbxNode in self.iterChildren(fbxNode) if fbxNode.GetName() not in exclusions])

    def getNodeByName(self, name):
        """
        Returns the fbx node associated with the given name.

        :type name: str
        :rtype: fbx.FbxNode
        """

        # Check if node has already been found
        #
        fbxNode = self._fbxNodes.get(name, None)

        if fbxNode is not None:

            return fbxNode

        # Collect all nodes with name
        #
        fbxNodes = [x for x in self.walk() if x.GetName() == name]
        numFbxNodes = len(fbxNodes)

        if numFbxNodes == 0:

            self._fbxNodes[name] = None

        elif numFbxNodes == 1:

            self._fbxNodes[name] = fbxNodes[0]

        else:

            raise TypeError('Multiple nodes found with the name: "%s"' % name)

        return self._fbxNodes[name]

    def getNodesByType(self, typeName):
        """
        Returns a list of nodes derived from the given type name.

        :type typeName: str
        :rtype: List[fbx.FbxNode]
        """

        return [x for x in self.walk() if x.GetTypeName() == typeName]

    def getObjectsByType(self, typeName):
        """
        Returns a list of objects derived from the given type name.

        :type typeName: str
        :rtype: List[fbx.FbxObject]
        """

        return [x for x in self.iterObjects() if x.GetTypeName() == typeName]

    def nodeExists(self, name):
        """
        Evaluates if a node with given name exists.

        :type name: str
        :rtype: bool
        """

        return self.getNodeByName(name) is not None

    def resetTransform(self, node):
        """
        Resets the local transform components on the supplied node.

        :type node: fbx.FbxNode
        :rtype: None
        """

        node.LclTranslation.Set(fbx.FbxDouble3(0.0, 0.0, 0.0))
        node.RotationPivot.Set(fbx.FbxDouble3(0.0, 0.0, 0.0))
        node.PreRotation.Set(fbx.FbxDouble3(0.0, 0.0, 0.0))
        node.LclRotation.Set(fbx.FbxDouble3(0.0, 0.0, 0.0))
        node.PostRotation.Set(fbx.FbxDouble3(0.0, 0.0, 0.0))
        node.LclScaling.Set(fbx.FbxDouble3(1.0, 1.0, 1.0))

    def clearTransformKeys(self, node):
        """
        Removes all keyframes from the supplied node.

        :type node: fbx.FbxNode
        :rtype: None
        """

        # Iterate through transform properties
        #
        animStack = self.fbxScene.GetCurrentAnimationStack()  # type: fbx.FbxAnimStack

        for component in (node.LclTranslation, node.LclRotation, node.LclScaling):

            # Get anim-curve node
            #
            animCurveNode = component.GetCurveNode(animStack, False)

            if animCurveNode is None:

                continue

            # Reset anim-curve channels
            #
            animCurveNode.ResetChannels()
            animCurveNode.Destroy(True)

    def removeDisplayLayers(self):
        """
        Removes all display layers from the fbx file.

        :rtype: None
        """

        # Collect and destroy layers
        #
        layers = self.getObjectsByType('DisplayLayer')

        for layer in layers:

            log.info('Destroying "%s" layer.' % layer.GetName())
            layer.Destroy()

    def removeContainers(self):
        """
        Removes all the containers from the fbx file.

        :rtype: None
        """

        # Collect and destroy containers
        #
        containers = self.getObjectsByType('Container')

        for container in containers:

            log.info('Destroying "%s" container.' % container.GetName())
            container.Destroy()

    def moveToOrigin(self):
        """
        Moves all root nodes to the origin.

        :rtype: None
        """

        # Iterate through root nodes
        #
        for child in self.iterChildren(self.rootNode()):

            self.clearTransformKeys(child)
            self.resetTransform(child)

    @staticmethod
    def stripDagPath(name):
        """
        Removes all pipe delimiters from the supplied name.

        :type name: str
        :rtype: str
        """

        return name.split('|')[-1]

    @staticmethod
    def stripNamespace(name):
        """
        Removes all colon delimiters from the supplied name.

        :type name: str
        :rtype: str
        """

        return name.split(':')[-1]

    @classmethod
    def stripAll(cls, name):
        """
        Removes any unwanted delimiters from the supplied name.

        :type name: str
        :rtype: str
        """

        name = cls.stripDagPath(name)
        name = cls.stripNamespace(name)

        return name

    def removeNamespaces(self):
        """
        Removes all namespaces from the fbx file.

        :rtype: None
        """

        # Iterate through scene nodes
        #
        for fbxNode in self.walk():

            # Inspect node name
            #
            name = fbxNode.GetName()
            newName = self.stripAll(name)

            if name != newName:

                log.info('Renaming fbx node from "%s" to "%s"!' % (name, newName))
                fbxNode.SetName(newName)

    def save(self, filePath=None, asAscii=False):
        """
        Saves any changes made to the fbx scene.
        An optional file path can be supplied in case you don't want to overwrite the original file.

        :type filePath: str
        :type asAscii: bool
        :rtype: None
        """

        # Check if file path was supplied
        #
        if filePath is None:

            filePath = self._filePath

        # Save fbx file
        #
        log.info('Saving changes to: %s' % filePath)
        FbxCommon.SaveScene(self._fbxManager, self._fbxScene, filePath, pFileFormat=int(asAscii))
    # endregion
