import os
import webbrowser

from Qt import QtCore, QtWidgets, QtGui
from copy import copy
from dcc import fnscene, fnnode, fnskin, fnnotify
from dcc.python import stringutils
from dcc.json import jsonutils
from dcc.ui import quicwindow, qdirectoryedit, qfileedit
from dcc.ui.dialogs import qlistdialog
from dcc.ui.models import qpsonitemmodel, qpsonstyleditemdelegate
from dcc.fbx.libs import fbxio, fbxasset, fbxexportset, fbxscript

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QFbxExportSetEditor(quicwindow.QUicWindow):
    """
    Overload of `QUicWindow` used to edit FBX export-set data.
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

        # Declare private variables
        #
        self._manager = fbxio.FbxIO()
        self._asset = None
        self._currentExportSet = None
        self._scene = fnscene.FnScene()
        self._notifies = fnnotify.FnNotify()

        # Declare public variables
        #
        self.fileMenu = None
        self.saveAction = None
        self.saveAsAction = None
        self.importAction = None
        self.exportAction = None

        self.settingsMenu = None
        self.useBuiltinSerializerAction = None
        self.generateLogsAction = None

        self.helpMenu = None
        self.usingFbxExportSetEditorAction = None

        self.assetGroupBox = None
        self.assetNameWidget = None
        self.assetNameLabel = None
        self.assetNameLineEdit = None
        self.savePushButton = None
        self.assetDirectoryWidget = None
        self.assetDirectoryLabel = None
        self.assetDirectoryLineEdit = None
        self.assetDirectoryPushButton = None
        self.fileTypeWidget = None
        self.fileTypeLabel = None
        self.fileTypeComboBox = None
        self.fileVersionWidget = None
        self.fileVersionLabel = None
        self.fileVersionComboBox = None

        self.exportSetGroupBox = None
        self.exportSetComboBox = None
        self.exportSetInteropWidget = None
        self.newExportSetPushButton = None
        self.duplicateExportSetPushButton = None
        self.renameExportSetPushButton = None
        self.reorderExportSetPushButton = None
        self.deleteExportSetPushButton = None
        self.exportSetTreeView = None
        self.exportSetItemModel = None
        self.exportSetItemDelegate = None

        self.exportGroupBox = None
        self.exportPathWidget = None
        self.exportPathLineEdit = None
        self.checkoutCheckBox = None
        self.exportInteropWidget = None
        self.exportPushButton = None
        self.exportAllPushButton = None

        self.customContextMenu = None
        self.copySelectionAction = None
        self.copyInfluencesAction = None
        self.clearItemsAction = None
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
    def postLoad(self, *args, **kwargs):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        # Call parent method
        #
        super(QFbxExportSetEditor, self).postLoad(*args, **kwargs)

        # Initialize tree view model
        #
        self.exportSetItemModel = qpsonitemmodel.QPSONItemModel(parent=self.exportSetTreeView)
        self.exportSetItemModel.setObjectName('exportSetItemModel')

        self.exportSetTreeView.setModel(self.exportSetItemModel)

        self.exportSetItemDelegate = qpsonstyleditemdelegate.QPSONStyledItemDelegate(parent=self.exportSetTreeView)
        self.exportSetItemDelegate.setObjectName('exportSetItemDelegate')

        self.exportSetTreeView.setItemDelegate(self.exportSetItemDelegate)

        # Initialize file menu
        #
        self.saveAction = QtWidgets.QAction(QtGui.QIcon(':dcc/icons/save.svg'), '&Save', parent=self.fileMenu)
        self.saveAction.setObjectName('saveAction')
        self.saveAction.triggered.connect(self.on_saveAction_triggered)

        self.importAction = QtWidgets.QAction(QtGui.QIcon(':dcc/icons/import.svg'), '&Import', parent=self.fileMenu)
        self.importAction.setObjectName('importAction')
        self.importAction.triggered.connect(self.on_importAction_triggered)

        self.exportAction = QtWidgets.QAction(QtGui.QIcon(':dcc/icons/export.svg'), '&Export', parent=self.fileMenu)
        self.exportAction.setObjectName('exportAction')
        self.exportAction.triggered.connect(self.on_exportAction_triggered)

        self.fileMenu.addAction(self.saveAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addActions([self.importAction, self.exportAction])

        # Initialize settings menu
        #
        self.useBuiltinSerializerAction = QtWidgets.QAction('Use Builtin Serializer', parent=self.settingsMenu)
        self.useBuiltinSerializerAction.setObjectName('useBuiltinSerializerAction')
        self.useBuiltinSerializerAction.setCheckable(True)
        self.useBuiltinSerializerAction.triggered.connect(self.on_useBuiltinSerializerAction_triggered)

        self.generateLogsAction = QtWidgets.QAction('Generate Logs', parent=self.settingsMenu)
        self.generateLogsAction.setObjectName('generateLogsActions')
        self.generateLogsAction.setCheckable(True)

        self.settingsMenu.addActions([self.useBuiltinSerializerAction, self.generateLogsAction])

        # Initialize help menu
        #
        self.usingFbxExportSetEditorAction = QtWidgets.QAction('Using Fbx Export Set Editor', parent=self.helpMenu)
        self.usingFbxExportSetEditorAction.setObjectName('usingFbxExportSetEditorAction')
        self.usingFbxExportSetEditorAction.triggered.connect(self.on_usingFbxExportSetEditorAction_triggered)

        # Initialize custom context menu
        #
        self.customContextMenu = QtWidgets.QMenu(parent=self.exportSetTreeView)
        self.customContextMenu.setObjectName('customContextMenu')

        self.copySelectionAction = QtWidgets.QAction('Copy Selection', parent=self.customContextMenu)
        self.copySelectionAction.setObjectName('copySelectionAction')
        self.copySelectionAction.triggered.connect(self.on_copySelectionAction_triggered)

        self.copyInfluencesAction = QtWidgets.QAction('Copy Influences', parent=self.customContextMenu)
        self.copyInfluencesAction.setObjectName('copyInfluencesAction')
        self.copyInfluencesAction.triggered.connect(self.on_copyInfluencesAction_triggered)

        self.clearItemsAction = QtWidgets.QAction('Clear Items', parent=self.customContextMenu)
        self.clearItemsAction.setObjectName('clearItemsAction')
        self.clearItemsAction.triggered.connect(self.on_clearItemsAction_triggered)

        self.customContextMenu.addActions([self.copySelectionAction, self.copyInfluencesAction])
        self.customContextMenu.addSeparator()
        self.customContextMenu.addAction(self.clearItemsAction)

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

    def reloadAsset(self):
        """
        Reloads the asset from the current scene file.

        :rtype: None
        """

        # Load scene asset
        # If no asset exists then create an empty asset!
        #
        self._asset = self._manager.loadAsset()

        if self._asset is None:

            self._asset = fbxasset.FbxAsset()

        # Invalidate user interface
        #
        self.invalidateAsset()

    def invalidateAsset(self):
        """
        Invalidates the asset related widgets.

        :rtype: None
        """

        # Synchronize asset widgets
        #
        self.assetNameLineEdit.setText(self.asset.name)
        self.assetDirectoryLineEdit.setText(self.asset.directory)
        self.fileTypeComboBox.setCurrentIndex(self.asset.fileType)
        self.fileVersionComboBox.setCurrentIndex(self.asset.fileVersion)
        self.useBuiltinSerializerAction.setChecked(self.asset.useBuiltinSerializer)

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

        self.reloadAsset()
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

        # Add post file-open notify
        #
        self._notifies.addPostFileOpenNotify(self.sceneChanged)
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

        # Clear notifies
        #
        self._notifies.clear()
    # endregion

    # region Slots
    @QtCore.Slot(bool)
    def on_saveAction_triggered(self, checked=False):
        """
        Slot method for the saveAction's triggered signal.

        :type checked: bool
        :rtype: None
        """

        self.manager.saveAsset(self.asset)
        self.scene.save()

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

        # Prompt user for import path
        #
        importPath, selectedFilter = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption='Import from',
            dir=self.scene.currentDirectory(),
            filter='JSON files (*.json)'
        )

        # Check if path is valid
        #
        if not stringutils.isNullOrEmpty(importPath):

            self._asset = jsonutils.load(importPath)
            self.invalidateAsset()

        else:

            log.info('Operation aborted...')

    @QtCore.Slot(bool)
    def on_exportAction_triggered(self, checked=False):
        """
        Slot method for the exportAction's triggered signal.

        :type checked: bool
        :rtype: None
        """

        # Prompt user for export path
        #
        exportPath, selectedFilter = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption='Export to',
            dir=self.scene.currentDirectory(),
            filter='JSON files (*.json)'
        )

        # Check if path is valid
        #
        if not stringutils.isNullOrEmpty(exportPath):

            jsonutils.dump(exportPath, self.asset, indent=4)

        else:

            log.info('Operation aborted...')

    @QtCore.Slot(str)
    def on_assetNameLineEdit_textChanged(self, text):
        """
        Slot method for the assetNameLineEdit's textChanged signal.

        :type text: str
        :rtype: None
        """

        self.asset.name = text

    @QtCore.Slot(bool)
    def on_useBuiltinSerializerAction_triggered(self, checked=False):
        """
        Slot method for the useBuiltinSerializerAction's triggered signal.

        :type checked: bool
        :rtype: None
        """

        self.asset.useBuiltinSerializer = checked

    @QtCore.Slot(bool)
    def on_savePushButton_clicked(self, checked=False):
        """
        Slot method for the savePushButton's clicked signal.

        :type checked: bool
        :rtype: None
        """

        self.manager.saveAsset(self.asset)
        self.scene.save()
        
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

        if name in ('includeObjects', 'excludeObjects'):

            globalPoint = self.sender().mapToGlobal(point)
            self.customContextMenu.exec_(globalPoint)

        else:

            pass

    @QtCore.Slot(bool)
    def on_copySelectionAction_triggered(self, checked=False):
        """
        Slot method for the copySelectionAction's triggered signal.

        :type checked: bool
        :rtype: None
        """

        # Evaluate selected indices
        #
        indices = [index for index in self.exportSetTreeView.selectedIndexes() if index.column() == 0]
        numIndices = len(indices)

        if numIndices != 1:

            return

        # Get pre-existing names
        #
        index = indices[0]
        model = index.model()

        currentNames = model.itemFromIndex(index)

        # Extend row using selection
        #
        node = fnnode.FnNode()
        selectedNames = [node(obj).name() for obj in self.scene.getActiveSelection()]

        nodeNames = [nodeName for nodeName in selectedNames if nodeName not in currentNames]

        # Extend row from node names
        #
        numNodeNames = len(nodeNames)

        if numNodeNames > 0:

            model.extendRow(nodeNames, parent=index)

    @QtCore.Slot(bool)
    def on_copyInfluencesAction_triggered(self, checked=False):
        """
        Slot method for the copySelectionAction's triggered signal.

        :type checked: bool
        :rtype: None
        """

        # Evaluate selected indices
        #
        indices = [index for index in self.exportSetTreeView.selectedIndexes() if index.column() == 0]
        numIndices = len(indices)

        if numIndices != 1:

            return

        # Get pre-existing names
        #
        index = indices[0]
        model = index.model()

        currentNames = model.itemFromIndex(index)

        # Collect used influence names
        #
        skin = fnskin.FnSkin()
        influenceNames = []

        for obj in self.scene.getActiveSelection():

            # Check if object is valid
            #
            success = skin.trySetObject(obj)

            if not success:

                continue

            # Extend influence names
            #
            influences = skin.influences()
            usedInfluenceIds = skin.getUsedInfluenceIds()
            usedInfluenceNames = [influences[influenceId].name() for influenceId in usedInfluenceIds]

            influenceNames.extend([influenceName for influenceName in usedInfluenceNames if influenceName not in currentNames])

        # Extend row from influence names
        #
        numInfluenceNames = len(influenceNames)

        if numInfluenceNames > 0:

            model.extendRow(influenceNames, parent=index)

    @QtCore.Slot(bool)
    def on_clearItemsAction_triggered(self, checked=False):
        """
        Slot method for the clearItemsAction's triggered signal.

        :type checked: bool
        :rtype: None
        """

        # Evaluate selected indices
        #
        indices = [index for index in self.exportSetTreeView.selectedIndexes() if index.column() == 0]
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
        newName = stringutils.slugify(newName)

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

                self.renameExportSetPushButton.click()  # Redo operation!

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
        dialog.setTextFilter(stringutils.slugify)
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

        # Check if export set exists
        #
        if self.currentExportSet is None:

            QtWidgets.QMessageBox.warning(self, 'Export Set', 'No set available to export!')
            return

        # Export current set
        #
        checkout = self.checkoutCheckBox.isChecked()
        self.currentExportSet.export(checkout=checkout)

    @QtCore.Slot(bool)
    def on_exportAllPushButton_clicked(self, checked=False):
        """
        Slot method for the exportAllPushButton's clicked signal.

        :type checked: bool
        :rtype: None
        """

        # Check if export set exists
        #
        if self.asset is None:

            QtWidgets.QMessageBox.warning(self, 'Export Sets', 'No asset available to export from!')
            return

        # Export all sets
        #
        checkout = self.checkoutCheckBox.isChecked()

        for exportSet in self.asset.exportSets:

            exportSet.export(checkout=checkout)

    @QtCore.Slot(bool)
    def on_usingFbxExportSetEditorAction_triggered(self, checked=False):
        """
        Slot method for the usingFbxExportSetEditorAction's triggered signal.

        :type checked: bool
        :rtype: None
        """

        webbrowser.open('https://github.com/bhsingleton/dcc')
    # endregion
