import fnmatch

from maya import cmds as mc, OpenMaya as legacy
from maya.api import OpenMaya as om, OpenMayaAnim as oma
from six import string_types
from collections import deque
from itertools import chain

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def getNodeName(dependNode):
    """
    Returns the name of the supplied node.
    This method will remove any hierarchical or namespace delimiters.

    :type dependNode: om.MObject
    :rtype: str
    """

    dependNode = getMObject(dependNode)

    if dependNode.hasFn(om.MFn.kDependencyNode):

        return stripAll(om.MFnDependencyNode(dependNode).name())

    else:

        return ''


def demoteMObject(dependNode):
    """
    Demotes the supplied MObject back into the legacy API type.
    This method only supports dependency/dag nodes!

    :type dependNode: om.MObject
    :rtype: legacy.MObject
    """

    # Check value type
    #
    if not isinstance(dependNode, om.MObject):

        raise TypeError('demoteMObject() expects the new MObject type!')

    # Get full path name from node
    #
    fullPathName = ''

    if dependNode.hasFn(om.MFn.kDagNode):

        dagPath = om.MDagPath.getAPathTo(dependNode)
        fullPathName = dagPath.fullPathName()

    elif dependNode.hasFn(om.MFn.kDependencyNode):

        fullPathName = om.MFnDependencyNode(dependNode).absoluteName()

    else:

        raise TypeError('getLegacyMObject() expects a dependency node (%s given)!' % dependNode.apiTypeStr)

    # Add name to legacy selection list
    #
    selectionList = legacy.MSelectionList()
    selectionList.add(fullPathName)

    legacyDependNode = legacy.MObject()
    selectionList.getDependNode(0, legacyDependNode)

    return legacyDependNode


def promoteMObject(dependNode):
    """
    Promotes the supplied MObject back into the new API type.
    This method only supports dependency/dag nodes!

    :type dependNode: legacy.MObject
    :rtype: om.MObject
    """

    # Check value type
    #
    if not isinstance(dependNode, legacy.MObject):

        raise TypeError('promoteMObject() expects the legacy MObject type!')

    # Get full path name from node
    #
    fullPathName = ''

    if dependNode.hasFn(legacy.MFn.kDagNode):

        dagPath = legacy.MDagPath()
        legacy.MDagPath.getAPathTo(dependNode, dagPath)

        fullPathName = dagPath.fullPathName()

    elif dependNode.hasFn(legacy.MFn.kDependencyNode):

        fullPathName = om.MFnDependencyNode(dependNode).absoluteName()

    else:

        raise TypeError('promoteLegacyMObject() expects a dependency node (%s given)!' % dependNode.apiTypeStr)

    # Add name to selection list
    #
    selectionList = om.MSelectionList()
    selectionList.add(fullPathName)

    return selectionList.getDependNode(0)


def getMObjectByName(name):
    """
    Returns an MObject from the supplied node name.
    If a plug is included in the name then a tuple will be returned instead.
    There's a better plug lookup method inside plugutils!

    :type name: str
    :rtype: om.MObject
    """

    # Check if string contains an attribute
    #
    strings = name.split('.', 1)
    numStrings = len(strings)

    if numStrings == 1:

        # Try and add node name to selection list
        # If it fails then a RuntimeError will be raised
        #
        try:

            # Append node name to selection list
            #
            selection = om.MSelectionList()
            selection.add(name)

            return selection.getDependNode(0)

        except RuntimeError as exception:

            log.debug('"%s" node does not exist!' % name)
            return om.MObject.kNullObj

    else:

        # Try and add node and attribute name to selection list
        # If it fails then a RuntimeError will be raised
        #
        try:

            # Append path name to selection list
            #
            selection = om.MSelectionList()
            selection.add(name)

            return selection.getDependNode(0), selection.getPlug(0)

        except RuntimeError as exception:

            log.debug('"%s" plug does not exist!' % name)
            return om.MObject.kNullObj, om.MPlug()


