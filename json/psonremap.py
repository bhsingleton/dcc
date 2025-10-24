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


def loadRemaps(*paths):
    """
    Loads any PSON remaps from the specified directory.

    :type paths: Union[str, List[str]]
    :rtype: List[PSONRemap]
    """

    # Iterate through paths
    #
    remaps = []

    for path in paths:

        # Evaluate path type
        #
        if os.path.isdir(path):

            # Search directory for remap definitions
            #
            filePaths = [os.path.join(path, filename) for filename in os.listdir(path)]
            filteredPaths = tuple(filter(os.path.isfile, filePaths))

            remaps.extend(loadRemaps(*filteredPaths))

        elif os.path.isfile(path):

            # Check if file is valid
            #
            if not path.endswith('.json'):

                log.warning(f'Skipping invalid JSON file: {path}')
                continue

            # Try and load JSON file
            #
            try:

                objs = None

                with open(path, mode='r') as jsonFile:

                    objs = json.load(jsonFile)

                # Yield remap objects
                #
                for obj in objs:

                    remap = PSONRemap(**obj)
                    remaps.append(remap)

            except json.JSONDecodeError as error:

                log.warning(error)
                continue

        else:

            log.warning(f'Skipping invalid path: {path}')
            continue

    return remaps
