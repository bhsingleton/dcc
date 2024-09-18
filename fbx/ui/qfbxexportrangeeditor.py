import math
import os

from Qt import QtWidgets, QtCore, QtGui
from dcc import fnscene, fnreference, fnnotify
from dcc.generators.consecutivepairs import consecutivePairs
from dcc.ui import qsingletonwindow, qrollout, qdivider, qsignalblocker
from dcc.ui.models import qpsonitemmodel, qpsonstyleditemdelegate
from dcc.fbx.libs import fbxio, fbxsequencer, fbxexportrange
from dcc.python import stringutils
from dcc.json import jsonutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QFbxExportRangeEditor(qsingletonwindow.QSingletonWindow):
    """
    Overload of `QSingletonWindow` that interfaces with FBX export-range data.
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

    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QFbxExportRangeEditor, self).__setup_ui__(*args, **kwargs)

        # Initialize main window
        #
        self.setWindowTitle("|| Fbx Export Range Editor")
        self.setMinimumSize(QtCore.QSize(400, 700))

        # Initialize main toolbar
        #
        self.mainToolBar = QtWidgets.QToolBar(parent=self)
        self.mainToolBar.setObjectName('mainToolBar')
        self.mainToolBar.setAllowedAreas(QtCore.Qt.LeftToolBarArea)
        self.mainToolBar.setMovable(False)
        self.mainToolBar.setOrientation(QtCore.Qt.Vertical)
        self.mainToolBar.setIconSize(QtCore.QSize(20, 20))
        self.mainToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.mainToolBar.setFloatable(True)

        self.newSequencerAction = QtWidgets.QAction(QtGui.QIcon(':/dcc/icons/new_file.svg'), '', parent=self.mainToolBar)
        self.newSequencerAction.setObjectName('newSequencerAction')
        self.newSequencerAction.setToolTip('Creates a new sequencer.')
        self.newSequencerAction.triggered.connect(self.on_newSequencerAction_triggered)

        self.saveSequencerAction = QtWidgets.QAction(QtGui.QIcon(':/dcc/icons/save_file.svg'), '', parent=self.mainToolBar)
        self.saveSequencerAction.setObjectName('saveSequencerAction')
        self.saveSequencerAction.setToolTip('Saves any changes made to the active sequencer.')
        self.saveSequencerAction.triggered.connect(self.on_saveSequencerAction_triggered)

        self.importRangesAction = QtWidgets.QAction(QtGui.QIcon(':/dcc/icons/import_file.svg'), '', parent=self.mainToolBar)
        self.importRangesAction.setObjectName('importRangesAction')
        self.importRangesAction.setToolTip('Import ranges into the selected sequencer.')
        self.importRangesAction.triggered.connect(self.on_importRangesAction_triggered)

        self.exportRangesAction = QtWidgets.QAction(QtGui.QIcon(':/dcc/icons/export_file.svg'), '', parent=self.mainToolBar)
        self.exportRangesAction.setObjectName('exportRangesAction')
        self.exportRangesAction.setToolTip('Export ranges from the selected sequencer.')
        self.exportRangesAction.triggered.connect(self.on_exportRangesAction_triggered)

        self.addExportRangeAction = QtWidgets.QAction(QtGui.QIcon(':/dcc/icons/add.svg'), '', parent=self.mainToolBar)
        self.addExportRangeAction.setObjectName('addExportRangeAction')
        self.addExportRangeAction.setToolTip('Adds an export range to the selected sequencer.')
        self.addExportRangeAction.triggered.connect(self.on_addExportRangeAction_triggered)

        self.removeExportRangeAction = QtWidgets.QAction(QtGui.QIcon(':/dcc/icons/remove.svg'), '', parent=self.mainToolBar)
        self.removeExportRangeAction.setObjectName('removeExportRangeAction')
        self.removeExportRangeAction.setToolTip('Remove the selected export ranges.')
        self.removeExportRangeAction.triggered.connect(self.on_removeExportRangeAction_triggered)

        self.updateStartTimeAction = QtWidgets.QAction(QtGui.QIcon(':/dcc/icons/start_time.svg'), '', parent=self.mainToolBar)
        self.updateStartTimeAction.setObjectName('updateStartTimeAction')
        self.updateStartTimeAction.setToolTip('LMB adopts start frame. Shift + LMB copies start frame.')
        self.updateStartTimeAction.triggered.connect(self.on_updateStartTimeAction_triggered)

        self.updateEndTimeAction = QtWidgets.QAction(QtGui.QIcon(':/dcc/icons/end_time.svg'), '', parent=self.mainToolBar)
        self.updateEndTimeAction.setObjectName('updateEndTimeAction')
        self.updateEndTimeAction.setToolTip('LMB adopts end frame. Shift + LMB copies end frame.')
        self.updateEndTimeAction.triggered.connect(self.on_updateEndTimeAction_triggered)

        self.updateTimeRangeAction = QtWidgets.QAction(QtGui.QIcon(':/dcc/icons/timeline.svg'), '', parent=self.mainToolBar)
        self.updateTimeRangeAction.setObjectName('updateTimeRangeAction')
        self.updateTimeRangeAction.setToolTip('LMB adopts timerange. Shift + LMB copies timerange.')
        self.updateTimeRangeAction.triggered.connect(self.on_updateTimeRangeAction_triggered)

        self.mainToolBar.addAction(self.newSequencerAction)
        self.mainToolBar.addAction(self.saveSequencerAction)
        self.mainToolBar.addAction(self.importRangesAction)
        self.mainToolBar.addAction(self.exportRangesAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.addExportRangeAction)
        self.mainToolBar.addAction(self.removeExportRangeAction)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addAction(self.updateStartTimeAction)
        self.mainToolBar.addAction(self.updateEndTimeAction)
        self.mainToolBar.addAction(self.updateTimeRangeAction)

        self.addToolBar(QtCore.Qt.LeftToolBarArea, self.mainToolBar)

        # Initialize central widget
        #
        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('centralLayout')
        centralLayout.setAlignment(QtCore.Qt.AlignTop)

        centralWidget = QtWidgets.QWidget()
        centralWidget.setObjectName('centralWidget')
        centralWidget.setLayout(centralLayout)

        self.setCentralWidget(centralWidget)

        # Initialize sequencer rollout
        #
        self.sequencerLayout = QtWidgets.QVBoxLayout()
        self.sequencerLayout.setObjectName('sequencerLayout')

        self.sequencerRollout = qrollout.QRollout('Sequencers')
        self.sequencerRollout.setObjectName('sequencerRollout')
        self.sequencerRollout.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.sequencerRollout.setExpanded(True)
        self.sequencerRollout.setLayout(self.sequencerLayout)
        self.sequencerRollout.expandedChanged.connect(self.on_sequencerRollout_expandedChanged)

        self.sequencerComboBox = QtWidgets.QComboBox()
        self.sequencerComboBox.setObjectName('sequencerComboBox')
        self.sequencerComboBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.sequencerComboBox.setFixedHeight(24)
        self.sequencerComboBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sequencerComboBox.currentIndexChanged.connect(self.on_sequencerComboBox_currentIndexChanged)

        self.deleteSequencerPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/delete.svg'), '')
        self.deleteSequencerPushButton.setObjectName('deleteSequencerPushButton')
        self.deleteSequencerPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.deleteSequencerPushButton.setFixedSize(QtCore.QSize(24, 24))
        self.deleteSequencerPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.deleteSequencerPushButton.clicked.connect(self.on_deleteSequencerPushButton_clicked)

        self.sequencerOptionsLayout = QtWidgets.QHBoxLayout()
        self.sequencerOptionsLayout.setObjectName('sequencerOptionsLayout')
        self.sequencerOptionsLayout.setContentsMargins(0, 0, 0, 0)
        self.sequencerOptionsLayout.addWidget(self.sequencerComboBox)
        self.sequencerOptionsLayout.addWidget(self.deleteSequencerPushButton)

        self.sequencerTreeView = QtWidgets.QTreeView()
        self.sequencerTreeView.setObjectName('sequencerTreeView')
        self.sequencerTreeView.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.sequencerTreeView.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.sequencerTreeView.setStyleSheet('QTreeView::item { height: 24px; }')
        self.sequencerTreeView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.sequencerTreeView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.sequencerTreeView.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | QtWidgets.QAbstractItemView.EditKeyPressed)
        self.sequencerTreeView.setDropIndicatorShown(True)
        self.sequencerTreeView.setDragEnabled(True)
        self.sequencerTreeView.setDragDropOverwriteMode(False)
        self.sequencerTreeView.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.sequencerTreeView.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.sequencerTreeView.setAlternatingRowColors(True)
        self.sequencerTreeView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.sequencerTreeView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.sequencerTreeView.setUniformRowHeights(True)
        self.sequencerTreeView.setAnimated(True)
        self.sequencerTreeView.setExpandsOnDoubleClick(False)
        self.sequencerTreeView.clicked.connect(self.on_sequencerTreeView_clicked)

        self.sequencerTreeHeader = self.sequencerTreeView.header()
        self.sequencerTreeHeader.setDefaultSectionSize(200)
        self.sequencerTreeHeader.setMinimumSectionSize(100)
        self.sequencerTreeHeader.setStretchLastSection(True)
        self.sequencerTreeHeader.setVisible(True)

        self.sequencerItemModel = qpsonitemmodel.QPSONItemModel(parent=self.sequencerTreeView)
        self.sequencerItemModel.setObjectName('sequencerItemModel')
        self.sequencerItemModel.invisibleRootProperty = 'exportRanges'

        self.sequencerTreeView.setModel(self.sequencerItemModel)

        self.sequencerItemDelegate = qpsonstyleditemdelegate.QPSONStyledItemDelegate(parent=self.sequencerTreeView)
        self.sequencerItemDelegate.setObjectName('sequencerItemDelegate')

        self.sequencerTreeView.setItemDelegate(self.sequencerItemDelegate)

        self.exportLabel = QtWidgets.QLabel('Export:')
        self.exportLabel.setObjectName('exportLabel')
        self.exportLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))

        self.exportLine = qdivider.QDivider(QtCore.Qt.Horizontal)
        self.exportLine.setObjectName('exportLine')
        self.exportLine.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))

        self.exportDividerLayout = QtWidgets.QHBoxLayout()
        self.exportDividerLayout.setObjectName('exportDividerLayout')
        self.exportDividerLayout.setContentsMargins(0, 0, 0, 0)
        self.exportDividerLayout.addWidget(self.exportLabel)
        self.exportDividerLayout.addWidget(self.exportLine)

        self.exportPathLineEdit = QtWidgets.QLineEdit('')
        self.exportPathLineEdit.setObjectName('exportPathLineEdit')
        self.exportPathLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.exportPathLineEdit.setFixedHeight(24)
        self.exportPathLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.exportPathLineEdit.setReadOnly(True)

        self.checkoutCheckBox = QtWidgets.QCheckBox('Checkout')
        self.checkoutCheckBox.setObjectName('checkoutCheckBox')
        self.checkoutCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))
        self.checkoutCheckBox.setFixedHeight(24)
        self.checkoutCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)

        self.exportPathLayout = QtWidgets.QHBoxLayout()
        self.exportPathLayout.setObjectName('exportPathLayout')
        self.exportPathLayout.setContentsMargins(0, 0, 0, 0)
        self.exportPathLayout.addWidget(self.exportPathLineEdit)
        self.exportPathLayout.addWidget(self.checkoutCheckBox)

        self.exportPushButton = QtWidgets.QPushButton('Export')
        self.exportPushButton.setObjectName('exportPushButton')
        self.exportPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.exportPushButton.setFixedHeight(24)
        self.exportPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.exportPushButton.clicked.connect(self.on_exportPushButton_clicked)

        self.exportAllPushButton = QtWidgets.QPushButton('Export All')
        self.exportAllPushButton.setObjectName('exportAllPushButton')
        self.exportAllPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.exportAllPushButton.setFixedHeight(24)
        self.exportAllPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.exportAllPushButton.clicked.connect(self.on_exportAllPushButton_clicked)

        self.exportButtonsLayout = QtWidgets.QHBoxLayout()
        self.exportButtonsLayout.setObjectName('exportButtonsLayout')
        self.exportButtonsLayout.setContentsMargins(0, 0, 0, 0)
        self.exportButtonsLayout.addWidget(self.exportPushButton)
        self.exportButtonsLayout.addWidget(self.exportAllPushButton)

        self.sequencerLayout.addLayout(self.sequencerOptionsLayout)
        self.sequencerLayout.addWidget(self.sequencerTreeView)
        self.sequencerLayout.addLayout(self.exportDividerLayout)
        self.sequencerLayout.addLayout(self.exportPathLayout)
        self.sequencerLayout.addLayout(self.exportButtonsLayout)

        centralLayout.addWidget(self.sequencerRollout)

        # Initialize batch rollout
        #
        self.batchLayout = QtWidgets.QVBoxLayout()
        self.batchLayout.setObjectName('batchLayout')

        self.batchRollout = qrollout.QRollout('Batch')
        self.batchRollout.setObjectName('batchRollout')
        self.batchRollout.setExpanded(False)
        self.batchRollout.setLayout(self.batchLayout)
        self.batchRollout.expandedChanged.connect(self.on_batchRollout_expandedChanged)

        self.filesLabel = QtWidgets.QLabel('Files:')
        self.filesLabel.setObjectName('filesLabel')
        self.filesLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))

        self.filesLine = qdivider.QDivider(QtCore.Qt.Horizontal)
        self.filesLine.setObjectName('exportLine')
        self.filesLine.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))

        self.addFilesPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/add.svg'), '')
        self.addFilesPushButton.setObjectName('addFilesPushButton')
        self.addFilesPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.addFilesPushButton.setFixedSize(QtCore.QSize(20, 20))
        self.addFilesPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.addFilesPushButton.clicked.connect(self.on_addFilesPushButton_clicked)

        self.removeFilesPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/remove.svg'), '')
        self.removeFilesPushButton.setObjectName('removeFilesPushButton')
        self.removeFilesPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.removeFilesPushButton.setFixedSize(QtCore.QSize(20, 20))
        self.removeFilesPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.removeFilesPushButton.clicked.connect(self.on_removeFilesPushButton_clicked)

        self.filesDividerLayout = QtWidgets.QHBoxLayout()
        self.filesDividerLayout.setObjectName('exportDividerLayout')
        self.filesDividerLayout.setContentsMargins(0, 0, 0, 0)
        self.filesDividerLayout.addWidget(self.filesLabel)
        self.filesDividerLayout.addWidget(self.filesLine)
        self.filesDividerLayout.addWidget(self.addFilesPushButton)
        self.filesDividerLayout.addWidget(self.removeFilesPushButton)

        self.fileListWidget = QtWidgets.QListWidget()
        self.fileListWidget.setObjectName('fileListWidget')
        self.fileListWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.fileListWidget.setStyleSheet('QListWidget::item { height: 24px; }')
        self.fileListWidget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.fileListWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.fileListWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.fileListWidget.setDropIndicatorShown(False)
        self.fileListWidget.setDragEnabled(False)
        self.fileListWidget.setDragDropOverwriteMode(False)
        self.fileListWidget.setDragDropMode(QtWidgets.QAbstractItemView.NoDragDrop)
        self.fileListWidget.setDefaultDropAction(QtCore.Qt.IgnoreAction)
        self.fileListWidget.setAlternatingRowColors(True)
        self.fileListWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.fileListWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.fileListWidget.setUniformItemSizes(True)

        self.batchPathLabel = QtWidgets.QLabel('Directory:')
        self.batchPathLabel.setObjectName('batchPathLabel')
        self.batchPathLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))
        self.batchPathLabel.setFixedHeight(24)
        self.batchPathLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.batchPathLineEdit = QtWidgets.QLineEdit('')
        self.batchPathLineEdit.setObjectName('batchPathLineEdit')
        self.batchPathLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.batchPathLineEdit.setFixedHeight(24)
        self.batchPathLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.batchPathLineEdit.setReadOnly(True)

        self.batchPathPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/open_folder.svg'), '')
        self.batchPathPushButton.setObjectName('batchPathPushButton')
        self.batchPathPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.batchPathPushButton.setFixedSize(QtCore.QSize(24, 24))
        self.batchPathPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.batchPathPushButton.clicked.connect(self.on_batchPathPushButton_clicked)

        self.batchPathLayout = QtWidgets.QHBoxLayout()
        self.batchPathLayout.setObjectName('batchPathLayout')
        self.batchPathLayout.setContentsMargins(0, 0, 0, 0)
        self.batchPathLayout.addWidget(self.batchPathLabel)
        self.batchPathLayout.addWidget(self.batchPathLineEdit)
        self.batchPathLayout.addWidget(self.batchPathPushButton)

        self.batchDivider = qdivider.QDivider(QtCore.Qt.Horizontal)
        self.batchDivider.setObjectName('batchDivider')
        self.batchDivider.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))

        self.batchPushButton = QtWidgets.QPushButton('Batch')
        self.batchPushButton.setObjectName('batchPushButton')
        self.batchPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.batchPushButton.setFixedHeight(24)
        self.batchPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.batchPushButton.clicked.connect(self.on_batchPushButton_clicked)

        self.batchProgressBar = QtWidgets.QProgressBar()
        self.batchProgressBar.setObjectName('batchProgressBar')
        self.batchProgressBar.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.batchProgressBar.setFixedHeight(24)
        self.batchProgressBar.setMinimum(0)
        self.batchProgressBar.setMaximum(100)
        self.batchProgressBar.setValue(0)

        self.batchLayout.addLayout(self.filesDividerLayout)
        self.batchLayout.addWidget(self.fileListWidget)
        self.batchLayout.addLayout(self.batchPathLayout)
        self.batchLayout.addWidget(self.batchDivider)
        self.batchLayout.addWidget(self.batchPushButton)
        self.batchLayout.addWidget(self.batchProgressBar)

        centralLayout.addWidget(self.batchRollout)
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

        if isinstance(checkout, bool):

            self.checkoutCheckBox.setChecked(checkout)
    # endregion

    # region Callbacks
    def sceneChanged(self, *args, **kwargs):
        """
        Post file-open callback that invalidates the current asset.

        :rtype: None
        """

        self.sequencers.clear()
        self.sequencers.extend([sequencer for sequencer in self.manager.loadSequencers() if sequencer.isValid()])

        self.invalidateSequencers()
    # endregion

    # region Methods
    def addCallbacks(self):
        """
        Adds any callbacks required by this window.

        :rtype: None
        """

        # Check if notifies already exist
        #
        hasNotifies = len(self._notifies) > 0

        if not hasNotifies:

            self._notifies.addPostFileOpenNotify(self.sceneChanged)

        # Invalidate sequencers
        #
        self.sceneChanged()

    def removeCallbacks(self):
        """
        Removes any callbacks created by this window.

        :rtype: None
        """

        # Check if notifies exist
        #
        hasNotifies = len(self._notifies) > 0

        if hasNotifies:

            self._notifies.clear()

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
        self.checkout = bool(settings.value('editor/checkout', defaultValue=1, type=int))

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

    # region Slots
    @QtCore.Slot(bool)
    def on_newSequencerAction_triggered(self, checked=False):
        """
        Slot method for the `newSequencerAction` widget's `triggered` signal.

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
        Slot method for the `deleteSequencerAction` widget's `triggered` signal.

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
        Slot method for the `saveSequencerAction` widget's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        self.save()

    @QtCore.Slot(bool)
    def on_addExportRangeAction_triggered(self, checked=False):
        """
        Slot method for the `addExportRangeAction` widget's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        exportRange = self.defaultExportRange()
        self.sequencerItemModel.appendRow(exportRange)

    @QtCore.Slot(bool)
    def on_removeExportRangeAction_triggered(self, checked=False):
        """
        Slot method for the `removeExportRangeAction` widget's `triggered` signal.

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
        Slot method for the `importRangesAction` widget's `triggered` signal.

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
        Slot method for the `exportRangesAction` widget's `triggered` signal.

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
        Slot method for the `updateStartTimeAction` widget's `triggered` signal.

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
        Slot method for the `updateEndTimeAction` widget's `triggered` signal.

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
        Slot method for the `updateTimeRangeAction` widget's `triggered` signal.

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
    def on_sequencerRollout_expandedChanged(self, expanded):
        """
        Slot method for the `sequencerRollout` widget's `expanded` signal.

        :type expanded: bool
        :rtype: None
        """

        with qsignalblocker.QSignalBlocker(self.batchRollout):

            self.batchRollout.setExpanded(not expanded)

    @QtCore.Slot(int)
    def on_sequencerComboBox_currentIndexChanged(self, index):
        """
        Slot method for the `sequencerComboBox` widget's `currentIndexChanged` signal.

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
        Slot method for the `sequencerTreeView` widget's `clicked` signal.

        :type index: QtCore.QModelIndex
        :rtype: None
        """

        self.invalidateExportPath()

    @QtCore.Slot()
    def on_exportPushButton_clicked(self):
        """
        Slot method for the `exportPushButton` widget's `clicked` signal.

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

    @QtCore.Slot()
    def on_exportAllPushButton_clicked(self):
        """
        Slot method for the `exportAllPushButton` widget's `clicked` signal.

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
    def on_batchRollout_expandedChanged(self, expanded):
        """
        Slot method for the `batchRollout` widget's `expanded` signal.

        :type expanded: bool
        :rtype: None
        """

        with qsignalblocker.QSignalBlocker(self.sequencerRollout):

            self.sequencerRollout.setExpanded(not expanded)

    @QtCore.Slot()
    def on_addFilesPushButton_clicked(self):
        """
        Slot method for the `addFilesPushButton` widget's `clicked` signal.

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

    @QtCore.Slot()
    def on_removeFilesPushButton_clicked(self):
        """
        Slot method for the `removeFilesPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Iterate through selected items
        #
        selectedItems = self.fileListWidget.selectedItems()

        for selectedItem in reversed(selectedItems):

            row = self.fileListWidget.row(selectedItem)
            self.fileListWidget.takeItem(row)

    @QtCore.Slot()
    def on_batchPathPushButton_clicked(self):
        """
        Slot method for the `batchPathPushButton` widget's `clicked` signal.

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

    @QtCore.Slot()
    def on_batchPushButton_clicked(self):
        """
        Slot method for the `batchPushButton` widget's `clicked` signal.

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