def getMObjectByMUuid(uuid):
    """
    Returns an MObject from the supplied UUID.
    If multiple nodes are found with the same UUID then a list will be returned!

    :type uuid: om.MUuid
    :rtype: Union[om.MObject, List[om.MObject]]
    """

    nodes = list(iterNodesByUuid(uuid))
    numNodes = len(nodes)

    if numNodes == 0:

        return om.MObject.kNullObj

    elif numNodes == 1:

        return nodes[0]

    else:

        return nodes


def getMObjectByMObjectHandle(handle):
    """
    Returns an MObject from the supplied MObjectHandle.

    :type handle: om.MObjectHandle
    :rtype: om.MObject
    """

    return handle.object()


def getMObjectByMDagPath(dagPath):
    """
    Returns an MObject from the supplied MDagPath.

    :type dagPath: om.MDagPath
    :rtype: om.MObject
    """

    return dagPath.node()


__getmobject__ = {
    'str': getMObjectByName,
    'unicode': getMObjectByName,  # Leaving this here for backwards compatibility
    'MUuid': getMObjectByMUuid,
    'MObjectHandle': getMObjectByMObjectHandle,
    'MDagPath': getMObjectByMDagPath
}


def getMObject(value):
    """
    Returns an MObject from the supplied value.
    This method expects the value to be derived from a dependency node in order to work!

    :type value: Union[str, om.MObject, om.MObjectHandle, om.MDagPath]
    :rtype: om.MObject
    """

    # Check for redundancy
    #
    if isinstance(value, om.MObject):

        return value

    # Check value type
    #
    typeName = type(value).__name__
    func = __getmobject__.get(typeName, None)

    if func is not None:

        return func(value)

    else:

        raise TypeError('getMObject() expects %s (%s given)!' % (tuple(__getmobject__.keys()), type(value).__name__))


def getMObjectHandle(value):
    """
    Returns an MObjectHandle from the supplied value.

    :type value: Union[str, om.MObject, om.MObjectHandle, om.MDagPath]
    :rtype: om.MObjectHandle
    """

    # Check for redundancy
    #
    if isinstance(value, om.MObjectHandle):

        return value

    else:

        return om.MObjectHandle(getMObject(value))


def getHashCode(value):
    """
    Returns a hash code from the supplied value.

    :type value: Union[str, om.MObject, om.MObjectHandle, om.MDagPath]
    :rtype: int
    """

    return getMObjectHandle(value).hashCode()


def getMDagPath(value):
    """
    Returns an MDagPath from the supplied value.
    This method expects the value to be derived from a dag node in order to work!

    :type value: Union[str, om.MObject, om.MObjectHandle, om.MDagPath]
    :rtype: om.MDagPath
    """

    # Check for redundancy
    #
    if isinstance(value, om.MDagPath):

        return value

    else:

        return om.MDagPath.getAPathTo(getMObject(value))


def getShapeDirectlyBelow(transform):
    """
    Returns the shape node directly below the supplied transform.

    :type transform: Union[om.MObject, om.MDagPath]
    :rtype: om.MDagPath
    """

    shapes = list(iterShapes(transform))
    numShapes = len(shapes)

    if numShapes == 0:

        return None

    elif numShapes == 1:

        return shapes[0]

    else:

        raise TypeError('getShapeDirectlyBelow() expects to find 1 shape (%s found)!' % numShapes)


