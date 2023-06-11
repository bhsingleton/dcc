import os

from Qt import QtWidgets, QtCore, QtGui
from dcc import fnscene, fnreference, fnnotify
from dcc.generators.consecutivepairs import consecutivePairs
from dcc.ui import quicwindow
from dcc.ui.models import qpsonitemmodel, qpsonstyleditemdelegate
from dcc.fbx.libs import fbxio, fbxsequencer, fbxsequence
from dcc.python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QFbxSequenceEditor(quicwindow.QUicWindow):
    """
    Overload of QUicWindow used to edit fbx sequence data.
    """

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key flags: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Define class variables
        #
        self._manager = fbxio.FbxIO()
        self._sequencers = []
        self._currentSequencer = None
        self._scene = fnscene.FnScene()
        self._notifies = fnnotify.FnNotify()

        # Declare public variables
        #
        self.sequencerItemModel = None
        self.sequencerItemDelegate = None

        # Call parent method
        #
        super(QFbxSequenceEditor, self).__init__(*args, **kwargs)
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
    # endregion

    # region Methods
    def postLoad(self, *args, **kwargs):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        # Call parent method
        #
        super(QFbxSequenceEditor, self).postLoad()

        # Edit sequencer/batch rollouts
        #
        self.sequencerRollout.setText('Sequencers')
        self.sequencerRollout.setExpanded(True)

        self.batchRollout.setText('Batch')
        self.batchRollout.setExpanded(False)

        self.centralWidget.layout().setAlignment(QtCore.Qt.AlignTop)

        # Initialize sequencer tree view model
        #
        self.sequencerItemModel = qpsonitemmodel.QPSONItemModel(parent=self.sequencerTreeView)
        self.sequencerItemModel.setObjectName('sequencerItemModel')
        self.sequencerItemModel.invisibleRootProperty = 'sequences'

        self.sequencerTreeView.setModel(self.sequencerItemModel)

        self.sequencerItemDelegate = qpsonstyleditemdelegate.QPSONStyledItemDelegate(parent=self.sequencerTreeView)
        self.sequencerItemDelegate.setObjectName('sequencerItemDelegate')

        self.sequencerTreeView.setItemDelegate(self.sequencerItemDelegate)

    def defaultSequence(self):
        """
        Returns a new sequence using the current scene settings.

        :rtype: fbxsequence.FbxSequence
        """

        name = os.path.splitext(self.scene.currentFilename())[0]
        startFrame, endFrame = self.scene.getStartTime(), self.scene.getEndTime()

        return fbxsequence.FbxSequence(name=name, startFrame=startFrame, endFrame=endFrame, useTimeline=False)

    def getSelectedRows(self):
        """
        Returns the selected rows from the tree view.

        :rtype: List[int]
        """

        return [self.sequencerItemModel.topLevelIndex(index).row() for index in self.sequencerTreeView.selectedIndexes() if index.column() == 0]

    def invalidateSequencers(self):
        """
        Invalidates the sequences displayed inside the combo box.

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

    def invalidateSequences(self):
        """
        Invalidates the sequences displayed inside the tree view.

        :rtype: None
        """

        self.sequencerItemModel.invisibleRootItem = self.currentSequencer

    def invalidateExportPath(self):
        """
        Invalidates the displayed export path.

        :rtype: None
        """

        selectedRows = self.getSelectedRows()
        numSelectedRows = len(selectedRows)

        if numSelectedRows:

            selectedRow = selectedRows[0]
            exportPath = self.currentSequencer.sequences[selectedRow].exportPath()

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
        super(QFbxSequenceEditor, self).showEvent(event)

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
        super(QFbxSequenceEditor, self).closeEvent(event)

        # Clear notifies
        #
        self._notifies.clear()
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
        self.invalidateSequences()

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

        references = list(reference.iterSceneReferences())
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

            index = filteredPaths.index(item)
            guid = reference(references[index]).guid()
            sequence = self.defaultSequence()

            sequencer = fbxsequencer.FbxSequencer(guid=guid, sequences=[sequence])
            self.sequencers.append(sequencer)

            self.invalidateSequencers()

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
            'Are you sure you want to delete this sequencer and all of its sequences?',
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
        )

        if response != QtWidgets.QMessageBox.Ok:

            log.info('Operation aborted...')
            return

        # Remove selected sequencer
        #
        index = self.sequencerComboBox.currentIndex()
        del self.sequencers[index]

        # Invalidate sequences
        #
        self.invalidateSequencers()

    @QtCore.Slot(bool)
    def on_saveSequencerAction_triggered(self, checked=False):
        """
        Slot method for the saveSequencerAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        self.manager.saveSequencers(self.sequencers)
        self.scene.save()

    @QtCore.Slot(bool)
    def on_addSequenceAction_triggered(self, checked=False):
        """
        Slot method for the addSequenceAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        sequence = self.defaultSequence()
        self.sequencerItemModel.appendRow(sequence)

    @QtCore.Slot(bool)
    def on_removeSequenceAction_triggered(self, checked=False):
        """
        Slot method for the removeSequenceAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        selectedRows = self.getSelectedRows()

        for (start, end) in reversed(tuple(consecutivePairs(selectedRows))):

            numRows = (end - start) + 1
            self.sequencerItemModel.removeRows(start, numRows)

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

                self.currentSequencer.sequences[row].startFrame = self.scene.getStartTime()

        else:

            row = selectedRows[0]
            self.scene.setStartTime(self.currentSequencer.sequences[row].startFrame)

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

                self.currentSequencer.sequences[row].endFrame = self.scene.getEndTime()

        else:

            row = selectedRows[0]
            self.scene.setEndTime(self.currentSequencer.sequences[row].endFrame)

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

                self.currentSequencer.sequences[row].startFrame = self.scene.getStartTime()
                self.currentSequencer.sequences[row].endFrame = self.scene.getEndTime()

        else:

            row = selectedRows[0]
            self.scene.setStartTime(self.currentSequencer.sequences[row].startFrame)
            self.scene.setEndTime(self.currentSequencer.sequences[row].endFrame)

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

            QtWidgets.QMessageBox.warning(self, 'Export Sequence', 'No sequencer available to export from!')
            return

        # Export selected sequences
        #
        checkout = self.checkoutCheckBox.isChecked()

        for row in self.getSelectedRows():

            self.currentSequencer.sequences[row].export(checkout=checkout)

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

            QtWidgets.QMessageBox.warning(self, 'Export Sequences', 'No sequencer available to export from!')
            return

        # Export all sequences
        #
        checkout = self.checkoutCheckBox.isChecked()

        for sequence in self.currentSequencer.sequences:

            sequence.export(checkout=checkout)

    @QtCore.Slot(bool)
    def on_addFilesPushButton_clicked(self, checked=False):
        """
        Slot method for the addFilesPushButton's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

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
            currentPaths = [self.fileListWidget.item(i).text() for i in range(self.fileListWidget.count())]
            filteredPaths = [path for path in filePaths if path not in currentPaths]

            for path in filteredPaths:

                self.fileListWidget.addItem(path)

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
            progress = increment * float(i + 1)

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
