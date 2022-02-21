import os
import inspect
import shiboken2

from PySide2 import QtCore, QtWidgets, QtUiTools
from abc import abstractmethod
from dcc.userinterface import qproxywindow

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__dir__ = os.path.dirname(os.path.abspath(__file__))


class QUicLoader(QtUiTools.QUiLoader):
    """
    Subclass of QUiLoader used to create custom user interfaces in a base instance.
    Unlike QUiLoader this class does not create a new instance of the top-level widget,
    but creates the user interface on an existing instance of the top-level class.
    """

    # region Dunderscores
    def __init__(self, instance, **kwargs):
        """
        Create a UI loader for the supplied instance.
        This class must be derived from the top-level xml class element in order to load.

        :type instance: QtWidgets.QWidget
        :keyword customWidgets: dict[str, type]
        :keyword workingDirectory: str
        :rtype: None
        """

        # Call parent method
        #
        super(QUicLoader, self).__init__(parent=instance)

        # Declare private variables
        #
        self._instance = instance
        self._customWidgets = kwargs.get('customWidgets', {})

        # Set working directory
        #
        workingDirectory = kwargs.get('workingDirectory', __dir__)
        self.setWorkingDirectory(workingDirectory)
    # endregion

    # region Properties
    @property
    def instance(self):
        """
        Getter method that returns the top-level widget that's being populated.

        :rtype: QtWidgets.QWidget
        """

        return self._instance

    @property
    def customWidgets(self):
        """
        Getter method that returns the custom widget collection.

        :rtype: dict[str, type]
        """

        return self._customWidgets
    # endregion

    # region Methods
    def createWidget(self, className, parent=None, name=''):
        """
        Called for each widget defined in the .ui file.
        This behavior is overridden to populate the internal instance instead.

        :type className: str
        :type parent: QtWidgets.QWidget
        :type name: str
        :rtype: QtWidgets.QWidget
        """

        # Check if this is top-level widget
        # If so then return the associated instance instead
        #
        log.info('Creating widget: %s' % className)

        if parent is None and self.instance is not None:

            return self.instance

        # Try and create widget from ui file
        #
        try:

            # Check if this is a builtin type
            # If not then check if it's a custom widget
            #
            if className in self.availableWidgets():

                return super(QUicLoader, self).createWidget(className, parent, name)

            else:

                return self.customWidgets[className](parent)

        except (TypeError, KeyError) as exception:

            raise Exception('createWidget() Unable to locate custom widget: %s' % className)
    # endregion


class QUicWindow(qproxywindow.QProxyWindow):
    """
    Overload of QProxyWindow used to dynamically create widgets via .ui files.
    """

    # region Dunderscores
    def __load__(self, **kwargs):
        """
        Private method used to load the user interface from the associated .ui file.
        Be sure to overload the associated class methods to augment the behavior of this method.

        :keyword customWidgets: dict[str, type]
        :keyword workingDirectory: str
        :rtype: QtWidgets.QWidget
        """

        # Create new ui loader
        #
        customWidgets = kwargs.get('customWidgets', self.customWidgets())
        workingDirectory = kwargs.get('workingDirectory', self.workingDirectory())
        self.loader = QUicLoader(self, customWidgets=customWidgets, workingDirectory=workingDirectory)

        # Load the .ui file
        #
        filename = self.filename()
        filePath = os.path.join(workingDirectory, filename)

        log.info('Loading UI file: %s' % filePath)
        window = self.loader.load(filePath)

        # Auto signal/slot connections
        # Qt expects the following method names: on_{objectName}_{signal} complete with QtCore.Slot decorator!
        #
        QtCore.QMetaObject.connectSlotsByName(window)

        return window

    def __build__(self, **kwargs):
        """
        Private method used to build the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QUicWindow, self).__build__(**kwargs)

        # Load the user interface
        #
        self.preLoad()
        self.__load__(**kwargs)
        self.postLoad()

    def __getattribute__(self, item):
        """
        Private method used to lookup an attribute.
        Sadly all pointers are lost from QUicLoader so we have to rebuild them on demand.

        :type item: str
        :rtype: QtCore.QObject
        """

        # Call parent method
        #
        obj = super(QUicWindow, self).__getattribute__(item)

        if isinstance(obj, QtWidgets.QWidget):

            # Check if cpp pointer is still valid
            #
            if not shiboken2.isValid(obj):

                obj = self.findChild(QtWidgets.QWidget, item)
                setattr(self, item, obj)

            return obj

        else:

            return obj
    # endregion

    # region Methods
    @classmethod
    def filename(cls):
        """
        Returns the ui configuration filename for this class.
        This defaults to the name of this python file.

        :rtype: str
        """

        filePath = inspect.getfile(cls)
        directory, filename = os.path.split(filePath)
        name, ext = os.path.splitext(filename)

        return '{name}.ui'.format(name=name)

    @classmethod
    def customWidgets(cls):
        """
        Returns a dictionary of custom widgets used by this class.
        Overload this method to extend this dictionary!

        :rtype: dict[str, type]
        """

        return {}

    @classmethod
    def workingDirectory(cls):
        """
        Returns the working directory for this class.
        This defaults to the directory this python file resides in.

        :rtype: str
        """

        return os.path.dirname(inspect.getfile(cls))

    def preLoad(self):
        """
        Called before the user interface has been loaded.

        :rtype: None
        """

        pass

    def postLoad(self):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        pass
    # endregion
