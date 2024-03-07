import re
import ast
import unicodedata

from six import string_types
from six.moves import collections_abc

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__title__ = re.compile(r'([A-Z]?[a-z0-9]*)')
__number__ = re.compile(r'(?:[+-])?(?:[0-9])+(?:\.{1}[0-9]+)?(?:e{1}\-{1}[0-9]+)?')
__states__ = ('true', 'on', 'yes')


def isNullOrEmpty(value):
    """
    Evaluates if the supplied value is null or empty.

    :type value: Any
    :rtype: bool
    """

    if isinstance(value, collections_abc.Sequence):

        return len(value) == 0

    else:

        return value is None


def isNumber(text):
    """
    Evaluates if the supplied text represents a number.

    :type text: str
    :rtype: bool
    """

    return __number__.match(text) is not None


def isBoolean(text):
    """
    Evaluates if the supplied text represents a boolean.

    :type text: str
    :rtype: bool
    """

    return text.lower() in __states__


def eval(text):
    """
    Parses the supplied text for any numerical values and returns them.
    If nothing is found then the original text is returned!

    :type text: str
    :rtype: Union[str, bool, int, float]
    """

    # Redundancy check
    #
    if not isinstance(text, string_types):

        return text

    # Evaluate if this is a number
    #
    if isNumber(text) or isBoolean(text):

        return ast.literal_eval(text)

    else:

        return text


def splitCasing(text):
    """
    Splits the supplied text at any case changes.

    :type text: str
    :rtype: str
    """

    return __title__.findall(text)


def titleize(text):
    """
    Returns a string where each split segment is titleized.
    For example: "left_arm_01" > "Left_Arm_01"

    :type text: str
    :rtype: str
    """

    return ''.join([pascalize(string) for string in text.split('_')])


def camelize(text, separator=''):
    """
    Returns a camel cased string using the supplied text.
    For example: "left_arm_01" > "leftArm01"

    :type text: str
    :type separator: str
    :rtype: str
    """

    return separator.join([string.title() if i > 0 else string.lower() for (i, string) in enumerate(splitCasing(text))])


def pascalize(text, separator=''):
    """
    Returns a pascal cased string using the supplied text.
    For example: "left_arm_01" > "LeftArm01"

    :type text: str
    :type separator: str
    :rtype: str
    """

    return separator.join([string.title() for string in splitCasing(text)])


def slugify(text, whitespace='_', illegal=''):
    """
    Normalizes string by removing illegal characters and converting spaces to underscores.
    See the following for more details: https://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename

    :type text: str
    :type whitespace: str
    :type illegal: str
    :rtype: str
    """

    name = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    name = re.sub(r'[^\w\s-]', illegal, name).strip()
    name = re.sub(r'[-\s]+', whitespace, name)

    return name


def stripCartesian(text):
    """
    Removes any cartesian characters from the end of the supplied string.

    :type text: str
    :rtype: str
    """

    if any([text.endswith(axis) for axis in ('X', 'Y', 'Z')]):

        return text[:-1]

    else:

        return text
