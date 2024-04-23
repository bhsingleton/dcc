import re
import fnmatch

from maya import cmds as mc, OpenMaya as legacy
from maya.api import OpenMaya as om, OpenMayaAnim as oma
from six import string_types, integer_types
from collections import deque
from itertools import chain
from . import plugutils
from ..decorators.undo import commit
from ...python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__name_regex__ = re.compile(r'^(?:\:?([a-zA-Z0-9_]))+$')
__uuid_regex__ = re.compile(r'^[A-Z0-9]{8}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{12}$')
__path_regex__ = re.compile(r'^(.*\|)([^\|]*)$')


def getNodeName(node, includePath=False, includeNamespace=False):
    """
    Returns the name of the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type includePath: bool
    :type includeNamespace: bool
    :rtype: str
    """

    # Check api type
    #
    node = getMObject(node)

    if not node.hasFn(om.MFn.kDependencyNode):

        return ''

    # Check if path should be included
    #
    if includePath:

        return '|'.join([getNodeName(ancestor, includeNamespace=includeNamespace) for ancestor in traceHierarchy(node)])

    elif includeNamespace:

        return '{namespace}:{name}'.format(namespace=getNodeNamespace(node), name=getNodeName(node))

    else:

        return stripAll(om.MFnDependencyNode(node).name())


def getNodeNamespace(node):
    """
    Returns the namespace from the supplied node.

    :rtype: str
    """

    return om.MFnDependencyNode(getMObject(node)).namespace


def getNodeUUID(node, asString=False):
    """
    Returns the UUID from the supplied node.

    :rtype: Union[om.MUuid, str]
    """

    uuid = om.MFnDependencyNode(getMObject(node)).uuid()

    if asString:

        return uuid.asString()

    else:

        return uuid


def getNodeHashCode(value):
    """
    Returns a hash code from the supplied value.

    :type value: Union[str, om.MObject, om.MObjectHandle, om.MDagPath]
    :rtype: int
    """

    return getMObjectHandle(value).hashCode()


def demoteMObject(node):
    """
    Demotes the supplied MObject back into the legacy API type.
    This method only supports dependency/dag nodes!

    :type node: om.MObject
    :rtype: legacy.MObject
    """

    # Check value type
    #
    if not isinstance(node, om.MObject):

        raise TypeError('demoteMObject() expects the new MObject type!')

    # Get full path name from node
    #
    fullPathName = ''

    if node.hasFn(om.MFn.kDagNode):

        dagPath = om.MDagPath.getAPathTo(node)
        fullPathName = dagPath.fullPathName()

    elif node.hasFn(om.MFn.kDependencyNode):

        fullPathName = om.MFnDependencyNode(node).absoluteName()

    else:

        raise TypeError('getLegacyMObject() expects a dependency node (%s given)!' % node.apiTypeStr)

    # Add name to legacy selection list
    #
    selectionList = legacy.MSelectionList()
    selectionList.add(fullPathName)

    legacyDependNode = legacy.MObject()
    selectionList.getDependNode(0, legacyDependNode)

    return legacyDependNode


def promoteMObject(node):
    """
    Promotes the supplied MObject back into the new API type.
    This method only supports dependency/dag nodes!

    :type node: legacy.MObject
    :rtype: om.MObject
    """

    # Check value type
    #
    if not isinstance(node, legacy.MObject):

        raise TypeError('promoteMObject() expects the legacy MObject type!')

    # Get full path name from node
    #
    fullPathName = ''

    if node.hasFn(legacy.MFn.kDagNode):

        dagPath = legacy.MDagPath()
        legacy.MDagPath.getAPathTo(node, dagPath)

        fullPathName = dagPath.fullPathName()

    elif node.hasFn(legacy.MFn.kDependencyNode):

        fullPathName = om.MFnDependencyNode(node).absoluteName()

    else:

        raise TypeError('promoteLegacyMObject() expects a dependency node (%s given)!' % node.apiTypeStr)

    # Add name to selection list
    #
    selectionList = om.MSelectionList()
    selectionList.add(fullPathName)

    return selectionList.getDependNode(0)


