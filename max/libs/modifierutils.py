import pymxs

from . import wrapperutils, nodeutils
from ...vendor.six import string_types

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def hasModifier(node, modifierType):
    """
    Evaluates if the supplied node has the specified modifier type.

    :type node: pymxs.MXSWrapperBase
    :type modifierType: pymxs.MAXClass
    :rtype: bool
    """

    return len(getModifierByClass(node, modifierType, all=True)) > 0


def getModifierByClass(node, modifierClass, all=False):
    """
    Returns a modifier derived from the specified type from the supplied node.

    :type node: Union[str, pymxs.MXSWrapperBase]
    :type modifierClass: pymxs.runtime.MAXClass
    :type all: bool
    :rtype: pymxs.MXSWrapperBase
    """

    # Evaluate node type
    #
    if isinstance(node, string_types):

        node = pymxs.runtime.getNodeByName(node)

    # Check if node is valid
    #
    if nodeutils.isValidNode(node):

        # Collect all modifiers by type
        #
        modifiers = [modifier for modifier in node.modifiers if pymxs.runtime.isKindOf(modifier, modifierClass)]

        if all:

            return modifiers

        # Evaluate collected modifiers
        #
        numModifiers = len(modifiers)

        if numModifiers == 0:

            return None

        elif numModifiers == 1:

            return modifiers[0]

        else:

            raise TypeError(f'getModifierByClass() expects a unique modifier ({numModifiers} found)!')

    elif isValidModifier(node):  # Redundancy check

        return node

    else:

        raise TypeError('getModifierByClass() expects a valid node!')


def isValidModifier(modifier):
    """
    Evaluates if the supplied object is a valid modifier.
    Not to be confused with `validModifier` from `pymxs` which tests if a node accepts a specific modifier!

    :type modifier: pymxs.MXSWrapperBase
    :rtype: bool
    """

    isModifier = pymxs.runtime.isKindOf(modifier, pymxs.runtime.Modifier)
    isValid = pymxs.runtime.isValidObj(modifier)
    isAlive = not pymxs.runtime.isDeleted(modifier)

    return isModifier and isValid and isAlive


def acceptsModifier(node, modifierClass):
    """
    Evaluates if the supplied node accepts the specified modifier class.

    :type node: pymxs.MXSWrapperBase
    :type modifierClass: pymxs.MAXClass
    :rtype: bool
    """

    if nodeutils.isValidNode(node) and wrapperutils.isClass(modifierClass):

        return pymxs.runtime.validModifier(node, modifierClass)

    else:

        return False


def getLastModifier(node):
    """
    Returns the last modifier from the supplied node's modifier stack.
    If the node has no modifiers then the base object is returned!

    :type node: pymxs.runtime.Node
    :rtype: pymxs.MXSWrapperBase
    """

    modifiers = getattr(node, 'modifiers', [])
    numModifiers = len(modifiers)

    if numModifiers > 0:

        return modifiers[0]  # In 3dsMax the last modifier is the first in the array!

    else:

        return getattr(node, 'baseObject', node)


def getNodeFromModifier(modifier):
    """
    Returns the node associated with the given modifier.

    :type modifier: pymxs.MXSWrapperBase
    :rtype: pymxs.MXSWrapperBase
    """

    if nodeutils.isValidBaseObject(modifier) or isValidModifier(modifier):

        return pymxs.runtime.refs.dependentNodes(modifier, firstOnly=True)

    elif nodeutils.isValidNode(modifier):  # Redundancy check

        return modifier

    else:

        return None


def ensureModifier(nodes, modifierClass, filter=pymxs.runtime.Node, defaults={}, before=1):
    """
    Ensures that the supplied nodes have a modifier derived from the specified class.

    :type nodes: List[pymxs.runtime.Node]
    :type modifierClass: pymxs.MAXClass
    :type filter: pymxs.runtime.MAXClass
    :type defaults: dict
    :type before: int
    :rtype: None
    """

    # Iterate through nodes
    #
    for node in nodes:

        # Check if node accepts modifier
        #
        isKindOf = wrapperutils.isKindOf(node, filter)
        accepted = acceptsModifier(node, modifierClass)

        if not (isKindOf and accepted):

            continue

        # Check if modifier already exists
        #
        modifiers = getModifierByClass(node, modifierClass, all=True)
        numModifiers = len(modifiers)

        if numModifiers > 0:

            continue

        # Update modifier defaults
        #
        modifier = modifierClass()

        for (key, value) in defaults.items():

            setattr(modifier, key, value)

        # Add modifier to node
        #
        pymxs.runtime.addModifier(node, modifier, before=before)


def deleteModifiersByClass(nodes, modifierClass):
    """
    Deletes any modifiers derived from the specified class from the supplied nodes.

    :type nodes: List[pymxs.MXSWrapperBase]
    :type modifierClass: pymxs.MAXClass
    :rtype: None
    """

    for node in nodes:

        modifiers = getModifierByClass(node, modifierClass, all=True)

        for modifier in reversed(modifiers):

            pymxs.runtime.deleteModifier(node, modifier)
