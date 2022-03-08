import pymxs

from six import string_types

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


BASE_TYPES = {'modifier': pymxs.runtime.modifier}


def findModifierByType(obj, modifierType):
    """
    Finds the skin modifier from the given object.

    :type obj: Union[str, pymxs.MXSWrapperBase]
    :type modifierType: pymxs.MXSWrapperBase
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
            modifiers = [modifier for modifier in obj.modifiers if pymxs.runtime.classOf(modifier) == modifierType]
            numModifiers = len(modifiers)

            if numModifiers == 1:

                return modifiers[0]

            else:

                raise TypeError('findModifierByType() expects 1 modifier (%s found)!' % numModifiers)

        elif pymxs.runtime.classOf(obj) == modifierType:

            return obj

        else:

            raise TypeError('findModifierByType() expects a node!')

    elif isinstance(obj, string_types):

        return findModifierByType(pymxs.runtime.getNodeByName(obj), modifierType)

    else:

        raise TypeError('findModifierByType() expects a MXSWrapper (%s given)!' % type(obj).__name__)


def isValidModifier(obj):
    """
    Evaluates if the supplied object is a valid modifier.

    :rtype: bool
    """

    return pymxs.runtime.superClassOf(obj) == pymxs.runtime.modifier


def getNodeFromModifier(modifier):
    """
    Returns the node associated with the given modifier.

    :type modifier: pymxs.MXSWrapperBase
    :rtype: pymxs.MXSWrapperBase
    """

    return pymxs.runtime.refs.dependentNodes(modifier)[0]
