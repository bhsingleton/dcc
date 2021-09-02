import os
import json

from six import string_types

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def getMirrorTable():
    """
    Method used to retrieve all of the available side names.
    This dictionary can be used to resolve any form of mirroring.

    :rtype: dict[str:str]
    """

    # Concatenate file path
    #
    filePath = os.path.join(os.path.dirname(__file__), r'sides.json')

    with open(filePath, 'r') as jsonFile:

        return json.load(jsonFile)


def mirrorName(name):
    """
    Method used to mirror the supplied name based on the sides dictionary.
    This dictionary can be located alongside this module.

    :type name: str
    :rtype: str
    """

    # Check value type
    #
    if not isinstance(name, string_types):

        raise TypeError('mirrorName() expects a str (%s given)!' % type(name).__name__)

    # Split string using underscores
    #
    strings = name.split('_')
    numStrings = len(strings)

    # Iterate through strings
    #
    sides = getMirrorTable()
    newStrings = [None] * numStrings

    for i in range(numStrings):

        # Check if token is in dictionary
        #
        string = strings[i]
        opposite = sides.get(string.lower(), None)

        if opposite is None:

            newStrings[i] = string
            continue

        # Match casing
        #
        casings = [x.isupper() for x in string]
        newStrings[i] = ''.join([char.upper() if case else char.lower() for char, case in zip(opposite, casings)])

    return '_'.join(newStrings)
