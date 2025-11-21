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


def getNodeFromModifier(modifier):
    """
    Returns the node associated with the given modifier.

    :type modifier: pymxs.MXSWrapperBase
    :rtype: pymxs.MXSWrapperBase
    """

    if isValidModifier(modifier):

        return pymxs.runtime.refs.dependentNodes(modifier, firstOnly=True)

    elif nodeutils.isValidNode(modifier):  # Redundancy check

        return modifier

    else:

        return None
