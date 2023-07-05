import os
import re
import json

from enum import Enum, IntEnum
from six import string_types, integer_types
from six.moves import configparser
from ..python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def getSideMappings():
    """
    Returns a map of all the possible sides and their opposites.

    :rtype: Dict[str, str]
    """

    # Concatenate file path
    #
    filePath = os.path.join(os.path.dirname(__file__), r'sides.json')

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

    directory = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(directory, 'configs', 'default.config')


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


def getAbbreviation(typeName):
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
    if not __config__.has_section('abbreviations'):

        raise TypeError('getAbbreviation() expects a naming configuration with an abbreviations section!')

    # Check if type name exists in section
    #
    abbreviation = None

    if __config__.has_option('abbreviations', typeName):

        # Get option and capitalize
        #
        abbreviation = __config__.get('abbreviations', typeName)

    else:

        abbreviation = typeName

    # Check if abbreviation should be titleized
    #
    titleize = __config__.getboolean('pattern', 'titleize')

    if titleize:

        return abbreviation.upper()

    else:

        return abbreviation.lower()


def applyCasing(name):
    """
    Enforces the casing setting from the current configuration.

    :type name: str
    :rtype: str
    """

    global __config__

    # Evaluate which casing style to use
    #
    titleize = __config__.getboolean('pattern', 'titleize')

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


def applyPadding(number, padding):
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

            return applyPadding(int(number), padding)

        else:

            return number

    else:

        raise TypeError('applyPadding() expects either an int or float (%s given)!' % type(number).__name__)


def expandSide(side):
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

        sideName = enumName

    # Check if side should be titleized
    #
    titleize = __config__.getboolean('pattern', 'titleize')

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


def formatName(comp=None, id=None, desc=None, type=None, side=None, index=None):
    """
    Concatenates a name based on the current configuration file.

    :type comp: str
    :type id: Union[int, str]
    :type desc: str
    :type index: str
    :type type: str
    :type side: IntEnum
    :rtype: str
    """

    global __config__

    # Get configuration section
    #
    pattern = __config__.get('pattern', 'name')
    idPadding = __config__.getint('pattern', 'id_padding')
    indexPadding = __config__.getint('pattern', 'index_padding')

    comp = applyCasing(comp)
    desc = applyCasing(desc)
    abbreviation = getAbbreviation(type)
    side = expandSide(side)
    id = applyPadding(id, idPadding)
    index = applyPadding(index, indexPadding)

    name = pattern.format(
        comp=comp,
        desc=desc,
        type=abbreviation,
        side=side,
        id=id,
        index=index
    )

    return removeDuplicateUnderscores(name)


__config__ = loadConfiguration()  # Initialize default configuration
