import os

from PySide2 import QtCore, QtWidgets, QtUiTools

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
        :key customWidgets: dict[str, type]
        :key workingDirectory: str
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
    # endregion

    # region Methods
    def customWidgets(self):
        """
        Getter method that returns the custom widget collection.

        :rtype: dict[str, type]
        """

        return self._customWidgets

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
        log.debug('Creating widget: %s' % className)

        if parent is None and self.instance is not None:

            return self.instance

        # Check if this is a builtin type
        # If not then check if it's a custom widget
        #
        customWidgets = self.customWidgets()

        if className in self.availableWidgets():

            return super(QUicLoader, self).createWidget(className, parent, name)

        elif className in customWidgets:

            return customWidgets[className](parent)

        else:

            raise TypeError('createWidget() expects a valid widget (%s given)!' % className)
    # endregion
