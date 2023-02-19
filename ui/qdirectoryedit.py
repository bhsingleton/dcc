import os

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

        # Add directory actions
        #
        self.getExistingDirectoryAction = QtWidgets.QAction(QtGui.QIcon(':/qt-project.org/styles/commonstyle/images/diropen-16.png'), '', parent=self)
        self.getExistingDirectoryAction.setObjectName('getExistingDirectoryAction')
        self.getExistingDirectoryAction.setToolTip('Get existing dialog.')
        self.getExistingDirectoryAction.triggered.connect(self.on_getExistingDirectoryAction_triggered)

        self.parentDirectoryAction = QtWidgets.QAction(QtGui.QIcon(':/qt-project.org/styles/commonstyle/images/up-16.png'), '', parent=self)
        self.parentDirectoryAction.setObjectName('parentDirectoryAction')
        self.parentDirectoryAction.triggered.connect(self.on_parentDirectoryAction_triggered)

        self.addAction(self.getExistingDirectoryAction, QtWidgets.QLineEdit.TrailingPosition)
        self.addAction(self.parentDirectoryAction, QtWidgets.QLineEdit.TrailingPosition)
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
    def on_getExistingDirectoryAction_triggered(self, checked=False):
        """
        Slot method for the getExistingDirectoryAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        # Check if this widget is an editor
        #
        if self.isEditor():

            # Clear focus to trigger text accessor
            #
            self._requiresUserInput = True
            self.clearFocus()

        else:

            # Evaluate user input
            #
            directory = self.getExistingDirectory()

            if not stringutils.isNullOrEmpty(directory):

                self.setText(directory)

    @QtCore.Slot(bool)
    def on_parentDirectoryAction_triggered(self, checked=False):
        """
        Slot method for the parentDirectoryAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        self.setText(os.path.dirname(self.text()))
    # endregion
