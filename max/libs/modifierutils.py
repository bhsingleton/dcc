import pymxs

from six import string_types

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

    return len(findModifierByType(node, modifierType, all=True)) > 0


def findModifierByType(node, modifierType, all=False):
    """
    Returns a modifier derived from the specified type from the supplied node.

    :type node: Union[str, pymxs.MXSWrapperBase]
    :type modifierType: pymxs.runtime.MAXClass
    :type all: bool
    :rtype: pymxs.MXSWrapperBase
    """

    # Evaluate node type
    #
    if isinstance(node, string_types):

        node = pymxs.runtime.getNodeByName(node)

    # Check if node is valid
    #
    if pymxs.runtime.isValidNode(node):

        # Collect all modifiers by type
        #
        modifiers = [modifier for modifier in node.modifiers if pymxs.runtime.isKindOf(modifier, modifierType)]

        if all:

            return modifiers

        else:

            # Evaluate collected modifiers
            #
            numModifiers = len(modifiers)

            if numModifiers == 0:

                return None

            elif numModifiers == 1:

                return modifiers[0]

            else:

                raise TypeError('findModifierByType() expects a unique modifier (%s found)!' % numModifiers)

    elif pymxs.runtime.isKindOf(node, modifierType):  # Redundancy check

        return node

    else:

        raise TypeError('findModifierByType() expects a valid node!')


def isValidModifier(modifier):
    """
    Evaluates if the supplied object is a valid modifier.

    :type modifier: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.isKindOf(modifier, pymxs.runtime.Modifier) and pymxs.runtime.isValidObj(modifier)


def getNodeFromModifier(modifier):
    """
    Returns the node associated with the given modifier.

    :type modifier: pymxs.MXSWrapperBase
    :rtype: pymxs.MXSWrapperBase
    """

    return pymxs.runtime.refs.dependentNodes(modifier, firstOnly=True)