def iterAssociatedDeformers(value, apiType=om.MFn.kGeometryFilt):
    """
    Returns a generator that yields the associated deformers from the supplied object.
    It is safe to supply either the transform, shape or deformer component.

    :type value: Union[om.MObject, om.MDagPath]
    :type apiType: int
    :rtype: iter
    """

    # Check api type
    #
    obj = getMObject(value)

    if obj.hasFn(om.MFn.kTransform):

        return iterAssociatedDeformers(getShapeDirectlyBelow(obj), apiType=apiType)

    elif obj.hasFn(om.MFn.kGeometryFilt):

        return iterAssociatedDeformers(dependents(obj, apiType=om.MFn.kShape)[0], apiType=apiType)

    elif obj.hasFn(om.MFn.kShape):

        return iterDependencies(obj, apiType, direction=om.MItDependencyGraph.kUpstream)

    else:

        log.warning('iterAssociatedDeformers() expects a shape node (%s given)!' % obj.apiTypeStr)
        return


def iterDeformersFromSelection(apiType=om.MFn.kGeometryFilt):
    """
    Returns a generator that yields deformers from the active selection.
    An optional api type can be provided to narrow down the yielded deformers.

    :type apiType: int
    :rtype: iter
    """

    # Iterate through selection
    #
    for dependNode in iterActiveSelection(apiType=om.MFn.kDagNode):

        # Iterate through deformers
        #
        for deformer in iterAssociatedDeformers(dependNode, apiType=apiType):

            yield deformer


def getAssociatedDeformers(value, apiType=om.MFn.kGeometryFilt):
    """
    Returns a list of deformers associated with the supplied shape.

    :type value: Union[om.MObject, om.MDagPath]
    :type apiType: int
    :rtype: list
    """

    return list(iterAssociatedDeformers(value, apiType=apiType))


def findDeformerByType(value, apiType):
    """
    Returns the specified deformer from the supplied shape.

    :type value: Union[om.MObject, om.MDagPath]
    :type apiType: int
    :rtype: om.MObject
    """

    deformers = getAssociatedDeformers(value, apiType=apiType)
    numDeformers = len(deformers)

    if numDeformers == 0:

        return None

    elif numDeformers == 1:

        return deformers[0]

    else:

        raise TypeError('findDeformerByType() expects 1 deformer (%s given)!' % numDeformers)


def decomposeDeformer(deformer):
    """
    Breaks down a deformer into its 3 components: transform, shape and intermediate object.
    A type error will be raised if the deformer was not setup correctly!

    :type deformer: om.MObject
    :rtype: Tuple[om.MObject, om.MObject, om.MObject]
    """

    # Locate shape nodes downstream
    #
    transform, shape, intermediateObject = None, None, None

    shapes = dependents(deformer, apiType=om.MFn.kShape)
    numShapes = len(shapes)

    if numShapes == 1:

        shape = shapes[0]

    else:

        raise TypeError('decomposeDeformer() expects 1 shape node (%s found)!' % numShapes)

    # Locate transform from shape node
    #
    transform = om.MFnDagNode(shape).parent(0)

    # Locate intermediate objects upstream
    #
    intermediateObjects = dependsOn(deformer, apiType=om.MFn.kShape)
    numIntermediateObjects = len(intermediateObjects)

    if numIntermediateObjects == 1:

        intermediateObject = intermediateObjects[0]

    else:

        raise TypeError('decomposeDeformer() expects 1 intermediate object (%s found)!' % numIntermediateObjects)

    return transform, shape, intermediateObject


def getAssociatedReferenceNode(dependNode):
    """
    Returns the reference node associated with the supplied dependency node.
    If this node is not referenced then none will be returned!

    :type dependNode: om.MObject
    :rtype: om.MObject
    """

    # Check if node is referenced
    #
    fnDependNode = om.MFnDependencyNode(dependNode)

    if not fnDependNode.isFromReferencedFile:

        return None

    # Iterate through reference nodes
    #
    fnReference = om.MFnReference()

    for reference in iterNodes(apiType=om.MFn.kReference):

        # Check if reference contains node
        #
        fnReference.setObject(reference)

        if fnReference.containsNodeExactly(dependNode):

            return reference

        else:

            continue

    return None


