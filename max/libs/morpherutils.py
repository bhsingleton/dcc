import pymxs

from dcc.generators.inclusiverange import inclusiveRange
from dcc.max.decorators.commandpaneloverride import commandPanelOverride

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@commandPanelOverride(mode='modify', select=0)
def iterTargets(morpher):
    """
    Returns a generator that yields the active vertex selection from the supplied skin.

    :type morpher: pymxs.MXSWrapperBase
    :rtype: iter
    """

    # Iterate through channels
    #
    numChannels = pymxs.runtime.WM3_NumberOfChannels(morpher)

    for i in inclusiveRange(1, numChannels, 1):

        # Check if channel has valid target
        #
        hasTarget = pymxs.runtime.WM3_MC_HasTarget(morpher, i)

        if not hasTarget:

            continue

        # Get target properties
        #
        name = pymxs.runtime.WM3_MC_GetName(morpher, i)
        target = pymxs.runtime.WM3_MC_GetTarget(morpher, i)
        weight = pymxs.runtime.WM3_MC_GetValue(morpher, i)

        yield name, target, weight
