from Qt import QtCore, QtWidgets, QtGui
from ..python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QDirectoryEdit(QtWidgets.QLineEdit):
    """
    Overload of QLineEdit that includes a directory explorer button.
    """

    # region Signals
    programmaticallyChanged = QtCore.Signal(str)
    # endregion

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key caption: str
        :key dir: str
        :key parent: QtWidgets.QWidget
        :rtype: None
        """

        # Declare private variables
        #
        self._caption = kwargs.pop('caption', 'Select Directory')
        self._requiresUserInput = False

        # Call parent method
        #
        super(QDirectoryEdit, self).__init__(*args, **kwargs)

        # Add custom action
        #
        action = QtWidgets.QAction(QtGui.QIcon(':dcc/icons/open_folder.svg'), '', parent=self)
        action.setToolTip('Select directory from dialog.')
        action.triggered.connect(self.on_action_triggered)

        self.addAction(action, QtWidgets.QLineEdit.TrailingPosition)
    # endregion

    # region Methods
    def text(self):
        """
        Returns the line edit's text.

        :rtype: str
        """

        # Check if user input is required
        # This is done for sake of circumventing crashes from a QStyledItemDelegate
        #
        if self._requiresUserInput:

            directory = self.getExistingDirectory()
            self._requiresUserInput = False

            if not stringutils.isNullOrEmpty(directory):

                self.setText(directory)

        # Call parent method
        #
        return super(QDirectoryEdit, self).text()

    def setText(self, text):
        """
        Updates the line edit's text.

        :type text: str
        :rtype: None
        """

        # Call parent method
        #
        super(QDirectoryEdit, self).setText(text)
        self.programmaticallyChanged.emit(text)

    def isEditor(self):
        """
        Evaluates if this widget is currently acting as an editor for a QStyledItemDelegate.

        :rtype: bool
        """

        parent = self.parent()
        objectName = parent.objectName()

        return isinstance(parent, QtWidgets.QWidget) and objectName == 'qt_scrollarea_viewport'

    def getExistingDirectory(self):
        """
        Prompts the user to select an existing directory.

        :rtype: str
        """

        currentDirectory = super(QDirectoryEdit, self).text()

        return QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption=self._caption,
            dir=currentDirectory,
            options=QtWidgets.QFileDialog.ShowDirsOnly
        )
    # endregion

    # region Slots
    @QtCore.Slot(bool)
    def on_action_triggered(self, checked=False):
        """
        Slot method for the associated action's triggered signal.

        :type checked: bool
        :rtype: None
        """

        # Check if this widget is an editor
        #
        if self.isEditor():

            self._requiresUserInput = True
            self.clearFocus()
            return

        # Evaluate user input
        #
        directory = self.getExistingDirectory()

        if not stringutils.isNullOrEmpty(directory):

            self.setText(directory)
    # endregion