def getComponentFromString(value):
    """
    Returns the node and component from the supplied string.
    A type error will be raised if the string is invalid!

    :type value: str
    :rtype: Tuple[om.MDagPath, om.MObject]
    """

    # Check value type
    #
    if not isinstance(value, string_types):

        raise TypeError('getComponentFromString() expects a str (%s given)!' % type(value).__name__)

    # Check if object exists
    #
    if not mc.objExists(value):

        raise TypeError('getComponentFromString() expects a valid string object!')

    # Add value to selection list
    #
    selection = om.MSelectionList()
    selection.add(value)

    return selection.getComponent(0)


def createSelectionList(items):
    """
    Returns a selection list from the supplied objects.

    :type items: List[Any]
    :rtype: om.MSelectionList
    """

    # Iterate through items
    #
    selection = om.MSelectionList()

    for item in items:

        # Get object
        #
        dependNode = getMObject(item)

        if dependNode.isNull():

            continue

        # Check if this is a dag node
        #
        if dependNode.hasFn(om.MFn.kDagNode):

            dagPath = om.MDagPath.getAPathTo(dependNode)
            selection.add(dagPath)

        else:

            selection.add(dependNode)

    return selection


def getActiveSelection(apiType=om.MFn.kDependencyNode):
    """
    Returns the active selection.
    An optional api type can be supplied to narrow down the returned nodes.

    :type apiType: int
    :rtype: List[om.MObject]
    """

    return list(iterActiveSelection(apiType=apiType))


def iterActiveSelection(apiType=om.MFn.kDependencyNode):
    """
    Returns a generator that yields the active selection.
    An optional api type can be supplied to narrow down the yielded nodes.

    :type apiType: int
    :rtype: iter
    """

    # Get active selection
    #
    selection = om.MGlobal.getActiveSelectionList()
    selectionCount = selection.length()

    for i in range(selectionCount):

        # Check api type
        #
        dependNode = selection.getDependNode(i)

        if dependNode.hasFn(apiType):

            yield dependNode

        else:

            continue


def getRichSelection(apiType=om.MFn.kMeshVertComponent):
    """
    Just like get component selection this function returns a list of tuples but with a dictionary instead.
    The dictionary value contains a series of vertex index keys that correlate with their soft selection weight.
    MItSelectionList will automatically convert any mesh component back to vertices unless overrided.

    :type apiType: int
    :rtype: List[Sequence[om.MDagPath, Dict[int, float]]]
    """

    # Get rich selection from MGlobal
    #
    softSelection = om.MGlobal.getRichSelection()

    selection = softSelection.getSelection()
    numSelected = selection.length()

    if numSelected > 0:

        # Initialize selection iterator
        #
        iterSelection = om.MItSelectionList(selection, apiType)

        # Iterate through selection
        #
        dagPath, component = None, None
        softWeights = {}

        fnComponent = om.MFnSingleIndexedComponent()

        # Define lambda expression
        #
        getWeight = lambda x: fnComponent.weight(x).influence if fnComponent.hasWeights else 1.0

        while not iterSelection.isDone():

            # Get mesh and vertex component
            #
            dagPath, component = iterSelection.getComponent()
            fnComponent.setObject(component)

            for i in range(fnComponent.elementCount):

                element = fnComponent.element(i)
                softWeights[element] = getWeight(i)

            # Increment iterator
            #
            iterSelection.next()

        return dagPath, softWeights

    else:

        return None, None


def iterActiveComponentSelection():
    """
    Returns a generator that yields the active component selection.
    Each tuple yielded consists on a dag path and a component object.

    :rtype: Iterator[Tuple[om.MDagPath, om.MObject]]
    """

    # Get active selection
    # Unfortunately the rich selection method will raise a runtime error if the selection is empty
    # So we have to wrap this in a try/catch in order to preserve weighted component data
    #
    selection = None

    try:

        selection = om.MGlobal.getRichSelection().getSelection()

    except RuntimeError as exception:

        log.debug(exception)
        selection = om.MGlobal.getActiveSelectionList()

    # Iterate through selection
    #
    iterSelection = om.MItSelectionList(selection, om.MFn.kMeshComponent)

    while not iterSelection.isDone():

        # Check if item has a valid component
        #
        dagPath, component = iterSelection.getComponent()

        if dagPath.isValid() and not component.isNull():

            yield dagPath, component

        else:

            log.debug('Skipping invalid component selection on %s.' % dagPath.partialPathName())

        # Go to next selection
        #
        iterSelection.next()


