import pymxs
import json

from datetime import datetime
from dcc.max.json import mxsobjectparser

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def saveAnimation(filePath, nodes):
    """
    Exports all of the animation from the supplied nodes to the specified path.

    :type filePath: str
    :type nodes: List[pymxs.runtime.Node]
    :rtype: None
    """

    now = datetime.now()

    document = {
        'filename': pymxs.runtime.maxFilename,
        'date': now.strftime('%m/%d/%Y'),
        'time': now.strftime('%H:%M:%S'),
        'frameRate': pymxs.runtime.frameRate,
        'ticksPerFrame': pymxs.runtime.ticksPerFrame,
        'nodes': nodes
    }

    with open(filePath, 'wt') as jsonFile:

        json.dump(document, jsonFile, indent=4, cls=mxsobjectparser.MXSObjectEncoder)
        log.info('Animation saved to: %s' % filePath)


def loadAnimation(filePath, nodes):
    """
    Imports all of the animation to the supplied nodes from the specified path.

    :type filePath: str
    :type nodes: List[pymxs.runtime.Node]
    :rtype: None
    """

    with open(filePath, 'r') as jsonFile:

        return json.load(jsonFile, cls=mxsobjectparser.MXSObjectDecoder)
