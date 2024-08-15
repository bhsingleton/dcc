from copy import deepcopy
from itertools import chain
from . import floatmath

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def clamp(value, minValue=0.0, maxValue=1.0):
    """
    Clamps the supplied value to the specified range.

    :type value: Union[int, float]
    :type minValue: Union[int, float]
    :type maxValue: Union[int, float]
    :rtype: Union[int, float]
    """

    return floatmath.clamp(value, minValue, maxValue)


def setWeights(weights, target, source, amount, **kwargs):
    """
    Sets the supplied target ID to the specified amount while preserving normalization.

    :type weights: Dict[int, float]
    :type target: int
    :type source: List[int]
    :type amount: float
    :key falloff: float
    :key maxInfluences: int
    :rtype: Dict[int, float]
    """

    # Check weights type
    #
    if not isinstance(weights, dict):

        raise TypeError(f'setWeights() expects a dict ({type(weights).__name__} given)!')

    # Check source and target influences
    #
    if not isinstance(target, int) or not isinstance(source, list):

        raise TypeError('setWeights() expects a valid target and source influences!')

    # Check amount type
    #
    if not isinstance(amount, float):

        raise TypeError(f'setWeights() expects a valid amount ({type(amount).__name__} given)!')

    # Copy weights to manipulate
    #
    newWeights = deepcopy(weights)

    falloff = kwargs.get('falloff', 1.0)
    softAmount = clamp(amount) * clamp(falloff)
    total = sum([weights.get(x, 0.0) for x in source])

    log.debug(f'Weights available to redistribute: {total}')

    # Check if influence exists on vertex
    #
    influenceIds = newWeights.keys()
    numInfluences = len(influenceIds)

    maxInfluences = kwargs.get('maxInfluences', len(weights) + 1)

    if (target in influenceIds) or (target not in influenceIds and numInfluences < maxInfluences):

        # Determine redistribution method:
        # If amount is less than current then give those weights back to the source list
        # If amount is greater than current then take weights from the source list
        #
        current = newWeights.get(target, 0.0)

        if softAmount < current and 0.0 < total:

            # Redistribute target weight to source influences
            #
            diff = current - softAmount

            for (influenceId, weight) in newWeights.items():

                # Check if influence is from source
                #
                if influenceId in source:

                    # Apply percentage of difference to influence
                    #
                    percent = weight / total
                    newWeight = weight + (diff * percent)

                    newWeights[influenceId] = newWeight

                else:

                    continue

            # Set target to amount
            #
            newWeights[target] = current - diff

        elif softAmount > current and 0.0 < total:

            # Make sure amount has not exceeded total
            #
            diff = softAmount - current

            if diff >= total:

                log.debug('Insufficient weights to pull from, clamping amount to: %s' % total)
                diff = total

            # Redistribute source weights to target influences
            #
            for (influenceId, weight) in newWeights.items():

                # Check if influence is from source
                #
                if influenceId in source:

                    # Reduce influence based on percentage of difference
                    #
                    percent = weight / total
                    newWeight = weight - (diff * percent)

                    newWeights[influenceId] = newWeight

                else:

                    continue

            # Set target to accumulated amount
            #
            newWeights[target] = current + diff

        else:

            pass

    elif target not in influenceIds and numInfluences >= maxInfluences:

        # Check if all influences are being replaced
        #
        if floatmath.isClose(amount, total, abs_tol=1e-06):

            newWeights = {target: 1.0}

        elif amount == 0.0:

            log.debug('No weights available to redistribute!')

        else:

            log.warning('Cannot exceed max influences!')

    else:

        raise TypeError('setWeights() Unable to manipulate vertex weights from supplied arguments!')

    # Return updated vertex weights
    #
    return newWeights


def scaleWeights(weights, target, source, percent, **kwargs):
    """
    Scales the supplied target ID to the specified amount while preserving normalization.

    :type weights: Dict[int, float]
    :type target: int
    :type source: List[int]
    :type percent: float
    :key falloff: float
    :key maxInfluences: int
    :rtype: Dict[int, float]
    """

    # Get amount to redistribute
    #
    falloff = kwargs.get('falloff', 1.0)
    current = weights.get(target, 0.0)

    amount = current + sum([(weights.get(influenceId, 0.0) * (percent * falloff)) for influenceId in source])

    # Set vertex weight
    #
    log.debug(f'Changing influence ID: {target}, from {current} to {amount}')
    return setWeights(weights, target, source, amount, **kwargs)


def incrementWeights(weights, target, source, increment, **kwargs):
    """
    Increments the supplied target ID to the specified amount while preserving normalization.

    :type weights: Dict[int, float]
    :type target: int
    :type source: List[int]
    :type increment: float
    :key falloff: float
    :key maxInfluences: int
    :rtype: Dict[int, float]
    """

    # Get amount to redistribute
    #
    falloff = kwargs.get('falloff', 1.0)
    current = weights.get(target, 0.0)

    amount = current + (increment * falloff)

    # Set vertex weight
    #
    log.debug(f'Changing influence ID: {target}, from {current} to {amount}')
    return setWeights(weights, target, source, amount, **kwargs)


def removeZeroWeights(weights):
    """
    Removes any zeroes from the supplied weights.

    :type weights: Dict[int, float]
    :rtype: Dict[int, float]
    """

    return {influenceId: weight for (influenceId, weight) in weights.items() if not floatmath.isClose(0.0, weight)}