def getMObjectByName(name):
    """
    Returns an MObject from the supplied node name.

    :type string: Union[str, unicode]
    :rtype: om.MObject
    """

    # Check if a namespace was supplied
    # If not, then use a wildcard to search recursively!
    #
    strings = name.split(':')
    hasNamespace = len(strings) >= 2

    name = strings[-1]
    namespaces = (':'.join(strings[:-1]),) if hasNamespace else ('', '*')  # Wildcards do not account for the root namespace!

    selection = om.MSelectionList()

    for namespace in namespaces:

        try:

            selection.add(f'{namespace}:{name}')

        except RuntimeError as exception:

            continue

    # Evaluate selection list
    #
    selectionCount = selection.length()

    if selectionCount > 0:

        return selection.getDependNode(0)

    else:

        log.debug(f'Cannot locate node from name: "{name}"')
        return om.MObject.kNullObj


def getMObjectByPath(path):
    """
    Returns an MObject from the supplied node path.

    :type string: Union[str, unicode]
    :rtype: om.MObject
    """

    # Check if a namespace was supplied
    # If not, then use a wildcard to search recursively!
    #
    hierarchy = path.split('|')
    leafName = hierarchy[-1]
    strings = leafName.split(':')
    hasNamespace = len(strings) >= 2

    name = strings[-1]
    namespaces = (':'.join(strings[:-1]),) if hasNamespace else ('', '*')

    selection = om.MSelectionList()

    for namespace in namespaces:

        try:

            selection.add(f'{namespace}:{name}')

        except RuntimeError as exception:

            continue

    # Evaluate selection list
    #
    selectionCount = selection.length()

    if selectionCount == 0:

        log.debug(f'Cannot locate node from path: "{path}"')
        return om.MObject.kNullObj

    elif selectionCount == 1:

        return selection.getDependNode(0)

    else:

        parentPath = '|'.join(hierarchy[:-1])

        for i in range(selectionCount):

            node = selection.getDependNode(i)
            nodePath = getNodeName(includePath=True, includeNamespace=hasNamespace)

            if nodePath.startswith(parentPath):

                return node

            else:

                continue

        log.debug(f'Cannot locate node from path: "{path}"')
        return om.MObject.kNullObj


def getMObjectByString(string):
    """
    Returns an MObject from the supplied node name.

    :type string: Union[str, unicode]
    :rtype: om.MObject
    """

    # Check if string contains an attribute
    #
    isName = __name_regex__.match(string)
    isPath = __path_regex__.match(string)
    isUUID = __uuid_regex__.match(string)

    if isName:

        return getMObjectByName(string)

    elif isPath:

        return getMObjectByPath(string)

    elif isUUID:

        return getMObjectByMUuid(string)

    else:

        raise TypeError(f'getMObjectByName() expects a valid string ("{string}" given)!')


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


