import os
import re
import webbrowser
import unicodedata

from PySide2 import QtCore, QtWidgets, QtGui
from copy import copy
from dcc import fnnotify
from dcc.ui import quicwindow
from dcc.ui.dialogs import qlistdialog
from dcc.ui.models import qpropertyitemmodel, qpropertyitemdelegate
from dcc.fbx import fbxasset, fbxexportset, fbxnode
from dcc.fbx.io import fbxstructuredstorageio

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
        self._manager = fbxstructuredstorageio.FbxStructuredStorageIO()
        self._asset = None
        self._currentExportSet = None
        self._fnNotify = fnnotify.FnNotify()
        self._notifyId = None
    # endregion

    # region Properties
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

        # Initialize tree view model
        #
        self.exportSetItemModel = qpropertyitemmodel.QPropertyItemModel(parent=self.exportSetTreeView)
        self.exportSetTreeView.setModel(self.exportSetItemModel)

        self.exportSetItemDelegate = qpropertyitemdelegate.QPropertyItemDelegate(parent=self.exportSetTreeView)
        self.exportSetTreeView.setItemDelegate(self.exportSetItemDelegate)

        # Create tree view context menu
        #
        self.exportSetMenu = QtWidgets.QMenu(parent=self.exportSetTreeView)
        self.exportSetMenu.setObjectName('exportSetMenu')

        self.addSkeletonAction = QtWidgets.QAction(QtGui.QIcon(':dcc/icons/skeleton'), 'Add Skeleton', parent=self.exportSetMenu)
        self.addSkeletonAction.setObjectName('addSkeletonAction')

        self.addMaterialSlotAction = QtWidgets.QAction(QtGui.QIcon(':dcc/icons/material'), 'Add Material Slot', parent=self.exportSetMenu)
        self.addMaterialSlotAction.setObjectName('addMaterialSlotAction')

        self.addMeshAction = QtWidgets.QAction(QtGui.QIcon(':dcc/icons/mesh'), 'Add Mesh', parent=self.exportSetMenu)
        self.addMeshAction.setObjectName('addMeshAction')

        self.exportSetMenu.addActions([self.addSkeletonAction, self.addMaterialSlotAction, self.addMeshAction])

    @staticmethod
    def slugify(name):
        """
        Normalizes string by removing non-alpha characters and converting spaces to underscores.
        See the following for more details: https://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename

        :type name: str
        :rtype: str
        """

        name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
        name = re.sub(r'[^\w\s-]', '', name).strip()
        name = re.sub(r'[-\s]+', '_', name)

        return name

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
        #self.fileTypeComboBox.setCurrentIndex(self.asset.fileType)
        self.fileVersionComboBox.setCurrentIndex(self.asset.fileVersion)
        self.exportSetComboBox.addItems([x.name for x in self.asset.exportSets])

    def invalidateExportSet(self):
        """
        Invalidates the displayed export set settings.

        :rtype: None
        """

        # Attach export set to item model
        #
        self.exportSetItemModel.setInvisibleRootItem(self.currentExportSet.children)

        # Synchronize export set widgets
        #
        self.scaleSpinBox.value = self.currentExportSet.scale
        self.exportDirectoryLineEdit.setText(self.currentExportSet.directory)

        for button in self.meshSettingsCheckBoxGroup.buttons():

            name = button.whatsThis()
            isChecked = getattr(self.currentExportSet, name, False)

            button.setChecked(isChecked)

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
        self._notifyId = self._fnNotify.addPostFileOpenNotify(self.sceneChanged)
        self.invalidateAsset()

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
        self._fnNotify.removeNotify(self._notifyId)
    # endregion

    # region Slots
    @QtCore.Slot(bool)
    def on_saveAction_triggered(self, checked=False):
        """
        Clicked slot method that saves all recent changes.

        :type checked: bool
        :rtype: None
        """

        self._manager.saveAsset(self.asset)  # This will mark the scene as dirty!

    @QtCore.Slot(bool)
    def on_saveAsAction_triggered(self, checked=False):
        """
        Clicked slot method that saves the current asset to a json file.

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

            self._manager.saveAssetAs(self.asset, filePath)

        else:

            log.info('Operation aborted...')

    @QtCore.Slot(bool)
    def on_importAction_triggered(self, checked=False):
        """
        Clicked slot method that imports asset settings from a json file.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(bool)
    def on_usingFbxExportSetEditor_triggered(self, checked=False):
        """
        Clicked slot method responsible for saving all recent changes.

        :type checked: bool
        :rtype: None
        """

        webbrowser.open('https://github.com/bhsingleton/dcc')

    @QtCore.Slot(str)
    def on_assetNameLineEdit_textChanged(self, text):
        """
        Text changed slot method responsible for updating the asset name.

        :type text: str
        :rtype: None
        """

        self.asset.name = text

    @QtCore.Slot(str)
    def on_assetDirectoryLineEdit_textChanged(self, text):
        """
        Text changed slot method responsible for updating the asset directory.

        :type text: str
        :rtype: None
        """

        self.asset.directory = os.path.normpath(text)
        self.invalidateExportPath()

    @QtCore.Slot(bool)
    def on_assetDirectoryPushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for updating the asset directory.

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
        Clicked slot method responsible for updating the fbx file type.

        :type index: int
        :rtype: None
        """

        self.asset.fileType = index

    @QtCore.Slot(int)
    def on_fileVersionComboBox_currentIndexChanged(self, index):
        """
        Current index changed slot method responsible for updating the fbx file version.

        :type index: int
        :rtype: None
        """

        self.asset.fileVersion = index

    @QtCore.Slot(int)
    def on_exportSetComboBox_currentIndexChanged(self, index):
        """
        Current index changed slot method responsible for updating the current fbx export set.

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
        Clicked slot method responsible for creating a new fbx export set.

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
        name = self.slugify(name)

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
        Clicked slot method responsible for duplicating the current fbx export set.

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
        fbxExportSet = copy.copy(self.currentExportSet)
        fbxExportSet.name = self.uniquify(fbxExportSet.name)

        self.asset.exportSets.append(fbxExportSet)

        # Add item to combo box
        #
        self.exportSetComboBox.addItem(fbxExportSet.name)

    @QtCore.Slot(bool)
    def on_renameExportSetPushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for renaming the current fbx export set.

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
        Clicked slot method responsible for reordering the fbx export sets.

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
        Clicked slot method responsible for deleting the current fbx export set.

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

    @QtCore.Slot(QtCore.QPoint)
    def on_exportSetTreeView_customContextMenuRequested(self, pos):
        """
        Custom context menu requested slot method responsible executing the export set menu.

        :type pos: QtCore.QPoint
        :rtype: None
        """

        sender = self.sender()
        globalPos = sender.mapToGlobal(pos)

        self.exportSetMenu.exec_(globalPos)

    @QtCore.Slot(bool)
    def on_addSkeletonAction_triggered(self, checked=False):
        """
        Triggered slot method responsible for adding a skeleton object.

        :type checked: bool
        :rtype: None
        """

        skeleton = fbxnode.FbxSkeleton()
        self.exportSetItemModel.appendRow(skeleton)

    @QtCore.Slot(bool)
    def on_addMaterialSlotAction_triggered(self, checked=False):
        """
        Triggered slot method responsible for adding a material slot object.

        :type checked: bool
        :rtype: None
        """

        material = fbxnode.FbxMaterialSlot()
        self.exportSetItemModel.appendRow(material)

    @QtCore.Slot(bool)
    def on_addMeshAction_triggered(self, checked=False):
        """
        Triggered slot method responsible for adding a mesh object.

        :type checked: bool
        :rtype: None
        """

        mesh = fbxnode.FbxMesh()
        self.exportSetItemModel.appendRow(mesh)

    @QtCore.Slot(bool)
    def on_customScriptsPushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for opening the custom script dialog.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(bool)
    def on_exportDirectoryPushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for updating the export directory.

        :type checked: bool
        :rtype: None
        """

        # Prompt user for save path
        #
        assetDirectory = os.path.expandvars(self.asset.directory)

        exportDirectory = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption='Select Export Directory',
            dir=assetDirectory,
            options=QtWidgets.QFileDialog.ShowDirsOnly
        )

        # Check if path is valid
        #
        if exportDirectory and self.currentExportSet is not None:

            relativePath = os.path.relpath(os.path.normpath(exportDirectory), os.path.normpath(assetDirectory))
            self.currentExportSet.directory = relativePath

        else:

            log.info('Operation aborted...')

    @QtCore.Slot(str)
    def on_exportDirectoryLineEdit_textChanged(self, text):
        """
        Text changed slot method responsible for updating the export directory.

        :type text: str
        :rtype: None
        """

        if self.currentExportSet is not None:

            self.currentExportSet.directory = os.path.normpath(text)
            self.invalidateExportPath()

    @QtCore.Slot(float)
    def on_scaleSpinBox_valueChanged(self, value):
        """
        Value changed slot method responsible for updating the scale value.

        :type value: float
        :rtype: None
        """

        if self.currentExportSet is not None:

            self.currentExportSet.scale = value

    @QtCore.Slot(int)
    def on_meshSettingsCheckBoxGroup_idClicked(self, index):
        """
        Id clicked slot method responsible for updating the associated property.

        :type index: int
        :rtype: None
        """

        if self.currentExportSet is not None:

            group = self.sender()
            checkBox = group.button(index)

            setattr(self.currentExportSet, checkBox.whatsThis(), checkBox.isChecked())

    @QtCore.Slot(bool)
    def on_exportPushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for exporting the current fbx export set.

        :type checked: bool
        :rtype: None
        """

        if self.currentExportSet is not None:

            self.currentExportSet.export()

    @QtCore.Slot(bool)
    def on_exportAllPushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for exporting all the fbx export sets.

        :type checked: bool
        :rtype: None
        """

        for exportSet in self.asset.exportSets():

            exportSet.export()
    # endregion
