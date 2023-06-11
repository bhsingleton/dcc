import os

from Qt import QtCore, QtWidgets, QtGui
from ..python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QFileEdit(QtWidgets.QLineEdit):
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
        self._caption = kwargs.pop('caption', 'Select File')
        self._filter = kwargs.pop('filter', 'All files (*.*)')
        self._requiresUserInput = False

        # Call parent method
        #
        super(QFileEdit, self).__init__(*args, **kwargs)

        # Add file action
        #
        self.getExistingFileAction = QtWidgets.QAction(QtGui.QIcon(':/qt-project.org/styles/commonstyle/images/diropen-16.png'), '', parent=self)
        self.getExistingFileAction.setObjectName('getExistingFileAction')
        self.getExistingFileAction.setToolTip('Browse for an existing file.')
        self.getExistingFileAction.triggered.connect(self.on_getExistingFileAction_triggered)

        self.addAction(self.getExistingFileAction, QtWidgets.QLineEdit.TrailingPosition)
    # endregion

    # region Methods
    def text(self):
        """
        Returns the text from the line edit.

        :rtype: str
        """

        # Check if user input is required
        #
        if self._requiresUserInput:

            filePath = self.getOpenFileName()
            self._requiresUserInput = False

            if not stringutils.isNullOrEmpty(filePath):

                self.setText(filePath)

        # Call parent method
        #
        return super(QFileEdit, self).text()

    def isEditor(self):
        """
        Evaluates if this widget is currently acting as an editor for a QStyledItemDelegate.

        :rtype: bool
        """

        parent = self.parent()
        objectName = parent.objectName()

        return isinstance(parent, QtWidgets.QWidget) and objectName == 'qt_scrollarea_viewport'

    def getOpenFileName(self):
        """
        Prompts the user to select an existing directory.

        :rtype: str
        """

        currentDirectory = super(QFileEdit, self).text()

        return QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption=self._caption,
            dir=currentDirectory,
            filter=self._filter
        )[0]
    # endregion

    # region Slots
    @QtCore.Slot(bool)
    def on_getExistingFileAction_triggered(self, checked=False):
        """
        Slot method for the associated action's triggered signal.

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
            filePath = self.getOpenFileName()

            if not stringutils.isNullOrEmpty(filePath):

                self.setText(filePath)
    # endregion
