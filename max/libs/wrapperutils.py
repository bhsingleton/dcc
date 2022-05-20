import pymxs

from . import nodeutils, controllerutils, attributeutils
from ...python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def getNextDependent(obj):
    """
    Returns the next logical up-stream dependent.
    This method will only consider sub-anims or custom attributes.

    :type obj: pymxs.MXSWrapperBase
    :rtype: pymxs.MXSWrapperBase
    """

    # Check if this is a sub-anim
    #
    if pymxs.runtime.isValidNode(obj):

        return

    elif pymxs.runtime.isKindOf(obj, pymxs.runtime.SubAnim):

        return obj.parent

    elif pymxs.runtime.isKindOf(obj, pymxs.runtime.ParamBlock2):

        definition = attributeutils.getAssociatedDefinition(obj)
        subAnim = controllerutils.getAssociatedSubAnim(obj)

        return definition if definition is not None else subAnim

    elif pymxs.runtime.isKindOf(obj, pymxs.runtime.AttributeDef):

        return pymxs.runtime.CustAttributes.getOwner(obj)

    else:

        return controllerutils.getAssociatedSubAnim(obj)


def iterDependents(obj):
    """
    Returns a generator that yields the upstream dependents from the given object.

    :type obj: pymxs.MXSWrapperBase
    :rtype: iter
    """

    dependent = getNextDependent(obj)

    while dependent is not None:

        yield dependent
        dependent = getNextDependent(dependent)


def trace(obj):
    """
    Returns a generator that yields the dependents leading to the given object.

    :type obj: pymxs.MXSWrapperBase
    :rtype: iter
    """

    # Check if object is valid
    #
    if not pymxs.runtime.isValidObj(obj):

        return

    # Iterate through dependents in reverse
    #
    for dependent in reversed(list(iterDependents(obj))):

        yield dependent

    yield obj  # Don't forget to yield self!


def exprForMaxObject(obj):
    """
    Returns a path to the supplied Max object.

    :type obj: pymxs.MXSWrapperBase
    :rtype: str
    """

    # Check if this is a valid max object
    #
    if not pymxs.runtime.isValidObj(obj):

        return ''

    # Evaluate dependents
    #
    dependents = list(trace(obj))
    numDependents = len(dependents)

    if numDependents == 1:

        return ''

    # Iterate through generator
    #
    expression = ''

    for (i, dependent) in enumerate(dependents):

        # Evaluate dependent type
        #
        if pymxs.runtime.isValidNode(dependent):

            expression += nodeutils.getFullPathTo(dependent)

        elif pymxs.runtime.isKindOf(dependent, pymxs.runtime.SubAnim):

            subAnimName = stringutils.slugify(dependent.name, whitespace='_', illegal='_')
            expression += '[#{subAnimName}]'.format(subAnimName=subAnimName)

        elif controllerutils.isValidController(dependent):

            expression += '.controller'

        elif pymxs.runtime.isKindOf(dependent, pymxs.runtime.AttributeDef):

            expression += '.{definitionName}'.format(definitionName=dependent.name)

        elif pymxs.runtime.isValidObj(dependent) and pymxs.runtime.isKindOf(dependents[i - 1], pymxs.runtime.SubAnim):

            expression += '.value'

        else:

            continue

    return expression
