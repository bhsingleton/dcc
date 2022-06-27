import pymxs

from . import nodeutils
from ...python import stringutils
from ...generators.inclusiverange import inclusiveRange

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def iterBases(cls):
    """
    Returns a generator that yields base classes from the supplied Max class.

    :type cls: pymxs.MXSWrapperBase
    :rtype: iter
    """

    # Check if this is a valid class
    #
    if not isinstance(cls, pymxs.MXSWrapperBase):

        return

    # Iterate until we hit the Value class
    #
    while cls != pymxs.runtime.Value:

        cls = pymxs.runtime.classOf(cls)
        yield cls


def bases(cls):
    """
    Returns a list of base classes from the supplied Max class.

    :type cls: pymxs.MXSWrapperBase
    :rtype: iter
    """

    return list(iterBases(cls))


def isKindOf(obj, cls):
    """
    Evaluates if the supplied object is derived from the given Max class.
    There are several improvements made to this method vs the builtin pymxs function:
        Support for tuples with Max classes.
        Literal Sub-Anim comparison rather than the implied value comparisons.

    :type obj: Any
    :type cls: Union[pymxs.MXSWrapperBase, Tuple[pymxs.MXSWrapperBase]]
    :rtype: bool
    """

    if isinstance(cls, tuple):

        return any([isKindOf(obj, x) for x in cls])

    elif pymxs.runtime.isKindOf(obj, pymxs.runtime.SubAnim):

        return pymxs.runtime.classOf(obj) == cls

    else:

        return pymxs.runtime.isKindOf(obj, cls)


def isParamBlock2Based(obj):
    """
    Evaluates if the supplied object is ParamBlock2 based.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    cls = pymxs.runtime.classOf(obj)
    return getattr(cls, 'ispb2based', False)


def isArray(obj):
    """
    Evaluates if the supplied Max-object represents an array.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.isProperty(obj, 'count')


def iterClassesByPattern(search, superOnly=False):
    """
    Returns a generator that yields MXS classes by search pattern.
    Apropos patterns should consist of the following: {variableName}:{className}
    For example: *XYZ:MAXClass, which returns XYZ controller classes.

    :type search: str
    :type superOnly: bool
    :rtype: iter
    """

    # Initialize string-stream for apropos
    #
    stringStream = pymxs.runtime.StringStream('')
    className = 'MAXSuperClass' if superOnly else 'MAXClass'
    pattern = '{search}:{className}'.format(search=search, className=className)

    pymxs.runtime.apropos(pattern, implicitWild=False, to=stringStream)

    # Iterate through string stream
    #
    pymxs.runtime.seek(stringStream, 0)

    while not pymxs.runtime.eof(stringStream):

        line = pymxs.runtime.readLine(stringStream)
        name = line.split(' ', 1)[0]
        cls = getattr(pymxs.runtime, name)

        yield name, cls


def getAssociatedNode(obj):
    """
    Returns the node associated with the given Max object.

    :type obj: pymxs.MXSWrapperBase
    :rtype: Union[pymxs.MXSWrapperBase, None]
    """

    return pymxs.runtime.refs.dependentNodes(obj, firstOnly=True)


def iterDependents(obj, ignore=None):
    """
    Returns a generator that yields dependents from the given object.
    Any optional list of MXS classes can supplied to ignore specific dependents.

    :type obj: pymxs.MXSWrapperBase
    :type ignore: Tuple[pymxs.MXSWrapperBase]
    :rtype: iter
    """

    # Iterate through dependents
    #
    dependents = pymxs.runtime.refs.dependents(obj)

    for dependent in dependents:

        # Check if dependent should be ignored
        #
        if not isKindOf(dependent, ignore):

            yield dependent

        else:

            continue


def getAssociatedSubAnim(obj, ignore=None):
    """
    Returns the sub-anim associated with the given Max object.

    :type obj: pymxs.MXSWrapperBase
    :type ignore: Tuple[pymxs.MXSWrapperBase]
    :rtype: Union[pymxs.MXSWrapperBase, None]
    """

    # Evaluate which dependent the object is derived from
    # Dependents are returned from closest to furthest away!
    #
    for dependent in iterDependents(obj, ignore=ignore):

        # Check if this is a valid object
        #
        if not pymxs.runtime.isValidObj(dependent):

            continue

        # Iterate through sub-anims
        #
        numSubs = getattr(dependent, 'numSubs', 0)

        for i in inclusiveRange(1, numSubs, 1):

            # Check if sub-anim contains object
            #
            subAnim = pymxs.runtime.getSubAnim(dependent, i)

            if subAnim.controller == obj or subAnim.value == obj:

                return subAnim

            else:

                continue

    return None


