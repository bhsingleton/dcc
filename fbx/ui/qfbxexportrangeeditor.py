import math
import os

from Qt import QtWidgets, QtCore, QtGui
from dcc import fnscene, fnreference, fnnotify
from dcc.generators.consecutivepairs import consecutivePairs
from dcc.ui import quicwindow
from dcc.ui.models import qpsonitemmodel, qpsonstyleditemdelegate
from dcc.fbx.libs import fbxio, fbxsequencer, fbxexportrange
from dcc.python import stringutils
from dcc.json import jsonutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QFbxExportRangeEditor(quicwindow.QUicWindow):
    """
    Overload of `QUicWindow` used to edit FBX export-range data.
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
        super(QFbxExportRangeEditor, self).__init__(*args, **kwargs)

        # Define private variables
        #
        self._manager = fbxio.FbxIO()
        self._sequencers = []
        self._currentSequencer = None
        self._scene = fnscene.FnScene()
        self._notifies = fnnotify.FnNotify()

        # Declare public variables
        #
        self.mainToolbar = None
        self.newSequencerAction = None
        self.saveSequencerAction = None
        self.importRangesAction = None
        self.exportRangesAction = None
        self.addExportRangeAction = None
        self.removeExportRangeAction = None
        self.updateStartTimeAction = None
        self.updateEndTimeAction = None
        self.updateTimeRangeAction = None

        self.sequencerRollout = None
        self.sequencerInteropWidget = None
        self.deleteSequencerPushButton = None
        self.sequencerComboBox = None
        self.sequencerTreeView = None
        self.sequencerItemModel = None
        self.sequencerItemDelegate = None
        self.exportWidget = None
        self.exportDividerWidget = None
        self.exportLabel = None
        self.exportLine = None
        self.exportPathWidget = None
        self.exportPathLineEdit = None
        self.checkoutCheckBox = None
        self.exportInteropWidget = None
        self.exportPushButton = None
        self.exportAllPushButton = None

        self.batchRollout = None
        self.fileDividerWidget = None
        self.fileDividerLabel = None
        self.fileDividerLine = None
        self.fileInteropWidget = None
        self.addFilesPushButton = None
        self.removeFilesPushButton = None
        self.fileListWidget = None
        self.batchPathWidget = None
        self.batchPathLabel = None
        self.batchPathLineEdit = None
        self.batchPathPushButton = None
        self.batchProgressBar = None
        self.batchPushButton = None
    # endregion

    # region Properties
    @property
    def manager(self):
        """
        Getter method that returns the fbx sequencer manager.

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
    def sequencers(self):
        """
        Getter method that returns the active fbx sequencers.

        :rtype: List[fbxsequencer.FbxSequencer]
        """

        return self._sequencers

    @property
    def currentSequencer(self):
        """
        Getter method that returns the current fbx sequencer.

        :rtype: fbxsequencer.FbxSequencer
        """

        return self._currentSequencer

    @property
    def checkout(self):
        """
        Getter method that returns the checkout state.

        :rtype: bool
        """

        return self.checkoutCheckBox.isChecked()

    @checkout.setter
    def checkout(self, checkout):
        """
        Setter method that updates the checkout state.

        :type checkout: bool
        :rtype: None
        """

        self.checkoutCheckBox.setChecked(checkout)
    # endregion

    # region Methods
    def postLoad(self, *args, **kwargs):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        # Call parent method
        #
        super(QFbxExportRangeEditor, self).postLoad()

        # Edit sequencer/batch rollouts
        #
        self.sequencerRollout.setText('Sequencers')
        self.sequencerRollout.setExpanded(True)

        self.batchRollout.setText('Batch')
        self.batchRollout.setExpanded(False)

        self.centralWidget().layout().setAlignment(QtCore.Qt.AlignTop)

        # Initialize sequencer tree view model
        #
        self.sequencerItemModel = qpsonitemmodel.QPSONItemModel(parent=self.sequencerTreeView)
        self.sequencerItemModel.setObjectName('sequencerItemModel')
        self.sequencerItemModel.invisibleRootProperty = 'exportRanges'

        self.sequencerTreeView.setModel(self.sequencerItemModel)

        self.sequencerItemDelegate = qpsonstyleditemdelegate.QPSONStyledItemDelegate(parent=self.sequencerTreeView)
        self.sequencerItemDelegate.setObjectName('sequencerItemDelegate')

        self.sequencerTreeView.setItemDelegate(self.sequencerItemDelegate)

    def saveSettings(self, settings):
        """
        Saves the user settings.

        :type settings: QtCore.QSettings
        :rtype: None
        """

        # Call parent method
        #
        super(QFbxExportRangeEditor, self).saveSettings(settings)

        # Save user settings
        #
        settings.setValue('editor/checkout', int(self.checkout))

    def loadSettings(self, settings):
        """
        Loads the user settings.

        :type settings: QtCore.QSettings
        :rtype: None
        """

        # Call parent method
        #
        super(QFbxExportRangeEditor, self).loadSettings(settings)

        # Load user settings
        #
        self.checkout = bool(settings.value('editor/checkout', defaultValue=1))

    def defaultExportRange(self):
        """
        Returns a new export-range using the current scene settings.

        :rtype: fbxexportrange.FbxExportRange
        """

        name = os.path.splitext(self.scene.currentFilename())[0]
        startFrame, endFrame = self.scene.getStartTime(), self.scene.getEndTime()

        return fbxexportrange.FbxExportRange(name=name, startFrame=startFrame, endFrame=endFrame, useTimeline=False)

    def getSelectedRows(self):
        """
        Returns the selected rows from the tree view.

        :rtype: List[int]
        """

        return [self.sequencerItemModel.topLevelIndex(index).row() for index in self.sequencerTreeView.selectedIndexes() if index.column() == 0]

    def invalidateSequencers(self):
        """
        Invalidates the sequencers displayed inside the combo box.

        :rtype: None
        """

        # Cache current index
        #
        index = self.sequencerComboBox.currentIndex()

        # Re-populate combo box
        #
        filePaths = [sequencer.reference.filePath() for sequencer in self.sequencers]
        numFilePaths = len(filePaths)

        self.sequencerComboBox.clear()
        self.sequencerComboBox.addItems(filePaths)

        if 0 <= index < numFilePaths:

            self.sequencerComboBox.setCurrentIndex(index)

    def invalidateExportRanges(self):
        """
        Invalidates the export-ranges displayed inside the tree view.

        :rtype: None
        """

        self.sequencerItemModel.invisibleRootItem = self.currentSequencer
        self.sequencerTreeView.expandToDepth(1)

    def invalidateExportPath(self):
        """
        Invalidates the displayed export path.

        :rtype: None
        """

        selectedRows = self.getSelectedRows()
        numSelectedRows = len(selectedRows)

        if numSelectedRows:

            selectedRow = selectedRows[0]
            exportPath = self.currentSequencer.exportRanges[selectedRow].exportPath()

            self.exportPathLineEdit.setText(exportPath)
    # endregion

    # region Callbacks
    def sceneChanged(self, *args, **kwargs):
        """
        Post file-open callback that invalidates the current asset.

        :rtype: None
        """

        self.sequencers.clear()
        self.sequencers.extend(self.manager.loadSequencers())

        self.invalidateSequencers()
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
        super(QFbxExportRangeEditor, self).showEvent(event)

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
        super(QFbxExportRangeEditor, self).closeEvent(event)

        # Clear notifies
        #
        self._notifies.clear()
    # endregion

    # region Methods
    def save(self):
        """
        Commits any changes to the file properties.

        :rtype: None
        """

        if not self.scene.isReadOnly():

            self.manager.saveSequencers(self.sequencers)
            self.scene.save()

        else:

            log.warning('Cannot save changes to read-only scene file!')
    # endregion

    # region Slots
    @QtCore.Slot(int)
    def on_sequencerComboBox_currentIndexChanged(self, index):
        """
        Slot method for the sequencerComboBox's `currentIndexChanged` signal.

        :type index: int
        :rtype: None
        """

        # Update current sequencer
        #
        numSequencers = len(self.sequencers)

        if 0 <= index < numSequencers:

            self._currentSequencer = self.sequencers[index]

        else:

            self._currentSequencer = None

        # Invalidate sequences
        #
        self.invalidateExportRanges()

    @QtCore.Slot(QtCore.QModelIndex)
    def on_sequencerTreeView_clicked(self, index):
        """
        Slot method for the sequencerTreeView's `clicked` signal.

        :type index: QtCore.QModelIndex
        :rtype: None
        """

        self.invalidateExportPath()

    @QtCore.Slot(bool)
    def on_newSequencerAction_triggered(self, checked=False):
        """
        Slot method for the newSequencerAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        # Collect references from scene
        #
        reference = fnreference.FnReference()

        references = list(reference.iterSceneReferences(topLevelOnly=False))
        numReferences = len(references)

        if numReferences == 0:

            QtWidgets.QMessageBox.information(self, 'Create Sequencer', 'Scene contains no references!')
            return

        # Collect potential sequencers
        #
        currentPaths = [self.sequencerComboBox.itemText(i) for i in range(self.sequencerComboBox.count())]
        referencePaths = [reference(obj).filePath() for obj in references]

        filteredPaths = [path for path in referencePaths if path not in currentPaths]
        numFilteredPaths = len(filteredPaths)

        if numFilteredPaths == 0:

            QtWidgets.QMessageBox.information(self, 'Create Sequencer', 'Scene contains no more references!')
            return

        # Prompt user for referenced asset
        #
        item, okay = QtWidgets.QInputDialog.getItem(
            self,
            'Create Sequencer',
            'Select a Referenced Asset:',
            filteredPaths,
            editable=False
        )

        if okay:

            index = referencePaths.index(item)
            guid = reference(references[index]).guid()
            exportRange = self.defaultExportRange()

            sequencer = fbxsequencer.FbxSequencer(guid=guid, exportRanges=[exportRange])
            self.sequencers.append(sequencer)

            self.invalidateSequencers()

            lastIndex = len(self.sequencers) - 1
            self.sequencerComboBox.setCurrentIndex(lastIndex)

        else:

            log.info('Operation aborted...')

    @QtCore.Slot(bool)
    def on_deleteSequencerPushButton_clicked(self, checked=False):
        """
        Slot method for the deleteSequencerAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        # Redundancy check
        #
        if len(self.sequencers) == 0:

            return

        # Confirm user wants to delete sequencer
        #
        response = QtWidgets.QMessageBox.warning(
            self,
            'Delete Sequencer',
            'Are you sure you want to delete this sequencer and all of its export ranges?',
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
        )

        if response != QtWidgets.QMessageBox.Ok:

            log.info('Operation aborted...')
            return

        # Remove selected sequencer
        #
        index = self.sequencerComboBox.currentIndex()
        del self.sequencers[index]

        # Invalidate export-ranges
        #
        self.invalidateSequencers()

    @QtCore.Slot(bool)
    def on_saveSequencerAction_triggered(self, checked=False):
        """
        Slot method for the saveSequencerAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        self.save()

    @QtCore.Slot(bool)
    def on_addExportRangeAction_triggered(self, checked=False):
        """
        Slot method for the addExportRangeAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        exportRange = self.defaultExportRange()
        self.sequencerItemModel.appendRow(exportRange)

    @QtCore.Slot(bool)
    def on_removeExportRangeAction_triggered(self, checked=False):
        """
        Slot method for the removeExportRangeAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        # Check if there are any rows remaining
        # We want to make sure there's always at least one export range remaining!
        #
        rowCount = self.sequencerItemModel.rowCount()

        if not (rowCount > 1):

            return

        # Remove selected rows
        #
        selectedRows = self.getSelectedRows()

        for (start, end) in reversed(tuple(consecutivePairs(selectedRows))):

            numRows = (end - start) + 1
            self.sequencerItemModel.removeRows(start, numRows)

    @QtCore.Slot(bool)
    def on_importRangesAction_triggered(self, checked=False):
        """
        Slot method for the importRangesAction's `triggered` signal.

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

            self.currentSequencer.exportRanges = jsonutils.load(importPath)
            self.invalidateExportRanges()

        else:

            log.info('Operation aborted...')

    @QtCore.Slot(bool)
    def on_exportRangesAction_triggered(self, checked=False):
        """
        Slot method for the exportRangesAction's `triggered` signal.

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

            jsonutils.dump(exportPath, self.currentSequencer.exportRanges, indent=4)

        else:

            log.info('Operation aborted...')

    @QtCore.Slot(bool)
    def on_updateStartTimeAction_triggered(self, checked=False):
        """
        Slot method for the updateStartTimeAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        # Get selected rows
        #
        selectedRows = self.getSelectedRows()
        numSelectedRows = len(selectedRows)

        if numSelectedRows == 0:

            return

        # Evaluate keyboard modifiers
        #
        keyboardModifiers = QtWidgets.QApplication.keyboardModifiers()

        if keyboardModifiers == QtCore.Qt.ShiftModifier:  # Copy start frame

            for row in selectedRows:

                self.currentSequencer.exportRanges[row].startFrame = self.scene.getStartTime()

        else:

            row = selectedRows[0]
            self.scene.setStartTime(self.currentSequencer.exportRanges[row].startFrame)

    @QtCore.Slot(bool)
    def on_updateEndTimeAction_triggered(self, checked=False):
        """
        Slot method for the updateEndTimeAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        # Get selected rows
        #
        selectedRows = self.getSelectedRows()
        numSelectedRows = len(selectedRows)

        if numSelectedRows == 0:

            return

        # Evaluate keyboard modifiers
        #
        keyboardModifiers = QtWidgets.QApplication.keyboardModifiers()

        if keyboardModifiers == QtCore.Qt.ShiftModifier:  # Copy start frame

            for row in selectedRows:

                self.currentSequencer.exportRanges[row].endFrame = self.scene.getEndTime()

        else:

            row = selectedRows[0]
            self.scene.setEndTime(self.currentSequencer.exportRanges[row].endFrame)

    @QtCore.Slot(bool)
    def on_updateTimeRangeAction_triggered(self, checked=False):
        """
        Slot method for the updateTimeRangeAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        # Get selected rows
        #
        selectedRows = self.getSelectedRows()
        numSelectedRows = len(selectedRows)

        if numSelectedRows == 0:

            return

        # Evaluate keyboard modifiers
        #
        keyboardModifiers = QtWidgets.QApplication.keyboardModifiers()

        if keyboardModifiers == QtCore.Qt.ShiftModifier:  # Copy start frame

            for row in selectedRows:

                self.currentSequencer.exportRanges[row].startFrame = self.scene.getStartTime()
                self.currentSequencer.exportRanges[row].endFrame = self.scene.getEndTime()

        else:

            row = selectedRows[0]
            self.scene.setStartTime(self.currentSequencer.exportRanges[row].startFrame)
            self.scene.setEndTime(self.currentSequencer.exportRanges[row].endFrame)

    @QtCore.Slot(bool)
    def on_exportPushButton_clicked(self, checked=False):
        """
        Slot method for the exportPushButton's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

        # Check if sequencer exists
        #
        if self.currentSequencer is None:

            QtWidgets.QMessageBox.warning(self, 'Export Ranges', 'No sequencer available to export from!')
            return

        # Export selected range
        #
        self.save()

        for row in self.getSelectedRows():

            self.currentSequencer.exportRanges[row].export(checkout=self.checkout)

    @QtCore.Slot(bool)
    def on_exportAllPushButton_clicked(self, checked=False):
        """
        Slot method for the exportAllPushButton's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

        # Check if sequencer exists
        #
        if self.currentSequencer is None:

            QtWidgets.QMessageBox.warning(self, 'Export Ranges', 'No sequencer available to export from!')
            return

        # Export all ranges
        #
        self.save()

        for exportRange in self.currentSequencer.exportRanges:

            exportRange.export(checkout=self.checkout)

    @QtCore.Slot(bool)
    def on_addFilesPushButton_clicked(self, checked=False):
        """
        Slot method for the addFilesPushButton's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

        # Evaluate keyboard modifiers
        #
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        currentPaths = [self.fileListWidget.item(i).text() for i in range(self.fileListWidget.count())]

        if modifiers == QtCore.Qt.ShiftModifier:

            # Add open scene file to list
            #
            filePath = self.scene.currentFilePath()

            if filePath not in currentPaths:

                self.fileListWidget.addItem(filePath)

        else:

            # Prompt user for scene files
            #
            filePaths, selectedFilter = QtWidgets.QFileDialog.getOpenFileNames(
                self,
                'Select files to batch',
                self.scene.currentDirectory(),
                f"Scene files ({' '.join([f'*.{extension.name}' for extension in self.scene.extensions()])})"
            )

            if not stringutils.isNullOrEmpty(filePaths):

                # Add new scene files to list
                #
                filteredPaths = [filePath for filePath in filePaths if filePath not in currentPaths]

                for filePath in filteredPaths:

                    self.fileListWidget.addItem(filePath)

            else:

                log.info('Operation aborted...')

    @QtCore.Slot(bool)
    def on_removeFilesPushButton_clicked(self, checked=False):
        """
        Slot method for the removeFilesPushButton's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

        # Iterate through selected items
        #
        selectedItems = self.fileListWidget.selectedItems()

        for selectedItem in reversed(selectedItems):

            row = self.fileListWidget.row(selectedItem)
            self.fileListWidget.takeItem(row)

    @QtCore.Slot(bool)
    def on_batchPathPushButton_clicked(self, checked=False):
        """
        Slot method for the batchPathPushButton's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

        # Prompt user for export directory
        #
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            'Select directory to export to',
            self.scene.currentDirectory(),
            QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks
        )

        if not stringutils.isNullOrEmpty(directory):

            self.batchPathLineEdit.setText(directory)

        else:

            log.info('Operation aborted...')

    @QtCore.Slot(bool)
    def on_batchPushButton_clicked(self, checked=False):
        """
        Slot method for the batchPushButton's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

        # Check if queue is valid
        #
        fileCount = self.fileListWidget.count()

        if fileCount == 0:

            QtWidgets.QMessageBox.warning(self, 'Batch Export', 'No files in queue to batch!')
            return

        # Iterate through files
        #
        checkout = self.checkoutCheckBox.isChecked()
        directory = self.batchPathLineEdit.text()

        increment = (1.0 / float(fileCount)) * 100.0

        for i in range(fileCount):

            # Try to open scene file
            #
            filePath = self.fileListWidget.item(i).text()
            progress = math.ceil(increment * float(i + 1))

            success = self.scene.open(filePath)

            if not success:

                log.warning(f'Unable to open scene file: {filePath}')
                self.batchProgressBar.setValue(progress)

                continue

            # Export sequences
            #
            self.manager.exportSequencers(directory=directory, checkout=checkout)
            self.batchProgressBar.setValue(progress)
    # endregion
