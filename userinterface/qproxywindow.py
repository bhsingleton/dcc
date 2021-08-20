from PySide2 import QtCore, QtWidgets, QtGui
from abc import ABCMeta, abstractmethod

from .. import fnqt
from ..decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QProxyWindow(QtWidgets.QMainWindow):
    """
    Overload of QMainWindow used to track all derived Robot Entertainment windows.
    This provides us the ability to close all windows on restart.
    """

    __instances__ = {}

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :keyword parent: QtWidgets.QWidget
        :keyword flags: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        parent = kwargs.get('parent', fnqt.FnQt().getMainWindow())
        flags = kwargs.get('flags', QtCore.Qt.WindowFlags())

        super(QProxyWindow, self).__init__(parent=parent, flags=flags)

        # Call build method
        #
        if not self.isInitialized():

            self.__build__()

    @abstractmethod
    def __build__(self):
        """
        Private method used to build the user interface.

        :rtype: None
        """

        self.setObjectName(self.__class__.__name__)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

    @classproperty
    def className(cls):
        """
        Getter method that returns the name of this class.

        :rtype: str
        """

        return cls.__name__

    def showEvent(self, event):
        """
        Event method called after the window has been shown.

        :type event: QtGui.QShowEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QProxyWindow, self).showEvent(event)

        # Store reference to instance
        #
        self.__class__.__instances__[self.className] = self

    def closeEvent(self, event):
        """
        Event method called after the window has been closed.

        :type event: QtGui.QCloseEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QProxyWindow, self).closeEvent(event)

        # Remove reference to instance
        #
        try:

            self.__class__.__instances__.pop(self.className)

        except KeyError as exception:

            log.debug(exception)

    @staticmethod
    def getTextWidth(item, text, offset=12):
        """
        Static method used to calculate the pixel units from the supplied string value.

        :type item: QtGui.QStandardItem
        :type text: str
        :type offset: int
        :rtype: int
        """

        # Get font from item and calculate width
        #
        font = item.font()
        fontMetric = QtGui.QFontMetrics(font)

        width = fontMetric.width(text) + offset

        return width

    @classmethod
    def createStandardItem(cls, text, height=16):
        """
        Class method used to create a QStandardItem from the given string value.

        :type text: str
        :type height: int
        :rtype: QtGui.QStandardItem
        """

        # Create item and resize based on text width
        #
        item = QtGui.QStandardItem(text)
        textWidth = cls.getTextWidth(item, text)

        item.setSizeHint(QtCore.QSize(textWidth, height))
        item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        return item

    @classmethod
    def isInitialized(cls):
        """
        Evaluates whether this class has already been initialized.

        :rtype: bool
        """

        return cls.className in cls.__instances__

    @classmethod
    def hasInstance(cls):
        """
        Checks if an instance already exists for this class.

        :rtype: bool
        """

        return cls.__instances__.get(cls.__name__, None) is not None

    @classmethod
    def getInstance(cls):
        """
        Returns the singleton instance for this class.
        If no window is found then a new instance is returned.

        :rtype: QProxyWindow
        """

        if not cls.hasInstance():

            cls.__instances__[cls.__name__] = cls()

        return cls.__instances__[cls.__name__]

    @classmethod
    def closeAllWindows(cls):
        """
        Closes all of the open windows.
        Only the windows that inherit from this class will be closed!

        :rtype: None
        """

        # Iterate through windows
        #
        for window in list(cls.__instances__.values()):

            window.close()