def findParamBlockSource(paramBlock):
    """
    Returns the attribute definition associated with the supplied parameter block.
    Not all parameter blocks have accessible definitions!

    :type paramBlock: pymxs.MXSWrapperBase
    :rtype: Union[pymxs.MXSWrapperBase, None]
    """

    # Iterate through dependents
    #
    dependents = pymxs.runtime.refs.dependents(paramBlock)

    for dependent in dependents:

        # Evaluate dependent type
        #
        if isKindOf(dependent, pymxs.runtime.AttributeDef) or isParamBlock2Based(dependent):

            return dependent

        else:

            continue

    return None


def getNextLogicalDependent(obj):
    """
    Returns the next logical up-stream dependent.
    This method will only consider sub-anims or custom attributes.

    :type obj: pymxs.MXSWrapperBase
    :rtype: pymxs.MXSWrapperBase
    """

    # Evaluate Max-object type
    #
    if pymxs.runtime.isvalidNode(obj) or isKindOf(obj, pymxs.runtime.Scene):

        return  # Nothing left to return!

    elif isKindOf(obj, pymxs.runtime.SubAnim):

        return obj.parent

    elif isKindOf(obj, pymxs.runtime.Material):

        return getAssociatedSubAnim(obj, ignore=(pymxs.runtime.ParamBlock2, pymxs.runtime.SMENodeAttr, pymxs.runtime.Node, pymxs.runtime.MAXTVNode))

    elif isKindOf(obj, pymxs.runtime.ParamBlock2):

        # Find parameter-block source
        # Otherwise default to associated sub-anim
        #
        source = findParamBlockSource(obj)

        if source is not None:

            return source

        else:

            return getAssociatedSubAnim(obj)

    elif isKindOf(obj, pymxs.runtime.AttributeDef):

        return pymxs.runtime.CustAttributes.getOwner(obj)

    elif pymxs.runtime.isValidObj(obj):

        return getAssociatedSubAnim(obj)

    else:

        return


def iterLogicalDependents(obj):
    """
    Returns a generator that yields the upstream dependents from the given object.

    :type obj: pymxs.MXSWrapperBase
    :rtype: iter
    """

    dependent = getNextLogicalDependent(obj)

    while dependent is not None:

        yield dependent
        dependent = getNextLogicalDependent(dependent)


def traceLogicalDependents(obj):
    """
    Returns a generator that yields the dependents leading to the given object.

    :type obj: pymxs.MXSWrapperBase
    :rtype: iter
    """

    # Iterate through dependents in reverse
    #
    for dependent in reversed(list(iterLogicalDependents(obj))):

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

        return

    # Iterate through dependency trace
    #
    dependents = list(traceLogicalDependents(obj))
    expression = ''

    for (i, dependent) in enumerate(dependents):

        # Evaluate dependent type
        #
        if pymxs.runtime.isValidNode(dependent):

            expression += nodeutils.getFullPathTo(dependent)

        elif pymxs.runtime.isKindOf(dependent, pymxs.runtime.Scene):

            expression += '::rootScene'

        elif pymxs.runtime.isKindOf(dependent, pymxs.runtime.SubAnim):

            subAnimName = stringutils.slugify(dependent.name, whitespace='_', illegal='_')
            expression += '[#{subAnimName}]'.format(subAnimName=subAnimName)

        elif pymxs.runtime.isController(dependent):

            expression += '.controller'

        elif pymxs.runtime.isKindOf(dependent, pymxs.runtime.AttributeDef):

            expression += '.{definitionName}'.format(definitionName=dependent.name)

        elif pymxs.runtime.isValidObj(dependent) and pymxs.runtime.isKindOf(dependents[i - 1], pymxs.runtime.SubAnim):

            expression += '.value'

        else:

            continue

    return expression
