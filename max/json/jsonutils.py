import json
import pymxs

from . import mxsobjectparser

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def saveScene(filePath):
    """
    Saves the scene nodes to the specified path.

    :type filePath: str
    :rtype: None
    """

    # Open file and overwrite contents
    #
    with open(filePath, 'w') as jsonFile:

        json.dump(
            pymxs.runtime.rootScene,
            jsonFile,
            cls=mxsobjectparser.MXSObjectEncoder,
            indent=4
        )

    log.info('Saving scene to: %s' % filePath)