def pruneWeights(weights, **kwargs):
    """
    Caps the supplied vertex weights to meet the maximum number of weighted influences.

    :type weights: Dict[int, float]
    :key tolerance: float
    :key maxInfluences: int
    :rtype: Dict[int, float]
    """

    # Check value type
    #
    if not isinstance(weights, dict):

        raise TypeError('pruneWeights() expects a dict (%s given)!' % type(weights).__name__)

    # Prune weights
    #
    tolerance = kwargs.get('tolerance', 1e-3)
    prunedWeights = {influenceId: influenceWeight for (influenceId, influenceWeight) in weights.items() if influenceWeight >= tolerance}

    return normalizeWeights(prunedWeights, **kwargs)


def capWeights(weights, **kwargs):
    """
    Caps the supplied vertex weights to meet the maximum number of weighted influences.

    :type weights: Dict[int, float]
    :key maxInfluences: int
    :rtype: Dict[int, float]
    """

    # Check value type
    #
    if not isinstance(weights, dict):

        raise TypeError('capWeights() expects a dict (%s given)!' % type(weights).__name__)

    # Check if any influences have dropped below limit
    #
    for (influenceId, weight) in weights.items():

        # Check if influence weight is below threshold
        #
        if floatmath.isClose(0.0, weight):

            weights[influenceId] = 0.0

        else:

            log.debug('Skipping influence ID: %s' % influenceId)

    # Check if influences have exceeded max allowances
    #
    numInfluences = len(weights)
    maxInfluences = kwargs.get('maxInfluences', numInfluences)

    if numInfluences > maxInfluences:

        # Order influences from lowest to highest
        #
        orderedInfluences = sorted(weights, key=weights.get, reverse=False)

        # Replace surplus influences with zero values
        #
        diff = numInfluences - maxInfluences

        for i in range(diff):

            influenceId = orderedInfluences[i]
            weights[influenceId] = 0.0

    else:

        log.debug('Vertex weights have not exceeded max influences.')

    # Return dictionary changes
    #
    return weights


def isNormalized(weights, **kwargs):
    """
    Evaluates if the supplied weights have been normalized.

    :type weights: Dict[int, float]
    :rtype: bool
    """

    # Check value type
    #
    if not isinstance(weights, dict):

        raise TypeError('isNormalized() expects a dict (%s given)!' % type(weights).__name__)

    # Check influence weight total
    #
    total = sum([weight for (influenceId, weight) in weights.items()])
    log.debug('Supplied influence weights equal %s.' % total)

    return floatmath.isClose(1.0, total)


def normalizeWeights(weights, **kwargs):
    """
    Normalizes the supplied vertex weights.

    :type weights: Dict[int, float]
    :key maxInfluences: int
    :rtype: Dict[int, float]
    """

    # Check value type
    #
    if not isinstance(weights, dict):

        raise TypeError('normalizeWeights() expects a dict (%s given)!' % type(weights).__name__)

    # Check if influences should be pruned
    #
    numInfluences = len(weights)
    maxInfluences = kwargs.get('maxInfluences', numInfluences)

    if numInfluences > maxInfluences:

        weights = capWeights(weights, **kwargs)

    # Check if weights have already been normalized
    #
    normalized = isNormalized(weights, **kwargs)

    if normalized:

        log.debug('Vertex weights have already been normalized.')
        return weights

    # Check if weights can be normalized
    #
    total = sum(weights.values())

    if total == 0.0:

        raise TypeError('Cannot normalize influences from zero weights!')

    # Scale weights to equal one
    #
    scale = 1.0 / total

    for (influenceId, weight) in weights.items():

        normalizedWeight = (weight * scale)
        weights[influenceId] = normalizedWeight

        log.debug(
            'Normalizing influence ID: {index}, from {weight} to {normalizedWeight}'.format(
                index=influenceId,
                weight=weight,
                normalizedWeight=normalizedWeight
            )
        )

    return weights


def mergeWeights(*args):
    """
    Combines any number of dictionaries together with null values.

    :type args: Union[dict, List[dict]]
    :rtype: dict
    """

    influenceIds = set(chain(*[arg.keys() for arg in args]))
    return dict.fromkeys(influenceIds, 0.0)


def averageWeights(*args, **kwargs):
    """
    Averages the supplied vertex weights.
    By default, maintain max influences is enabled.

    :key maxInfluences: int
    :rtype: Dict[int, float]
    """

    # Iterate through vertices
    #
    average = {}

    for arg in args:

        # Check argument type
        #
        if not isinstance(arg, dict):

            continue

        # Iterate through copied weights
        #
        for (influenceId, vertexWeight) in arg.items():

            # Check if influence key already exists
            #
            if influenceId not in average:

                average[influenceId] = arg[influenceId]

            else:

                average[influenceId] += arg[influenceId]

    # Return normalized result
    #
    return normalizeWeights(average, **kwargs)


def weightedAverageWeights(startWeights, endWeights, **kwargs):
    """
    Averages supplied vertex weights based on a normalized percentage.

    :type startWeights: dict
    :type endWeights: dict
    :key percent: float
    :key maxInfluences: int
    :rtype: Dict[int, float]
    """

    # Check percentage type
    #
    percent = kwargs.get('percent', 0.5)

    if not isinstance(percent, (int, float)):

        raise TypeError('weightedAverageWeights() expects a float (%s given)!' % type(percent).__name__)

    # Merge dictionary keys using null values
    #
    weights = mergeWeights(startWeights, endWeights)
    influenceIds = weights.keys()

    for influenceId in influenceIds:

        # Get weight values
        #
        startWeight = startWeights.get(influenceId, 0.0)
        endWeight = endWeights.get(influenceId, 0.0)

        # Average weights
        #
        weight = (startWeight * (1.0 - percent)) + (endWeight * percent)
        weights[influenceId] = weight

    # Return normalized weights
    #
    return normalizeWeights(weights, **kwargs)