def iterChildren(transform, apiType=om.MFn.kTransform):
    """
    Returns a generator that yields children from the supplied dag node.
    An optional api type can be supplied to narrow down the children.

    :type transform: Union[om.MObject, om.MDagPath]
    :type apiType: int
    :rtype: iter
    """

    # Initialize function set
    #
    fnDagNode = om.MFnDagNode(getMDagPath(transform))
    childCount = fnDagNode.childCount()

    for i in range(childCount):

        # Check child api type
        #
        child = fnDagNode.child(i)

        if child.hasFn(apiType):

            yield child

        else:

            continue


def iterDescendants(transform, apiType=om.MFn.kTransform):
    """
    Returns a generator that yields all descendants from the supplied dag node.

    :type transform: Union[om.MObject, om.MDagPath]
    :type apiType: int
    :rtype: iter
    """

    # Iterate through queue
    #
    queue = deque([transform])

    while len(queue):

        # Iterate through children
        #
        item = queue.popleft()

        for child in iterChildren(item, apiType=apiType):

            queue.append(child)
            yield child


def iterShapes(transform, apiType=om.MFn.kShape):
    """
    Returns a generator that yields shapes from the supplied dag node.

    :type transform: Union[om.MObject, om.MDagPath]
    :type apiType: int
    :rtype: iter
    """

    # Iterate through children
    #
    fnDagNode = om.MFnDagNode()

    for child in iterChildren(transform, apiType=apiType):

        # Check if child is intermediate object
        #
        fnDagNode.setObject(child)

        if not fnDagNode.isIntermediateObject:

            yield child

        else:

            continue


def iterIntermediateObjects(transform, apiType=om.MFn.kShape):
    """
    Returns a generator that yields intermediate objects from the supplied dag node.

    :type transform: Union[om.MObject, om.MDagPath]
    :type apiType: int
    :rtype: iter
    """

    # Iterate through children
    #
    fnDagNode = om.MFnDagNode()

    for child in iterChildren(transform, apiType=apiType):

        # Check if child is intermediate object
        #
        fnDagNode.setObject(child)

        if fnDagNode.isIntermediateObject:

            yield child

        else:

            continue


def iterFunctionSets():
    """
    Returns a generator that yields all functions sets compatible with dependency nodes.

    :rtype: iter
    """

    # Iterate through dictionary
    #
    for (key, value) in chain(om.__dict__.items(), oma.__dict__.items()):

        # Check if pair matches criteria
        #
        if key.startswith('MFn') and issubclass(value, om.MFnDependencyNode):

            yield value


def iterNodes(apiType=om.MFn.kDependencyNode):
    """
    Returns a generator that yields dependency nodes with the specified API type.
    The default API type will yield ALL nodes derived from "kDependencyNode".

    :type apiType: int
    :rtype: iter
    """

    # Initialize dependency node iterator
    #
    iterDependNodes = om.MItDependencyNodes(apiType)

    while not iterDependNodes.isDone():

        # Get current node
        #
        currentNode = iterDependNodes.thisNode()
        yield currentNode

        # Increment iterator
        #
        iterDependNodes.next()


