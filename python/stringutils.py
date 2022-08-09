import re
import unicodedata

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__title__ = re.compile(r'([A-Z]?[a-z0-9]+)')
__number__ = re.compile(r'(?:[+-])?(?:[0-9])+(?:\.{1}[0-9]+)?(?:e{1}\-{1}[0-9]+)?')
__states__ = ('true', 'on', 'yes')


def isNullOrEmpty(value):
    """
    Evaluates if the supplied value is null or empty.

    :type value: Any
    :rtype: bool
    """

    if hasattr(value, '__len__'):

        return len(value) == 0

    elif value is None:

        return True

    else:

        raise TypeError('isNullOrEmpty() expects a sequence (%s given)!' % type(value).__name__)


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


def camelize(text, separator=''):
    """
    Returns a camel cased string using the supplied text.
    For example: "left_arm_01" > "leftArm01"

    :type text: str
    :type separator: str
    :rtype: str
    """

    return separator.join([string.title() if i > 0 else string for (i, string) in enumerate(__title__.findall(text))])


def pascalize(text, separator=''):
    """
    Returns a pascal cased string using the supplied text.
    For example: "left_arm_01" > "LeftArm01"

    :type text: str
    :type separator: str
    :rtype: str
    """

    return separator.join([x.title() for x in __title__.findall(text)])


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
