import os
import webbrowser

from Qt import QtCore, QtWidgets, QtGui
from copy import copy
from dcc import fnscene, fnnode, fnnotify
from dcc.ui import quicwindow, qdirectoryedit, qfileedit
from dcc.ui.dialogs import qlistdialog
from dcc.ui.models import qpsonitemmodel, qpsonstyleditemdelegate
from dcc.fbx.libs import fbxio, fbxasset, fbxexportset, fbxscript
from dcc.python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QFbxExportSetItemDelegate(qpsonstyleditemdelegate.QPSONStyledItemDelegate):
    """
    Overload of QPSONStyledItemDelegate that delegates fbx export set types.
    """

    # region Methods
    def createEditorByProperty(self, obj, func, isElement=False, parent=None):
        """
        Returns a widget from the supplied object and property.

        :type obj: object
        :type func: function
        :type isElement: bool
        :type parent: QtWidgets.QWidget
        :rtype: QtWidgets.QWidget
        """

        # Evaluate object type
        #
        if isinstance(obj, fbxexportset.FbxExportSet) and func.__name__ == 'directory':

            return qdirectoryedit.QDirectoryEdit(parent=parent)

        elif isinstance(obj, fbxscript.FbxScript) and func.__name__ == 'filePath':

            return qfileedit.QFileEdit(parent=parent)

        else:

            return super(QFbxExportSetItemDelegate, self).createEditorByProperty(obj, func, isElement=isElement, parent=parent)
    # endregion


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

        # Declare private variables
        #
        self._manager = fbxio.FbxIO()
        self._asset = None
        self._currentExportSet = None
        self._scene = fnscene.FnScene()
        self._notifies = fnnotify.FnNotify()
        self._notifyId = None

        # Declare public variables
        #
        self.exportSetItemModel = None
        self.exportSetItemDelegate = None
        self.customContextMenu = None
        self.clearItemsAction = None
        self.copySelectionAction = None

        # Call parent method
        #
        super(QFbxExportSetEditor, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def manager(self):
        """
        Getter method that returns the fbx asset manager.

        :rtype: fbxio.FbxIO
        """

        return self._manager

    @property
    def scene(self):
        """
        Getter method that returns the scene interface.

        :rtype: fnscene.FnScene
        """

        return self._scene

    @property
    def asset(self):
        """
        Getter method that returns the current fbx asset.

        :rtype: fbxasset.FbxAsset
        """

        return self._asset

    @property
    def currentExportSet(self):
        """
        Getter method that returns the current fbx export set.

        :rtype: fbxexportset.FbxExportSet
        """

        return self._currentExportSet
    # endregion

    # region Methods
    def postLoad(self):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        # Call parent method
        #
        super(QFbxExportSetEditor, self).postLoad()

        # Initialize tree view model
        #
        self.exportSetItemModel = qpsonitemmodel.QPSONItemModel(parent=self.exportSetTreeView)
        self.exportSetItemModel.setObjectName('exportSetItemModel')

        self.exportSetTreeView.setModel(self.exportSetItemModel)

        self.exportSetItemDelegate = QFbxExportSetItemDelegate(parent=self.exportSetTreeView)
        self.exportSetItemDelegate.setObjectName('exportSetItemDelegate')

        self.exportSetTreeView.setItemDelegate(self.exportSetItemDelegate)

        # Initialize custom context menu
        #
        self.customContextMenu = QtWidgets.QMenu(parent=self.exportSetTreeView)
        self.customContextMenu.setObjectName('customContextMenu')

        self.clearItemsAction = QtWidgets.QAction('Clear Items', parent=self.customContextMenu)
        self.clearItemsAction.setObjectName('clearItemsAction')
        self.clearItemsAction.triggered.connect(self.on_clearItemsAction_triggered)

        self.copySelectionAction = QtWidgets.QAction('Copy Selection', parent=self.customContextMenu)
        self.copySelectionAction.setObjectName('copySelectionAction')
        self.copySelectionAction.triggered.connect(self.on_copySelectionAction_triggered)

        self.customContextMenu.addActions([self.clearItemsAction, self.copySelectionAction])

    def isNameUnique(self, name):
        """
        Evaluates if the supplied name is currently unique.

        :type name: str
        :rtype: bool
        """

        return not any(x.name == name for x in self.asset.exportSets)

    def uniquify(self, name):
        """
        Generates a unique name from the supplied string.

        :type name: str
        :rtype: str
        """

        newName = name
        index = 1

        while not self.isNameUnique(newName):

            newName = '{name}{padding}'.format(name=name, padding=str(index).zfill(2))
            index += 1

        return newName

    def invalidateAsset(self):
        """
        Invalidates the displayed asset settings.

        :rtype: None
        """

        # Load scene asset
        #
        self._asset = self._manager.loadAsset()

        if self._asset is None:

            self._asset = fbxasset.FbxAsset()

        # Synchronize asset widgets
        #
        self.assetNameLineEdit.setText(self.asset.name)
        self.assetDirectoryLineEdit.setText(self.asset.directory)
        self.fileTypeComboBox.setCurrentIndex(self.asset.fileType)
        self.fileVersionComboBox.setCurrentIndex(self.asset.fileVersion)

        # Re-populate combo box
        #
        self.exportSetComboBox.clear()
        self.exportSetComboBox.addItems([x.name for x in self.asset.exportSets])

    def invalidateExportSet(self):
        """
        Invalidates the displayed export set settings.

        :rtype: None
        """

        # Attach export set to item model
        #
        if self.currentExportSet is not None:

            self.exportSetItemModel.invisibleRootItem = self.currentExportSet

        # Invalidate export path
        #
        self.invalidateExportPath()

    def invalidateExportPath(self):
        """
        Invalidates the displayed export path.

        :rtype: None
        """

        if self.currentExportSet is not None:

            self.exportPathLineEdit.setText(self.currentExportSet.exportPath())
    # endregion

    # region Callbacks
    def sceneChanged(self, *args, **kwargs):
        """
        Post file-open callback that invalidates the current asset.

        :rtype: None
        """

        self.invalidateAsset()
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

        # Create post file-open notify
        #
        self._notifyId = self._notifies.addPostFileOpenNotify(self.sceneChanged)
        self.sceneChanged()

    def closeEvent(self, event):
        """
        Event method called after the window has been closed.

        :type event: QtGui.QCloseEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QFbxExportSetEditor, self).closeEvent(event)

        # Remove post file-open notify
        #
        self._notifies.removeNotify(self._notifyId)
        self._notifies = None  # Clean up resources
    # endregion

    # region Slots
    @QtCore.Slot(bool)
    def on_saveAction_triggered(self, checked=False):
        """
        Slot method for the saveAction's triggered signal.

        :type checked: bool
        :rtype: None
        """

        self.manager.saveAsset(self.asset)  # This will mark the scene as dirty!

    @QtCore.Slot(bool)
    def on_saveAsAction_triggered(self, checked=False):
        """
        Slot method for the saveAsAction's triggered signal.

        :type checked: bool
        :rtype: None
        """

        # Prompt user for save path
        #
        currentDirectory = os.path.expandvars(self.asset.directory)

        filePath = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption='Save Asset As',
            dir=currentDirectory,
            filter='Fbx Assets (*.json)'
        )

        # Check if path is valid
        # A null value will be returned if the user exited
        #
        if filePath:

            self.manager.saveAssetAs(self.asset, filePath)

        else:

            log.info('Operation aborted...')

    @QtCore.Slot(bool)
    def on_importAction_triggered(self, checked=False):
        """
        Slot method for the importAction's triggered signal.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(str)
    def on_assetNameLineEdit_textChanged(self, text):
        """
        Slot method for the assetNameLineEdit's textChanged signal.

        :type text: str
        :rtype: None
        """

        self.asset.name = text

    @QtCore.Slot(bool)
    def on_savePushButton_clicked(self, checked=False):
        """
        Slot method for the savePushButton's clicked signal.

        :type checked: bool
        :rtype: None
        """

        self.manager.saveAsset(self.asset)  # This will mark the scene as dirty!

    @QtCore.Slot(str)
    def on_assetDirectoryLineEdit_textChanged(self, text):
        """
        Slot method for the assetDirectoryLineEdit's textChanged signal.

        :type text: str
        :rtype: None
        """

        self.asset.directory = os.path.normpath(text)
        self.invalidateExportPath()

    @QtCore.Slot(bool)
    def on_assetDirectoryPushButton_clicked(self, checked=False):
        """
        Slot method for the assetDirectoryPushButton's clicked signal.

        :type checked: bool
        :rtype: None
        """

        # Prompt user for save path
        #
        currentDirectory = os.path.expandvars(self.asset.directory)

        assetDirectory = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption='Select Asset Directory',
            dir=currentDirectory,
            options=QtWidgets.QFileDialog.ShowDirsOnly
        )

        # Check if path is valid
        # A null value will be returned if the user exited
        #
        if assetDirectory:

            self.assetDirectoryLineEdit.setText(assetDirectory)

        else:

            log.info('Operation aborted...')

    @QtCore.Slot(int)
    def on_fileTypeComboBox_currentIndexChanged(self, index):
        """
        Slot method for the fileTypeComboBox's currentIndexChanged signal.

        :type index: int
        :rtype: None
        """

        self.asset.fileType = index

    @QtCore.Slot(int)
    def on_fileVersionComboBox_currentIndexChanged(self, index):
        """
        Slot method for the fileVersionComboBox's currentIndexChanged signal.

        :type index: int
        :rtype: None
        """

        self.asset.fileVersion = index

    @QtCore.Slot(QtCore.QPoint)
    def on_exportSetTreeView_customContextMenuRequested(self, point):
        """
        Slot method for the exportSetTreeView's customContextMenuRequested signal.

        :type point: QtCore.QPoint
        :rtype: None
        """

        # Check if index is valid
        #
        index = self.sender().indexAt(point)

        if not index.isValid():

            return

        # Inspect item at index
        #
        model = index.model()
        internalId = model.decodeInternalId(index.internalId())

        name = internalId[-1]

        if name in ('includeNodes', 'includeJoints', 'excludeJoints'):

            globalPoint = self.sender().mapToGlobal(point)
            self.customContextMenu.exec_(globalPoint)

        else:

            pass

    @QtCore.Slot(bool)
    def on_clearItemsAction_triggered(self, checked=False):
        """
        Slot method for the clearItemsAction's triggered signal.

        :type checked: bool
        :rtype: None
        """

        # Evaluate selected indices
        #
        indices = [index for index in self.sequencerTreeView.selectedIndexes() if index.column() == 0]
        numIndices = len(indices)

        if numIndices != 1:

            return

        # Remove all child row
        #
        index = indices[0]
        model = index.model()

        rowCount = model.rowCount(parent=index)

        if rowCount > 0:

            model.removeRows(0, rowCount, parent=index)

    @QtCore.Slot(bool)
    def on_copySelectionAction_triggered(self, checked=False):
        """
        Slot method for the copySelectionAction's triggered signal.

        :type checked: bool
        :rtype: None
        """

        # Evaluate selected indices
        #
        indices = [index for index in self.sequencerTreeView.selectedIndexes() if index.column() == 0]
        numIndices = len(indices)

        if numIndices != 1:

            return

        # Remove all child row
        #
        index = indices[0]
        model = index.model()

        rowCount = model.rowCount(parent=index)

        if rowCount > 0:

            model.removeRows(0, rowCount, parent=index)

        # Extend row using selection
        #
        node = fnnode.FnNode()

        nodeNames = [node(obj).name() for obj in self.scene.getActiveSelection()]
        numNodeNames = len(nodeNames)

        if numNodeNames > 0:

            model.extendRows(nodeNames, parent=index)

    @QtCore.Slot(int)
    def on_exportSetComboBox_currentIndexChanged(self, index):
        """
        Slot method for the exportSetComboBox's currentIndexChanged signal.

        :type index: int
        :rtype: None
        """

        sender = self.sender()

        if 0 <= index < sender.count():

            self._currentExportSet = self.asset.exportSets[index]
            self.invalidateExportSet()

    @QtCore.Slot(bool)
    def on_newExportSetPushButton_clicked(self, checked=False):
        """
        Slot method for the newExportSetPushButton's clicked signal.

        :type checked: bool
        :rtype: None
        """

        # Prompt user
        #
        name, response = QtWidgets.QInputDialog.getText(
            self,
            'Create New Export Set',
            'Enter Name:',
            QtWidgets.QLineEdit.Normal
        )

        if not response:

            log.info('Operation aborted...')
            return

        # Check if name is unique
        # Be sure to slugify the name before processing!
        #
        name = stringutils.slugify(name)

        if not self.isNameUnique(name) or len(name) == 0:

            # Prompt user
            #
            response = QtWidgets.QMessageBox.warning(
                self,
                'Create New Export Set',
                'The supplied name is not unique!',
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
            )

            if response == QtWidgets.QMessageBox.Ok:

                self.newExportSetPushButton.click()

        else:

            # Append new export set
            #
            fbxExportSet = fbxexportset.FbxExportSet(name=name)
            self.asset.exportSets.append(fbxExportSet)

            # Add export set to combo box
            #
            self.exportSetComboBox.addItem(fbxExportSet.name)
            self.exportSetComboBox.setCurrentIndex(len(self.asset.exportSets) - 1)

    @QtCore.Slot(bool)
    def on_duplicateExportSetPushButton_clicked(self, checked=False):
        """
        Slot method for the duplicateExportSetPushButton's clicked signal.

        :type checked: bool
        :rtype: None
        """

        # Check if there are any sets to duplicate
        #
        if self.currentExportSet is None:

            log.warning('No export sets available to duplicate!')
            return

        # Copy current export set
        #
        fbxExportSet = copy(self.currentExportSet)
        fbxExportSet.name = self.uniquify(fbxExportSet.name)

        self.asset.exportSets.append(fbxExportSet)

        # Add item to combo box
        #
        self.exportSetComboBox.addItem(fbxExportSet.name)

    @QtCore.Slot(bool)
    def on_renameExportSetPushButton_clicked(self, checked=False):
        """
        Slot method for the renameExportSetPushButton's clicked signal.

        :type checked: bool
        :rtype: None
        """

        # Check if current export set is valid
        #
        if self.currentExportSet is None:

            log.warning('No export sets available to rename!')
            return

        # Prompt user
        #
        newName, response = QtWidgets.QInputDialog.getText(
            self,
            'Change Export Set Name',
            'Enter Name:',
            text=self.currentExportSet.name
        )

        if not response:

            log.info('Operation aborted...')
            return

        # Check if name is unique
        # Be sure to slugify the name before processing!
        #
        newName = self.slugify(newName)

        if not self.isNameUnique(newName) or len(newName) == 0:

            # Prompt user
            #
            response = QtWidgets.QMessageBox.warning(
                self,
                'Change Export Set Name',
                'The supplied name is not unique!',
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
            )

            if response == QtWidgets.QMessageBox.Ok:

                self.renameExportSetPushButton.click()

        else:

            # Update export set name
            #
            self.currentExportSet.name = newName

            # Update associated item text
            #
            currentIndex = self.exportSetComboBox.currentIndex()
            self.exportSetComboBox.setItemText(currentIndex, newName)

    @QtCore.Slot(bool)
    def on_reorderExportSetPushButton_clicked(self, checked=False):
        """
        Slot method for the reorderExportSetPushButton's clicked signal.

        :type checked: bool
        :rtype: None
        """

        # Check if current export set is valid
        #
        if len(self.asset.exportSets) == 0:

            log.warning('No export sets available to reorder!')
            return

        # Prompt user
        #
        dialog = qlistdialog.QListDialog('Reorder Export Sets', parent=self)
        dialog.setTextFilter(self.slugify)
        dialog.setItems([x.name for x in self.asset.exportSets])

        response = dialog.exec_()

        if not response:

            log.info('Operation aborted...')
            return

        # Reassign fbx export sets
        #
        items = dialog.items()
        numItems = len(items)

        itemLookup = {x.name: x for x in self.asset.exportSets}
        exportSets = [None] * numItems

        for i in range(numItems):

            item = items[i]
            exportSets[i] = itemLookup.get(item, fbxexportset.FbxExportSet(name=item))

        # Assign reordered list back to asset
        # All notifies will be preserved this way
        #
        self.asset.exportSets = exportSets

        self.exportSetComboBox.clear()
        self.exportSetComboBox.addItems([x.name for x in self.asset.exportSets])

    @QtCore.Slot(bool)
    def on_deleteExportSetPushButton_clicked(self, checked=False):
        """
        Slot method for the deleteExportSetPushButton's clicked signal.

        :type checked: bool
        :rtype: None
        """

        # Check if there are any sets to rename
        #
        if len(self.asset.exportSets) == 0:

            log.warning('No export sets available to delete!')
            return

        # Remove export set
        #
        currentIndex = self.exportSetComboBox.currentIndex()
        del self.asset.exportSets[currentIndex]

        # Remove associated item from combo box
        #
        self.exportSetComboBox.removeItem(currentIndex)

    @QtCore.Slot(bool)
    def on_exportPushButton_clicked(self, checked=False):
        """
        Slot method for the exportPushButton's clicked signal.

        :type checked: bool
        :rtype: None
        """

        if self.currentExportSet is not None:

            self.currentExportSet.export()

    @QtCore.Slot(bool)
    def on_exportAllPushButton_clicked(self, checked=False):
        """
        Slot method for the exportAllPushButton's clicked signal.

        :type checked: bool
        :rtype: None
        """

        for exportSet in self.asset.exportSets():

            exportSet.export()

    @QtCore.Slot(bool)
    def on_usingFbxExportSetEditorAction_triggered(self, checked=False):
        """
        Slot method for the usingFbxExportSetEditorAction's triggered signal.

        :type checked: bool
        :rtype: None
        """

        webbrowser.open('https://github.com/bhsingleton/dcc')
    # endregion
