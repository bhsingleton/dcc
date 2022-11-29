import pymxs

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

        return iter([])

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
        1. Support for tuples of Max classes.
        3. Support for python types.
        2. Literal Sub-Anim comparison rather than an implied value comparison.

    :type obj: Any
    :type cls: Union[pymxs.MXSWrapperBase, Tuple[pymxs.MXSWrapperBase]]
    :rtype: bool
    """

    # Evaluate supplied class
    #
    if isinstance(cls, (tuple, list)):

        # Evaluate all items
        #
        return any([isKindOf(obj, x) for x in cls])

    else:

        # Evaluate if this is a maxscript type
        # Otherwise, `isKindOf(1, int) == False` can happen in python!
        #
        if isinstance(cls, pymxs.MXSWrapperBase):

            # Check if this is a sub-anim
            # Otherwise, MXS will evaluate the sub-anim value rather than the object itself!
            #
            if pymxs.runtime.isKindOf(obj, pymxs.runtime.SubAnim):

                return pymxs.runtime.classOf(obj) == cls

            else:

                return pymxs.runtime.isKindOf(obj, cls)

        else:

            return isinstance(obj, cls)


def isValidWrapper(obj):
    """
    Evaluates if the supplied object is a valid Max wrapper.

    :type obj: Any
    :rtype: bool
    """

    return pymxs.runtime.isValidObj(obj) and pymxs.runtime.MAXWrapper in bases(obj)


def isParamBlock2Based(obj):
    """
    Evaluates if the supplied object is ParamBlock2 based.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    cls = pymxs.runtime.classOf(obj)
    return getattr(cls, 'ispb2based', False)


def iterSubAnims(obj):
    """
    Returns a generator that yields sub-anims from the supplied Max object.

    :type obj: pymxs.MXSWrapperBase
    :rtype: iter
    """

    # Iterate through sub-anims
    #
    numSubs = getattr(obj, 'numSubs', 0)

    for i in inclusiveRange(1, numSubs, 1):

        subAnim = pymxs.runtime.getSubAnim(obj, i)
        yield subAnim


def isSubAnimNameUnique(subAnim):
    """
    Evaluates if the supplied sub-anim's name is unique.

    :type subAnim: pymxs.MXSWrapperBase
    :rtype: bool
    """

    obj = subAnim.parent
    name = subAnim.name

    return not any([x.name == name and x != subAnim for x in iterSubAnims(obj)])


def isArray(obj):
    """
    Evaluates if the supplied Max-object represents an array.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    return pymxs.runtime.isProperty(obj, 'count')


def hasValidExpression(obj):
    """
    Evaluates if the supplied object has a valid expression.

    :type obj: pymxs.MXSWrapperBase
    :rtype: bool
    """

    try:

        expression = pymxs.runtime.exprForMaxObject(obj)
        result = pymxs.runtime.execute(expression)

        return obj == result

    except RuntimeError as error:

        return False


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
    Any optional list of MXS classes can be used to ignore specific dependents.

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
        for subAnim in iterSubAnims(dependent):

            # Check if sub-anim contains object
            #
            if subAnim.controller == obj or subAnim.value == obj:

                return subAnim

            else:

                continue

    return None


def findAssociatedAttributeDef(paramBlock):
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
        if isKindOf(dependent, pymxs.runtime.AttributeDef) and isParamBlock2Based(dependent):

            return dependent

        else:

            continue

    return None
