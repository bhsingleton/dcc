import os
import re
import json

from enum import Enum, IntEnum
from ..python import stringutils
from ..vendor.six import string_types, integer_types
from ..vendor.six.moves import configparser

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__location__ = os.path.dirname(os.path.abspath(__file__))


def getSideMappings():
    """
    Returns a map of all the possible sides and their opposites.

    :rtype: Dict[str, str]
    """

    # Concatenate file path
    #
    filePath = os.path.join(__location__, r'sides.json')

    with open(filePath, 'r') as jsonFile:

        return json.load(jsonFile)


def mirrorName(name):
    """
    Mirrors the supplied name based on the internal side mappings.
    This map can be located inside the `sides.json` file next to this module.

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
    sides = getSideMappings()
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


def getDefaultConfiguration():
    """
    Returns the default naming configuration.

    :rtype: str
    """

    return os.path.join(__location__, 'configs', 'default.config')


def changeConfiguration(*args):
    """
    Updates the internal naming configuration.

    :rtype: bool
    """

    global __config__

    # Check if file exists
    #
    filePath = args[0] if len(args) == 1 else getDefaultConfiguration()

    if os.path.exists(filePath):

        log.info('Loading configuration: %s' % filePath)
        __config__ = loadConfiguration(filePath)

        return True

    else:

        return False


def loadConfiguration(*args):
    """
    Returns a configuration parser from the supplied file path.
    If no path is supplied then the default configuration file is used instead.

    :rtype: configparser.ConfigParser
    """

    # Check if a path was supplied
    #
    filePath = args[0] if len(args) == 1 else getDefaultConfiguration()

    if os.path.exists(filePath):

        # Read configuration file
        #
        parser = configparser.SafeConfigParser()
        parser.read(filePath)

        return parser

    else:

        raise TypeError('loadConfiguration() cannot locate configuration: %s' % filePath)


def getAcronym(typeName):
    """
    Returns an abbreviation for the supplied type name using the current configuration.

    :type typeName: str
    :rtype: str
    """

    global __config__

    # Check if type name is valid
    #
    if stringutils.isNullOrEmpty(typeName):

        return ''

    # Check if abbreviations section exists
    #
    if not __config__.has_section('acronyms'):

        raise TypeError('getAcronym() expects a naming configuration with an abbreviations section!')

    # Check if type name exists in section
    #
    acronym = None

    if __config__.has_option('acronyms', typeName):

        # Get option and capitalize
        #
        acronym = __config__.get('acronyms', typeName)

    else:

        acronym = typeName

    # Check if abbreviation should be titleized
    #
    titleize = __config__.getboolean('format', 'titleize')

    if titleize:

        return acronym.upper()

    else:

        return acronym.lower()


def findSide(name):
    """
    Returns the side from the supplied name.
    The side correlates to the key name from the sides section in the config file!

    :type name: str
    :rtype: str
    """

    global __config__

    # Create reverse lookup map
    #
    sides = {value: key for (key, value) in __config__['sides'].items()}
    strings = name.split('_')

    for string in strings:

        side = sides.get(string.lower(), None)
        hasSide = side is not None

        if hasSide:

            return side

    return ''


def caseify(name):
    """
    Enforces the casing setting from the current configuration.

    :type name: str
    :rtype: str
    """

    global __config__

    # Evaluate which casing style to use
    #
    titleize = __config__.getboolean('format', 'titleize')

    if titleize:

        # Check if there are any characters
        #
        if not stringutils.isNullOrEmpty(name):

            return stringutils.pascalize(name)

        else:

            return ''

    else:

        # Check if there are any characters
        #
        if not stringutils.isNullOrEmpty(name):

            return stringutils.camelize(name)

        else:

            return ''


def padify(number, padding):
    """
    Converts the supplied number into a string with the specified padding.

    :type number: Union[int, float]
    :type padding: int
    :rtype: str
    """

    # Check if number is valid
    #
    if stringutils.isNullOrEmpty(number):

        return ''

    # Evaluate number type
    #
    if isinstance(number, integer_types):

        # Ensure zeroes
        #
        return str(number).zfill(padding)

    elif isinstance(number, float):

        # Round number to number of digits
        #
        return str(round(number, padding))

    elif isinstance(number, string_types):

        # Check if string is a number
        #
        if stringutils.isNumber(number):

            return padify(int(number), padding)

        else:

            return number

    else:

        raise TypeError('applyPadding() expects either an int or float (%s given)!' % type(number).__name__)


def sideify(side):
    """
    Returns the name associated with the supplied side enumerator.

    :type side: IntEnum
    :rtype: str
    """

    global __config__

    # Redundancy check
    #
    if not isinstance(side, (Enum, IntEnum)):

        return ''

    # Check if side exists
    #
    enumName = side.name.lower()
    sideName = None

    if __config__.has_option('sides', enumName):

        sideName = __config__.get('sides', enumName)

    else:

        return ''

    # Check if side should be titleized
    #
    titleize = __config__.getboolean('format', 'titleize')

    if titleize:

        return sideName.upper()

    else:

        return sideName.lower()


def removeDuplicateUnderscores(name):
    """
    Remove any duplicate underscores.

    :param name: String name.
    :return: String
    """

    # Remove any leading/trailing underscores
    #
    name = name.lstrip('_+')
    name = name.rstrip('_+')

    return re.sub('_+', '_', name)


def formatName(name=None, id=None, subname=None, kinemat=None, index=None, type=None, side=None):
    """
    Concatenates a name based on the current configuration file.

    :type name: str
    :type id: Union[int, str]
    :type subname: str
    :type index: str
    :type type: str
    :type side: IntEnum
    :rtype: str
    """

    global __config__

    # Get configuration section
    #
    nameFormat = __config__.get('format', 'name')
    useAcronyms = __config__.getboolean('format', 'use_acronyms')
    idPadding = __config__.getint('format', 'id_padding')
    indexPadding = __config__.getint('format', 'index_padding')

    name = caseify(name)
    subname = caseify(subname)
    kinemat = caseify(kinemat)
    type = getAcronym(type) if useAcronyms else caseify(type)
    side = sideify(side)
    id = padify(id, idPadding)
    index = padify(index, indexPadding)

    newName = nameFormat.format(
        name=name,
        subname=subname,
        kinemat=kinemat,
        type=type,
        side=side,
        id=id,
        index=index
    )

    return removeDuplicateUnderscores(newName)


__config__ = loadConfiguration()  # Initialize default configuration
