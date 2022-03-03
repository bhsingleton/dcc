from PySide2 import QtCore, QtWidgets, QtGui

from dcc.fbx import fbxutils
from dcc.ui import quicwindow, qlistdialog

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QFbxExportSetEditor(quicwindow.QUicWindow):
    """
    Overload of QUicWindow used to edit fbx export set data.
    """

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key flags: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        super(QFbxExportSetEditor, self).__init__(*args, **kwargs)

        # Declare class variables
        #
        self._currentAsset = None
        self._currentExportSet = None
    # endregion

    # region Events
    def showEvent(self, event):
        """
        Event method called after the window has been shown.

        :type event: QtGui.QShowEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QFbxExportSetEditor, self).showEvent(event)

    def closeEvent(self, event):
        """
        Event method called after the window has been closed.

        :type event: QtGui.QCloseEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QFbxExportSetEditor, self).closeEvent(event)
    # endregion

    # region Slots
    @QtCore.Slot(bool)
    def on_savePushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for saving all recent changes.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(bool)
    def on_projectPathPushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for updating the project path.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(int)
    def on_fileTypeComboBox_currentIndexChanged(self, index):
        """
        Clicked slot method responsible for updating the fbx file type.

        :type index: int
        :rtype: None
        """

        pass

    @QtCore.Slot(int)
    def on_fileVersionComboBox_currentIndexChanged(self, index):
        """
        Current index changed slot method responsible for updating the fbx file version.

        :type index: int
        :rtype: None
        """

        pass

    @QtCore.Slot(int)
    def on_exportSetComboBox_currentIndexChanged(self, index):
        """
        Current index changed slot method responsible for updating the current fbx export set.

        :type index: int
        :rtype: None
        """

        pass

    @QtCore.Slot(bool)
    def on_newExportSetPushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for creating a new fbx export set.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(bool)
    def on_duplicateExportSetPushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for duplicating the current fbx export set.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(bool)
    def on_renameExportSetPushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for renaming the current fbx export set.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(bool)
    def on_reorderExportSetPushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for reordering the fbx export sets.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(bool)
    def on_deleteExportSetPushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for deleting the current fbx export set.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(bool)
    def on_customScriptsPushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for opening the custom script dialog.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(bool)
    def on_exportPushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for exporting the current fbx export set.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(bool)
    def on_exportAllPushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for exporting all of the fbx export sets.

        :type checked: bool
        :rtype: None
        """

        pass
    # endregion
