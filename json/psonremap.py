import os
import json

from dataclasses import dataclass, field

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class PSONRemap(object):
    """
    Base class used for remapping PSON class changes.
    """

    # region Fields
    name: str = ''
    nameChange: str = ''
    path: str = ''
    pathChange: str = ''
    properties: dict = field(default_factory=dict)
    # endregion


def iterRemaps():
    """
    Returns the remap objects from the remap directory.

    :rtype: Iterator[Remap]
    """

    # Iterate through directory
    #
    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'remaps')
    filenames = os.listdir(directory)

    for filename in filenames:

        # Evaluate file extension
        #
        filePath = os.path.join(directory, filename)

        if not filePath.endswith('.json'):

            continue

        # Try and load file contents
        #
        try:

            # Load JSON file
            #
            objs = None

            with open(filePath, mode='r') as jsonFile:

                objs = json.load(jsonFile)

            # Yield remap objects
            #
            for obj in objs:

                yield PSONRemap(**obj)

        except json.JSONDecodeError as error:

            log.warning(error)
            continue
