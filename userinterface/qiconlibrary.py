import os

from PySide2 import QtGui
from six.moves import collections_abc
from dcc.decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__dir__ = os.path.join(os.path.dirname(__file__))


class QIconLibrary(collections_abc.MutableMapping):
    """
    Overload of MutableMapping used to lookup and initialize QIcons for external use.
    """

    __slots__ = ('_icons',)
    __extensions__ = ('ico', 'bmp', 'png', 'cur')
    __paths__ = [os.path.join(__dir__, 'icons')]

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(QIconLibrary, self).__init__()

        # Declare private variables
        #
        self._icons = {}

    def __getitem__(self, key):
        """
        Private method that returns an indexed icon.

        :type key: str
        :rtype: QtGui.QIcon
        """

        return self.get(key, default=None)

    def __setitem__(self, key, value):
        """
        Private method that updates an indexed icon.

        :type key: str
        :type value: QtGui.QIcon
        :rtype: None
        """

        # Check value type
        #
        if not isinstance(value, QtGui.QIcon):

            raise TypeError('Unable to assign icon using "%s" type!' % type(value).__name__)

        self._icons[key] = value

    def __delitem__(self, key):
        """
        Private method that deletes an indexed icon.

        :type key: str
        :rtype: None
        """

        del self._icons[key]

    def __len__(self):
        """
        Private method that evaluates the number of initialized icons.

        :rtype: int
        """

        return len(self._icons)

    def __iter__(self):
        """
        Private method that returns a generator that yields all active icons.

        :rtype: iter
        """

        return self._icons.items()

    def get(self, key, default=None):
        """
        Returns an with the given name.

        :type key: str
        :type default: object
        :rtype: QtGui.QIcon
        """

        # Check if icon exists
        #
        icon = self._icons.get(key, None)

        if icon is not None:

            return icon

        # Concatenate file path
        #
        filePath = self.findIconByName(key)

        if os.path.exists(filePath):

            icon = QtGui.QIcon(filePath)
            self._icons[key] = icon

            return icon

        else:

            log.warning('Unable to locate icon: %s' % key)
            return default

    def clear(self):
        """
        Clears all the icons belonging to this instance.

        :rtype: None
        """

        return self._icons.clear()

    @classproperty
    def paths(cls):
        """
        Getter method that returns the paths utilized by this library.

        :rtype: list[str]
        """

        return cls.__paths__

    @classproperty
    def extensions(cls):
        """
        Getter method that returns the extensions supported by this library.

        :rtype: tuple[str]
        """

        return cls.__extensions__

    def findIconByName(self, name):
        """
        Locates an icon based on the supplied name.

        :type name: str
        :rtype: str
        """

        # Iterate through path
        #
        for path in self.paths:

            # Iterate through extensions
            #
            for extension in self.extensions:

                filename = '{name}.{extension}'.format(name=name, extension=extension)
                filePath = os.path.join(path, filename)

                if os.path.exists(filePath):

                    return filePath

                else:

                    continue

        return ''


def getIconByName(name):
    """
    Returns an icon with the given name.

    :type name: str
    :rtype: QtGui.QIcon
    """

    return ICONS[name]


ICONS = QIconLibrary()  # Module constant for icon lookups
