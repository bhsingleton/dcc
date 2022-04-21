import re
import unicodedata

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__title__ = re.compile(r'([A-Z]?[a-z0-9_]+)')


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


def titleize(text, separator=''):
    """
    Capitalizes the first letter of the supplied text.

    :type text: str
    :type separator: str
    :rtype: str
    """

    return separator.join([x.title() for x in __title__.findall(text)])


def slugify(text):
    """
    Normalizes string by removing non-alpha characters and converting spaces to underscores.
    See the following for more details: https://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename

    :type text: str
    :rtype: str
    """

    name = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    name = re.sub(r'[^\w\s-]', '', name).strip()
    name = re.sub(r'[-\s]+', '_', name)

    return name