def iterPluginNodes(typeName):
    """
    Returns a generator that yields plugin derived nodes based on the supplied type name.
    This method will not respect sub-classes on user plugins! But these are SUPER rare...
    The type name is defined through the "MFnPlugin::registerNode()" method as the first argument.

    :type typeName: str
    :rtype: iter
    """

    # Initialize dependency node iterator
    #
    iterDependNodes = om.MItDependencyNodes(om.MFn.kPluginDependNode)
    fnDependNode = om.MFnDependencyNode()

    while not iterDependNodes.isDone():

        # Get current node
        #
        currentNode = iterDependNodes.thisNode()
        fnDependNode.setObject(currentNode)

        if fnDependNode.typeName == typeName:

            yield currentNode

        # Increment iterator
        #
        iterDependNodes.next()


def iterNodesByNamespace(*namespaces, recurse=False):
    """
    Returns a generator that yields dependency nodes from the supplied namespace.

    :type namespaces: Union[str, List[str]]
    :type recurse: bool
    :rtype: iter
    """

    # Iterate through namespaces
    #
    for name in namespaces:

        # Check if namespace exists
        #
        if not om.MNamespace.namespaceExists(name):

            log.warning(f'Cannot locate "{name}" namespace!')
            continue

        # Iterate through namespace objects
        #
        namespace = om.MNamespace.getNamespaceFromName(name)

        for dependNode in namespace.getNamespaceObjects(recurse=recurse):

            yield dependNode


def iterNodesByUuid(*uuids):
    """
    Returns a generator that yields dependency nodes with the specified UUID.

    :type uuids: Union[str, List[str]]
    :rtype: iter
    """

    # Iterate through UUIDs
    #
    for uuid in uuids:

        # Inspect UUID type
        #
        if isinstance(uuid, string_types):

            uuid = om.MUuid(uuid)

        # Add uuid to selection list
        #
        selection = om.MSelectionList()
        selection.add(uuid)

        for i in range(selection.length()):

            yield selection.getDependNode(i)


def iterNodesByPattern(*patterns, apiType=om.MFn.kDependencyNode):
    """
    Returns a generator that yields any nodes whose name matches the supplied patterns.

    :type patterns: Union[str, List[str]]
    :type apiType: int
    :rtype: iter
    """

    # Iterate through nodes
    #
    for dependNode in iterNodes(apiType):

        # Check if there are any pattern matches
        #
        name = getNodeName(dependNode)

        if any(fnmatch.fnmatch(name, pattern) for pattern in patterns):

            yield dependNode

        else:

            continue


def iterDependencies(dependNode, apiType, direction=om.MItDependencyGraph.kDownstream, traversal=om.MItDependencyGraph.kDepthFirst):
    """
    Returns a generator that yields dependencies based on the specified criteria.

    :param dependNode: The dependency node to iterate from.
    :type dependNode: om.MObject
    :param apiType: The specific api type to collect.
    :type apiType: int
    :param direction: The direction to traverse in the node graph.
    :type direction: int
    :param traversal: The order of traversal.
    :type traversal: int
    :rtype: iter
    """

    # Initialize dependency graph iterator
    #
    iterDepGraph = om.MItDependencyGraph(
        dependNode,
        filter=apiType,
        direction=direction,
        traversal=traversal,
        level=om.MItDependencyGraph.kNodeLevel
    )

    while not iterDepGraph.isDone():

        # Get current node
        #
        currentNode = iterDepGraph.currentNode()
        yield currentNode

        # Increment iterator
        #
        iterDepGraph.next()


def dependsOn(dependNode, apiType=om.MFn.kDependencyNode):
    """
    Returns a list of nodes that this object is dependent on.

    :type dependNode: om.MObject
    :type apiType: int
    :rtype: List[om.MObject]
    """

    return list(iterDependencies(dependNode, apiType, direction=om.MItDependencyGraph.kUpstream))


def dependents(dependNode, apiType=om.MFn.kDependencyNode):
    """
    Returns a list of nodes that are dependent on this object.

    :type dependNode: om.MObject
    :type apiType: int
    :rtype: List[om.MObject]
    """

    return list(iterDependencies(dependNode, apiType, direction=om.MItDependencyGraph.kDownstream))