__get_mobject__ = {
    'str': getMObjectByString,
    'unicode': getMObjectByString,  # Leaving this here for backwards compatibility!
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
    func = __get_mobject__.get(typeName, None)

    if func is not None:

        return func(value)

    else:

        raise TypeError('getMObject() expects %s (%s given)!' % (tuple(__get_mobject__.keys()), type(value).__name__))


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


def uniquifyObjects(objects):
    """
    Returns a unique list of objects from the supplied array.

    :type objects: om.MObjectArray
    :rtype: om.MObjectArray
    """

    handles = list(map(om.MObjectHandle, objects))
    return om.MObjectArray(list({handle.hashCode(): handle.object() for handle in handles}.values()))


def getWorldNode():
    """
    Returns the world node.

    :rtype: om.MObject
    """

    return list(iterNodes(apiType=om.MFn.kWorld))[0]


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


def getShapeDirectlyBelow(node):
    """
    Returns the shape node directly below the supplied transform.

    :type node: Union[om.MObject, om.MDagPath]
    :rtype: om.MDagPath
    """

    shapes = list(iterShapes(node))
    numShapes = len(shapes)

    if numShapes == 0:

        return None

    elif numShapes == 1:

        return shapes[0]

    else:

        raise TypeError('getShapeDirectlyBelow() expects to find 1 shape (%s found)!' % numShapes)


def iterAssociatedDeformers(node, apiType=om.MFn.kGeometryFilt):
    """
    Returns a generator that yields deformers associated with the supplied object.
    It is safe to supply either the transform, shape or deformer component.

    :type node: Union[om.MObject, om.MDagPath]
    :type apiType: int
    :rtype: Iterator[om.MObject]
    """

    # Check api type
    #
    node = getMObject(node)

    if node.hasFn(om.MFn.kTransform):

        return iterAssociatedDeformers(getShapeDirectlyBelow(node), apiType=apiType)

    elif node.hasFn(om.MFn.kGeometryFilt):

        return iterAssociatedDeformers(dependents(node, apiType=om.MFn.kShape)[0], apiType=apiType)

    elif node.hasFn(om.MFn.kShape):

        return iterDependencies(node, apiType, direction=om.MItDependencyGraph.kUpstream)

    else:

        log.warning('iterAssociatedDeformers() expects a shape node (%s given)!' % node.apiTypeStr)
        return


def iterDeformersFromSelection(apiType=om.MFn.kGeometryFilt):
    """
    Returns a generator that yields deformers from the active selection.
    An optional api type can be provided to narrow down the yielded deformers.

    :type apiType: int
    :rtype: Iterator[om.MObject]
    """

    # Iterate through selection
    #
    for dependNode in iterActiveSelection(apiType=om.MFn.kDagNode):

        # Iterate through deformers
        #
        for deformer in iterAssociatedDeformers(dependNode, apiType=apiType):

            yield deformer


def getAssociatedDeformers(node, apiType=om.MFn.kGeometryFilt):
    """
    Returns a list of deformers associated with the supplied shape.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type apiType: int
    :rtype: List[om.MObject]
    """

    return list(iterAssociatedDeformers(node, apiType=apiType))


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


def getAssociatedReferenceNode(node):
    """
    Returns the reference node associated with the supplied dependency node.
    If this node is not referenced then none will be returned!

    :type node: om.MObject
    :rtype: om.MObject
    """

    # Check if node is referenced
    #
    fnDependNode = om.MFnDependencyNode(node)

    if not fnDependNode.isFromReferencedFile:

        return None

    # Iterate through reference nodes
    #
    fnReference = om.MFnReference()

    for reference in iterNodes(apiType=om.MFn.kReference):

        # Check if reference contains node
        #
        fnReference.setObject(reference)

        if fnReference.containsNodeExactly(node):

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
    :rtype: List[Tuple[om.MDagPath, Dict[int, float]]]
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


def iterActiveComponentSelection(apiType=om.MFn.kDagNode, skipNullComponents=True):
    """
    Returns a generator that yields the active component selection.
    Each tuple yielded consists on a dag path and a component object.

    :type apiType: int
    :type skipNullComponents: bool
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
    selectionCount = selection.length()

    for i in range(selectionCount):

        # Evaluate api type
        #
        node = selection.getDependNode(i)
        isDagNode = node.hasFn(om.MFn.kDagNode)

        if not (node.hasFn(apiType) and isDagNode):

            continue

        # Evaluate component object
        #
        dagPath, component = selection.getComponent(i)

        if not (component.isNull() and skipNullComponents):

            yield dagPath, component

        else:

            log.debug(f'Skipping null component @ {dagPath.partialPathName()}')
            continue


def getParent(node):
    """
    Returns the parent of the supplied node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :rtype: om.MObject
    """

    # Check if node has a parent
    #
    dagPath = getMDagPath(node)
    fnDagNode = om.MFnDagNode(dagPath)

    parentCount = fnDagNode.parentCount()

    if parentCount == 0:

        return om.MObject.kNullObj

    # Make sure parent isn't world
    #
    parent = fnDagNode.parent(0)

    if not parent.hasFn(om.MFn.kWorld):

        return parent

    else:

        return om.MObject.kNullObj


def iterAncestors(node, apiType=om.MFn.kTransform):
    """
    Returns a generator that yields ancestors from the supplied transform.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type apiType: int
    :rtype: Iterator[om.MObject]
    """

    # Iterate through parents
    #
    ancestor = getParent(node)

    while not ancestor.isNull():

        # Evaluate api type
        #
        if ancestor.hasFn(apiType):

            yield ancestor
            ancestor = getParent(ancestor)

        else:

            break


def traceHierarchy(node):
    """
    Returns a generator that yields the nodes leading up to, and including, the supplied transform.

    :type node: om.MObject
    :rtype: Iterator[om.MObject]
    """

    yield from reversed(list(iterAncestors(node)))
    yield node


def iterChildren(node, apiType=om.MFn.kTransform):
    """
    Returns a generator that yields children from the supplied dag node.
    An optional api type can be supplied to narrow down the children.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type apiType: int
    :rtype: Iterator[om.MObject]
    """

    # Verify this is a dag node
    #
    node = getMObject(node)

    if not node.hasFn(om.MFn.kDagNode):

        return iter([])

    # Iterate through children
    #
    dagPath = getMDagPath(node)
    fnDagNode = om.MFnDagNode(dagPath)

    childCount = fnDagNode.childCount()

    for i in range(childCount):

        # Evaluate api type
        #
        child = fnDagNode.child(i)

        if child.hasFn(apiType):

            yield child

        else:

            continue


def iterDescendants(node, apiType=om.MFn.kTransform):
    """
    Returns a generator that yields all descendants from the supplied dag node.

    :type node: Union[str, om.MObject, om.MDagPath]
    :type apiType: int
    :rtype: Iterator[om.MObject]
    """

    # Iterate through queue
    #
    queue = deque([node])

    while len(queue) > 0:

        # Pop descendant and yield children
        #
        descendant = queue.popleft()
        children = list(iterChildren(descendant, apiType=apiType))
        queue.extend(children)

        yield from children


def iterShapes(node, apiType=om.MFn.kShape):
    """
    Returns a generator that yields shapes from the supplied dag node.

    :type node: Union[om.MObject, om.MDagPath]
    :type apiType: int
    :rtype: Iterator[om.MObject]
    """

    # Iterate through children
    #
    fnDagNode = om.MFnDagNode()

    for child in iterChildren(node, apiType=apiType):

        # Check if child is intermediate object
        #
        fnDagNode.setObject(child)

        if not fnDagNode.isIntermediateObject:

            yield child

        else:

            continue


def iterIntermediateObjects(node, apiType=om.MFn.kShape):
    """
    Returns a generator that yields intermediate objects from the supplied dag node.

    :type node: Union[om.MObject, om.MDagPath]
    :type apiType: int
    :rtype: Iterator[om.MObject]
    """

    # Iterate through children
    #
    fnDagNode = om.MFnDagNode()

    for child in iterChildren(node, apiType=apiType):

        # Check if child is intermediate object
        #
        fnDagNode.setObject(child)

        if fnDagNode.isIntermediateObject:

            yield child

        else:

            continue


def iterFunctionSets():
    """
    Returns a generator that yields functions sets compatible with dependency nodes.

    :rtype: Iterator[om.MFnBase]
    """

    # Iterate through dictionary
    #
    for (key, value) in chain(om.__dict__.items(), oma.__dict__.items()):

        # Check if pair matches criteria
        #
        if key.startswith('MFn') and issubclass(value, om.MFnDependencyNode):

            yield value


def iterNodes(apiType=om.MFn.kDependencyNode, typeName=None):
    """
    Returns a generator that yields dependency nodes.
    The default arguments will yield ALL nodes derived from the `kDependencyNode` type.

    :type apiType: int
    :type typeName: str
    :rtype: Iterator[om.MObject]
    """

    # Check if a type name was supplied
    #
    if not stringutils.isNullOrEmpty(typeName):

        # Yield nodes from `ls` command
        #
        nodeNames = mc.ls(type=typeName, long=True)

        for nodeName in nodeNames:

            yield getMObjectByName(nodeName)

    else:

        # Initialize dependency node iterator
        #
        iterDependNodes = om.MItDependencyNodes(apiType)

        while not iterDependNodes.isDone():

            # Yield current node
            #
            currentNode = iterDependNodes.thisNode()
            yield currentNode

            # Increment iterator
            #
            iterDependNodes.next()


def iterVisibleNodes():
    """
    Returns a generator that yields transforms with visible shapes.

    :rtype: Iterator[om.MObject]
    """

    # Iterate through shapes
    #
    for node in iterNodes(apiType=om.MFn.kTransform):

        # Evaluate shape visibility
        #
        isVisible = [getMDagPath(shape).isVisible() for shape in iterShapes(node)]

        if all(isVisible) and len(isVisible) > 0:

            yield node

        else:

            continue


def iterPluginNodes(typeName):
    """
    Returns a generator that yields plugin derived nodes based on the supplied type name.
    This method will not respect subclasses on user plugins! But these are SUPER rare...
    The type name is defined through the "MFnPlugin::registerNode()" method as the first argument.

    :type typeName: str
    :rtype: Iterator[om.MObject]
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
    :rtype: Iterator[om.MObject]
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
    :rtype: Iterator[om.MObject]
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


def iterNodesByPattern(*patterns, apiType=om.MFn.kDependencyNode, exactType=False):
    """
    Returns a generator that yields any nodes whose name matches the supplied patterns.

    :type patterns: Union[str, List[str]]
    :type apiType: int
    :type exactType: bool
    :rtype: Iterator[om.MObject]
    """

    # Compose selection list from patterns
    #
    selectionList = om.MSelectionList()

    for pattern in patterns:

        try:

            selectionList.add(pattern)

        except RuntimeError:

            continue

    # Iterate through selection list
    #
    selectionCount = selectionList.length()

    for i in range(selectionCount):

        # Check if node matches api type
        #
        node = selectionList.getDependNode(i)

        if exactType and node.apiType() == apiType:

            yield node

        elif not exactType and node.hasFn(apiType):

            yield node

        else:

            continue


def iterDependencies(node, apiType, typeName=None, direction=om.MItDependencyGraph.kDownstream, traversal=om.MItDependencyGraph.kDepthFirst):
    """
    Returns a generator that yields dependencies based on the specified criteria.

    :param node: The dependency node to iterate from.
    :type node: om.MObject
    :param apiType: The specific api type to collect, the default being all dependency nodes.
    :type apiType: int
    :param typeName: The specific type name to collect if supplied.
    :type typeName: Union[str, None]
    :param direction: The direction to traverse in the node graph.
    :type direction: int
    :param traversal: The order of traversal.
    :type traversal: int
    :rtype: Iterator[om.MObject]
    """

    # Initialize dependency graph iterator
    #
    fnDependNode = om.MFnDependencyNode()

    iterDepGraph = om.MItDependencyGraph(
        node,
        filter=apiType,
        direction=direction,
        traversal=traversal,
        level=om.MItDependencyGraph.kNodeLevel
    )

    useTypeName = not stringutils.isNullOrEmpty(typeName)
    typeNames = mc.nodeType(typeName, isTypeName=True, derived=True) if useTypeName else []

    while not iterDepGraph.isDone():

        # Evaluate current node
        #
        currentNode = iterDepGraph.currentNode()
        fnDependNode.setObject(currentNode)

        if (fnDependNode.typeName in typeNames and useTypeName) or not useTypeName:

            yield currentNode

        # Go to next item
        #
        iterDepGraph.next()


def dependsOn(node, apiType=om.MFn.kDependencyNode, typeName=None):
    """
    Returns a list of nodes that this object is dependent on.

    :type node: om.MObject
    :type apiType: int
    :type typeName: Union[str, None]
    :rtype: List[om.MObject]
    """

    return list(iterDependencies(node, apiType, typeName=typeName, direction=om.MItDependencyGraph.kUpstream))


def dependents(node, apiType=om.MFn.kDependencyNode, typeName=None):
    """
    Returns a list of nodes that are dependent on this object.

    :type node: om.MObject
    :type apiType: int
    :type typeName: Union[str, None]
    :rtype: List[om.MObject]
    """

    return list(iterDependencies(node, apiType, typeName=typeName, direction=om.MItDependencyGraph.kDownstream))


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


def absolutify(name, namespace=''):
    """
    Ensures the supplied name starts with the root namespace.

    :type name: str
    :type namespace: str
    :rtype: str
    """

    if not name.startswith(':'):

        return f'{namespace}:{name}'

    else:

        return name


def isDGType(typeName):
    """
    Evaluates if the supplied type name is derived from a dag node.

    :type typeName: Union[str, int]
    :rtype: bool
    """

    if isinstance(typeName, string_types):

        return om.MNodeClass(typeName).hasAttr('message')

    elif isinstance(typeName, integer_types):

        return om.MFnDependencyNode().hasObj(typeName)

    else:

        raise TypeError('isDGType() expects either a str or int (%s given)!' % type(typeName).__name__)


def isDAGType(typeName):
    """
    Evaluates if the supplied type name is derived from a dag node.
    This method also accepts `MFn` type IDs.

    :type typeName: Union[str, int]
    :rtype: bool
    """

    if isinstance(typeName, string_types):

        return om.MNodeClass(typeName).hasAttribute('visibility')

    elif isinstance(typeName, integer_types):

        return om.MFnDagNode().hasObj(typeName)

    else:

        raise TypeError('isDAGType() expects either a str or int (%s given)!' % type(typeName).__name__)


def createNode(typeName, name='', parent=None, skipSelect=True):
    """
    Creates a new dependency node from the supplied type name.

    :type typeName: Union[str, int]
    :type name: str
    :type parent: Union[str, om.MObject, om.MDagPath, None]
    :type skipSelect: bool
    :rtype: om.MObject
    """

    # Create new node
    #
    node = om.MObject.kNullObj
    parent = om.MObject.kNullObj if (parent is None) else getMObject(parent)

    modifier = None

    if isDAGType(typeName):

        modifier = om.MDagModifier()
        node = modifier.createNode(typeName, parent=parent)

    else:

        modifier = om.MDGModifier()
        node = modifier.createNode(typeName)

    # Check if inverse-scale is required
    #
    if node.hasFn(om.MFn.kJoint) and parent.hasFn(om.MFn.kJoint):

        source = plugutils.findPlug(parent, 'scale')
        destination = plugutils.findPlug(node, 'inverseScale')

        plugutils.connectPlugs(source, destination)

    # Execute modifier
    #
    commit(modifier.doIt, modifier.undoIt)
    modifier.doIt()

    # Check if a name was supplied
    #
    if not stringutils.isNullOrEmpty(name):

        renameNode(node, name)

    # Check if node should be selected
    #
    if not skipSelect:

        selectionList = createSelectionList([node])
        om.MGlobal.setActiveSelectionList(selectionList)

    return node


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


def renameNode(node, newName, modifier=None):
    """
    Renames the supplied node to the new name.

    :type node: om.MObject
    :type newName: str
    :type modifier: Union[om.MDGModifier, None]
    :rtype: str
    """

    # Check if a dag modifier was supplied
    #
    if modifier is None:

        modifier = om.MDGModifier()

    # Cache and execute modifier
    #
    modifier.renameNode(node, newName)

    commit(modifier.doIt, modifier.undoIt)
    modifier.doIt()

    return newName


def reparentNode(node, otherNode, modifier=None):
    """
    Parents the supplied node to the other node.

    :type node: om.MObject
    :type otherNode: om.MObject
    :type modifier: Union[om.MDGModifier, None]
    :rtype: om.MObject
    """

    # Check if a dag modifier was supplied
    #
    if modifier is None:

        modifier = om.MDagModifier()

    # Cache and execute modifier
    #
    modifier.reparentNode(node, newParent=otherNode)

    commit(modifier.doIt, modifier.undoIt)
    modifier.doIt()

    return otherNode


def deleteNode(node):
    """
    Deletes the supplied dependency node from the scene file.
    In order to prevent any other nodes from being deleted this method breaks all connections before deleting the node.

    :type node: om.MObject
    :rtype: None
    """

    # Break any connections to node
    #
    node = getMObject(node)
    plugs = om.MFnDependencyNode(node).getConnections()
    hasPlugs = len(plugs) > 0

    modifier = om.MDGModifier()

    if hasPlugs:

        for plug in plugs:

            # Check if this plug has a source connection
            #
            source = plug.source()

            if not source.isNull:

                log.debug(f'Breaking connection: {source.info} and {plug.info}')
                modifier.disconnect(source, plug)

            # Check if this plug has any destination connections
            #
            destinations = plug.destinations()

            for destination in destinations:

                log.debug(f'Breaking connection: {plug.info} and {destination.info}')
                modifier.disconnect(plug, destination)

        commit(modifier.doIt, modifier.undoIt)
        modifier.doIt()

    # Next, check if children should be re-parented
    #
    isDagNode = node.hasFn(om.MFn.kDagNode)

    if isDagNode:

        modifier = om.MDagModifier()
        children = list(iterChildren(node, apiType=om.MFn.kTransform))

        hasChildren = len(children) > 0

        if hasChildren:

            for child in children:

                modifier.reparentNode(child)

            commit(modifier.doIt, modifier.undoIt)
            modifier.doIt()

    # Finally, delete node and execute modifier stack
    #
    modifier = om.MDagModifier() if isDagNode else om.MDGModifier()
    modifier.deleteNode(node, includeParents=False)

    commit(modifier.doIt, modifier.undoIt)
    modifier.doIt()