def stripDagPath(name):
    """
    Removes any pipe characters from the supplied name.

    :type name: str
    :rtype: str
    """

    return name.split('|')[-1]


def stripNamespace(name):
    """
    Remove any colon characters from the supplied name.

    :type name: str
    :rtype: str
    """

    return name.split(':')[-1]


def stripAll(name):
    """
    Remove any unwanted characters from the supplied name.

    :type name: str
    :rtype: str
    """

    name = stripDagPath(name)
    name = stripNamespace(name)

    return name


def createDependencyNode(typeName, name=''):
    """
    Creates a node based on the supplied typename or type ID.
    If you wanna create a dag node in world space then supply a null MObject.

    :type typeName: Union[str, int]
    :type name: str
    :rtype: om.MObject
    """

    # Add node to the modifier stack
    #
    dagModifier = om.MDGModifier()
    dependNode = dagModifier.createNode(typeName)

    # Check if a name was supplied
    #
    if len(name) > 0:

        dagModifier.renameNode(dependNode, name)

    # Execute stack
    #
    dagModifier.doIt()
    return dependNode


def createDagNode(typeName, name='', parent=om.MObject.kNullObj):
    """
    Creates a dag node using the supplied type name.

    :type typeName: str
    :type name: str
    :type parent: om.MObject
    :rtype: om.MObject
    """

    # Add node to the modifier stack
    #
    dagModifier = om.MDagModifier()
    dependNode = dagModifier.createNode(typeName, parent=parent)

    # Check if a name was supplied
    #
    if len(name) > 0:

        dagModifier.renameNode(dependNode, name)

    # Execute stack
    #
    dagModifier.doIt()
    return dependNode


def createComponent(indices, apiType=om.MFn.kSingleIndexedComponent):
    """
    Method used to create a component object based on a list of elements and an api enumerator constant.

    :type indices: om.MIntArray
    :type apiType: int
    :rtype: om.MObject
    """

    # Check value type
    #
    if isinstance(indices, om.MIntArray):

        # Create component from function set
        #
        fnSingleIndexComponent = om.MFnSingleIndexedComponent()
        component = fnSingleIndexComponent.create(apiType)

        # Add elements to component
        #
        fnSingleIndexComponent.addElements(indices)

        return component

    elif isinstance(indices, (list, set, tuple, deque)):

        return createComponent(om.MIntArray(indices), apiType=apiType)

    elif isinstance(indices, int):

        return createComponent(om.MIntArray([indices]), apiType=apiType)

    elif indices is None:

        return createComponent(om.MIntArray(), apiType=apiType)

    else:

        raise TypeError('createComponent() expects a list (%s given)!' % type(indices).__name__)


def deleteNode(dependNode):
    """
    Deletes the supplied dependency node from the scene file.
    This operation must be done in chunks starting with breaking connections before deleting the node.

    :type dependNode: om.MObject
    :rtype: None
    """

    # Initialize function set
    #
    fnDependNode = om.MFnDependencyNode(dependNode)
    dagModifier = om.MDagModifier()

    # Break all connections to node
    #
    plugs = fnDependNode.getConnections()

    for plug in plugs:

        # Check if this plug has a source connection
        #
        source = plug.source()

        if not source.isNull:

            log.info('Breaking connection: %s and %s' % (source.info, plug.info))
            dagModifier.disconnect(source, plug)

        # Check if this plug has any destination connections
        #
        destinations = plug.destinations()

        for destination in destinations:

            log.info('Breaking connection: %s and %s' % (plug.info, destination.info))
            dagModifier.disconnect(plug, destination)

    dagModifier.doIt()

    # Finally delete the node
    #
    log.info('Deleting node: %s' % fnDependNode.name())

    dagModifier.deleteNode(dependNode)
    dagModifier.doIt()
