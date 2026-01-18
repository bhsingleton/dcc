import math
import os

from ..libs import fbxio, fbxreferencedasset, fbxexportrange
from ... import fnscene, fnreference, fnnotify
from ...generators.consecutivepairs import consecutivePairs
from ...python import stringutils
from ...json import jsonutils
from ...ui import qsingletonwindow, qrollout, qdivider, qsignalblocker
from ...ui.models import qpsonitemmodel, qpsonstyleditemdelegate
from ...vendor.Qt import QtWidgets, QtCore, QtGui

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
        self._referencedAssets = []
        self._selectedReferencedAsset = None
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
        self.setWindowTitle("|| FBX Export-Range Editor")
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

        self.newReferencedAssetAction = QtWidgets.QAction(QtGui.QIcon(':/dcc/icons/new_file.svg'), '', parent=self.mainToolBar)
        self.newReferencedAssetAction.setObjectName('newSequencerAction')
        self.newReferencedAssetAction.setToolTip('Creates a new referenced asset.')
        self.newReferencedAssetAction.triggered.connect(self.on_newReferencedAssetAction_triggered)

        self.saveReferencedAssetAction = QtWidgets.QAction(QtGui.QIcon(':/dcc/icons/save_file.svg'), '', parent=self.mainToolBar)
        self.saveReferencedAssetAction.setObjectName('saveSequencerAction')
        self.saveReferencedAssetAction.setToolTip('Saves any changes made to the active referenced asset.')
        self.saveReferencedAssetAction.triggered.connect(self.on_saveReferencedAssetAction_triggered)

        self.importRangesAction = QtWidgets.QAction(QtGui.QIcon(':/dcc/icons/import_file.svg'), '', parent=self.mainToolBar)
        self.importRangesAction.setObjectName('importRangesAction')
        self.importRangesAction.setToolTip('Import ranges into the selected referenced asset.')
        self.importRangesAction.triggered.connect(self.on_importRangesAction_triggered)

        self.exportRangesAction = QtWidgets.QAction(QtGui.QIcon(':/dcc/icons/export_file.svg'), '', parent=self.mainToolBar)
        self.exportRangesAction.setObjectName('exportRangesAction')
        self.exportRangesAction.setToolTip('Export ranges from the selected referenced asset.')
        self.exportRangesAction.triggered.connect(self.on_exportRangesAction_triggered)

        self.addExportRangeAction = QtWidgets.QAction(QtGui.QIcon(':/dcc/icons/add.svg'), '', parent=self.mainToolBar)
        self.addExportRangeAction.setObjectName('addExportRangeAction')
        self.addExportRangeAction.setToolTip('Adds an export range to the selected referenced asset.')
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

        self.mainToolBar.addAction(self.newReferencedAssetAction)
        self.mainToolBar.addAction(self.saveReferencedAssetAction)
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

        # Initialize referenced asset rollout
        #
        self.referencedAssetLayout = QtWidgets.QVBoxLayout()
        self.referencedAssetLayout.setObjectName('referencedAssetLayout')

        self.referencedAssetRollout = qrollout.QRollout('Referenced Assets')
        self.referencedAssetRollout.setObjectName('referencedAssetRollout')
        self.referencedAssetRollout.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.referencedAssetRollout.setExpanded(True)
        self.referencedAssetRollout.setLayout(self.referencedAssetLayout)
        self.referencedAssetRollout.expandedChanged.connect(self.on_referencedAssetRollout_expandedChanged)

        self.referencedAssetComboBox = QtWidgets.QComboBox()
        self.referencedAssetComboBox.setObjectName('referencedAssetComboBox')
        self.referencedAssetComboBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.referencedAssetComboBox.setFixedHeight(24)
        self.referencedAssetComboBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.referencedAssetComboBox.currentIndexChanged.connect(self.on_referencedAssetComboBox_currentIndexChanged)

        self.deleteReferencedAssetPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/delete.svg'), '')
        self.deleteReferencedAssetPushButton.setObjectName('deleteSequencerPushButton')
        self.deleteReferencedAssetPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.deleteReferencedAssetPushButton.setFixedSize(QtCore.QSize(24, 24))
        self.deleteReferencedAssetPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.deleteReferencedAssetPushButton.clicked.connect(self.on_deleteReferencedAssetPushButton_clicked)

        self.referencedAssetOptionsLayout = QtWidgets.QHBoxLayout()
        self.referencedAssetOptionsLayout.setObjectName('referencedAssetOptionsLayout')
        self.referencedAssetOptionsLayout.setContentsMargins(0, 0, 0, 0)
        self.referencedAssetOptionsLayout.addWidget(self.referencedAssetComboBox)
        self.referencedAssetOptionsLayout.addWidget(self.deleteReferencedAssetPushButton)

        self.referencedAssetTreeView = QtWidgets.QTreeView()
        self.referencedAssetTreeView.setObjectName('referencedAssetTreeView')
        self.referencedAssetTreeView.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.referencedAssetTreeView.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.referencedAssetTreeView.setStyleSheet('QTreeView::item { height: 24px; }')
        self.referencedAssetTreeView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.referencedAssetTreeView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.referencedAssetTreeView.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | QtWidgets.QAbstractItemView.EditKeyPressed)
        self.referencedAssetTreeView.setDropIndicatorShown(True)
        self.referencedAssetTreeView.setDragEnabled(True)
        self.referencedAssetTreeView.setDragDropOverwriteMode(False)
        self.referencedAssetTreeView.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.referencedAssetTreeView.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.referencedAssetTreeView.setAlternatingRowColors(True)
        self.referencedAssetTreeView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.referencedAssetTreeView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.referencedAssetTreeView.setUniformRowHeights(True)
        self.referencedAssetTreeView.setAnimated(True)
        self.referencedAssetTreeView.setExpandsOnDoubleClick(False)
        self.referencedAssetTreeView.clicked.connect(self.on_referencedAssetTreeView_clicked)

        self.referencedAssetTreeHeader = self.referencedAssetTreeView.header()
        self.referencedAssetTreeHeader.setDefaultSectionSize(200)
        self.referencedAssetTreeHeader.setMinimumSectionSize(100)
        self.referencedAssetTreeHeader.setStretchLastSection(True)
        self.referencedAssetTreeHeader.setVisible(True)

        self.referencedAssetItemModel = qpsonitemmodel.QPSONItemModel(parent=self.referencedAssetTreeView)
        self.referencedAssetItemModel.setObjectName('referencedAssetItemModel')
        self.referencedAssetItemModel.invisibleRootProperty = 'exportRanges'

        self.referencedAssetTreeView.setModel(self.referencedAssetItemModel)

        self.referencedAssetItemDelegate = qpsonstyleditemdelegate.QPSONStyledItemDelegate(parent=self.referencedAssetTreeView)
        self.referencedAssetItemDelegate.setObjectName('referencedAssetItemDelegate')

        self.referencedAssetTreeView.setItemDelegate(self.referencedAssetItemDelegate)

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

        self.referencedAssetLayout.addLayout(self.referencedAssetOptionsLayout)
        self.referencedAssetLayout.addWidget(self.referencedAssetTreeView)
        self.referencedAssetLayout.addLayout(self.exportDividerLayout)
        self.referencedAssetLayout.addLayout(self.exportPathLayout)
        self.referencedAssetLayout.addLayout(self.exportButtonsLayout)

        centralLayout.addWidget(self.referencedAssetRollout)

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
        Getter method that returns the fbx IO interface.

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
    def referencedAssets(self):
        """
        Getter method that returns the active FBX referenced assets.

        :rtype: List[referencedasset.ReferencedAsset]
        """

        return self._referencedAssets

    @property
    def selectedReferencedAsset(self):
        """
        Getter method that returns the current FBX referenced assets.

        :rtype: referencedasset.ReferencedAsset
        """

        return self._selectedReferencedAsset

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

        self.referencedAssets.clear()
        self.referencedAssets.extend([referencedAsset for referencedAsset in self.manager.loadReferencedAssets() if referencedAsset.isValid()])

        self.invalidateReferencedAssets()
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

        # Invalidate user interface
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

            self.manager.saveReferencedAssets(self.referencedAssets)
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

        return [self.referencedAssetItemModel.topLevelIndex(index).row() for index in self.referencedAssetTreeView.selectedIndexes() if index.column() == 0]

    def invalidateReferencedAssets(self):
        """
        Invalidates the referenced asset combo box items.
        
        :rtype: None
        """

        # Cache combo-box selection
        #
        index = self.referencedAssetComboBox.currentIndex()

        # Re-populate combo box
        #
        items = [f'{referencedAsset.reference.associatedNamespace()}:{referencedAsset.reference.filename()}' for referencedAsset in self.referencedAssets]
        numItems = len(items)

        with qsignalblocker.QSignalBlocker(self.referencedAssetComboBox):

            self.referencedAssetComboBox.clear()
            self.referencedAssetComboBox.addItems(items)
            self.referencedAssetComboBox.setCurrentIndex(-1)

        # Recreate combo-box selection
        #
        if 0 <= index < numItems:

            self.referencedAssetComboBox.setCurrentIndex(index)

        elif numItems > 0:

            self.referencedAssetComboBox.setCurrentIndex(0)

        else:

            pass

    def invalidateExportRanges(self):
        """
        Invalidates the export-ranges displayed inside the tree view.

        :rtype: None
        """

        self.referencedAssetItemModel.invisibleRootItem = self.selectedReferencedAsset
        self.referencedAssetTreeView.expandToDepth(1)

    def invalidateExportPath(self):
        """
        Invalidates the displayed export path.

        :rtype: None
        """

        selectedRows = self.getSelectedRows()
        numSelectedRows = len(selectedRows)

        if numSelectedRows:

            selectedRow = selectedRows[0]
            exportPath = self.selectedReferencedAsset.exportRanges[selectedRow].exportPath()

            self.exportPathLineEdit.setText(exportPath)
    # endregion

    # region Slots
    @QtCore.Slot()
    def on_newReferencedAssetAction_triggered(self):
        """
        Slot method for the `newReferencedAssetAction` widget's `triggered` signal.

        :rtype: None
        """

        # Collect references from scene
        #
        references = list(map(fnreference.FnReference, fnreference.FnReference.iterSceneReferences(topLevelOnly=False)))
        numReferences = len(references)

        if numReferences == 0:

            QtWidgets.QMessageBox.information(self, 'Create Referenced Asset', 'Scene contains no references!')
            return

        # Collect unused referenced assets
        #
        topLevelItems = [f'{reference.associatedNamespace()}:{reference.filename()}' for reference in references]
        currentItems = [self.referencedAssetComboBox.itemText(i) for i in range(self.referencedAssetComboBox.count())]

        filteredItems = [item for item in topLevelItems if item not in currentItems]
        numFilteredItems = len(filteredItems)

        if numFilteredItems == 0:

            QtWidgets.QMessageBox.information(self, 'Create Referenced Asset', 'Scene contains no more references!')
            return

        # Prompt user for referenced asset
        #
        item, okay = QtWidgets.QInputDialog.getItem(
            self,
            'Create Referenced Asset',
            'Select a Referenced Asset:',
            filteredItems,
            editable=False
        )

        if okay:

            # Create new referenced asset
            #
            index = topLevelItems.index(item)
            guid = references[index].guid()
            exportRange = self.defaultExportRange()

            referencedAsset = fbxreferencedasset.FbxReferencedAsset(guid=guid, exportRanges=[exportRange])
            self.referencedAssets.append(referencedAsset)

            self.invalidateReferencedAssets()

            # Update combo-box selection
            #
            lastIndex = len(self.referencedAssets) - 1
            self.referencedAssetComboBox.setCurrentIndex(lastIndex)

        else:

            log.info('Operation aborted...')

    @QtCore.Slot()
    def on_deleteReferencedAssetPushButton_clicked(self):
        """
        Slot method for the `deleteReferencedAssetPushButton` widget's `triggered` signal.

        :rtype: None
        """

        # Redundancy check
        #
        if len(self.referencedAssets) == 0:

            return

        # Confirm user wants to delete this referenced asset
        #
        response = QtWidgets.QMessageBox.warning(
            self,
            'Delete Sequencer',
            'Are you sure you want to delete this referenced asset and all of its export ranges?',
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
        )

        if response != QtWidgets.QMessageBox.Ok:

            log.info('Operation aborted...')
            return

        # Remove selected referenced asset
        #
        index = self.referencedAssetComboBox.currentIndex()
        del self.referencedAssets[index]

        # Invalidate export-ranges
        #
        self.invalidateReferencedAssets()

    @QtCore.Slot()
    def on_saveReferencedAssetAction_triggered(self):
        """
        Slot method for the `saveReferencedAssetAction` widget's `triggered` signal.

        :rtype: None
        """

        self.save()

    @QtCore.Slot()
    def on_addExportRangeAction_triggered(self):
        """
        Slot method for the `addExportRangeAction` widget's `triggered` signal.

        :rtype: None
        """

        exportRange = self.defaultExportRange()
        self.referencedAssetItemModel.appendRow(exportRange)

    @QtCore.Slot()
    def on_removeExportRangeAction_triggered(self, checked=False):
        """
        Slot method for the `removeExportRangeAction` widget's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        # Check if there are any rows remaining
        # We want to make sure there's always at least one export range remaining!
        #
        rowCount = self.referencedAssetItemModel.rowCount()

        if not (rowCount > 1):

            return

        # Remove selected rows
        #
        selectedRows = self.getSelectedRows()

        for (start, end) in reversed(tuple(consecutivePairs(selectedRows))):

            numRows = (end - start) + 1
            self.referencedAssetItemModel.removeRows(start, numRows)

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

            self.selectedReferencedAsset.exportRanges = jsonutils.load(importPath)
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

            jsonutils.dump(exportPath, self.selectedReferencedAsset.exportRanges, indent=4)

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

                self.selectedReferencedAsset.exportRanges[row].startFrame = self.scene.getStartTime()

        else:

            row = selectedRows[0]
            self.scene.setStartTime(self.selectedReferencedAsset.exportRanges[row].startFrame)

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

                self.selectedReferencedAsset.exportRanges[row].endFrame = self.scene.getEndTime()

        else:

            row = selectedRows[0]
            self.scene.setEndTime(self.selectedReferencedAsset.exportRanges[row].endFrame)

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

                self.selectedReferencedAsset.exportRanges[row].startFrame = self.scene.getStartTime()
                self.selectedReferencedAsset.exportRanges[row].endFrame = self.scene.getEndTime()

        else:

            row = selectedRows[0]
            self.scene.setStartTime(self.selectedReferencedAsset.exportRanges[row].startFrame)
            self.scene.setEndTime(self.selectedReferencedAsset.exportRanges[row].endFrame)

    @QtCore.Slot(bool)
    def on_referencedAssetRollout_expandedChanged(self, expanded):
        """
        Slot method for the `referencedAssetRollout` widget's `expanded` signal.

        :type expanded: bool
        :rtype: None
        """

        with qsignalblocker.QSignalBlocker(self.batchRollout):

            self.batchRollout.setExpanded(not expanded)

    @QtCore.Slot(int)
    def on_referencedAssetComboBox_currentIndexChanged(self, index):
        """
        Slot method for the `referencedAssetComboBox` widget's `currentIndexChanged` signal.

        :type index: int
        :rtype: None
        """

        # Update current referenced asset
        #
        numSequencers = len(self.referencedAssets)

        if 0 <= index < numSequencers:

            self._selectedReferencedAsset = self.referencedAssets[index]

        else:

            self._selectedReferencedAsset = None

        # Invalidate export-ranges
        #
        self.invalidateExportRanges()

    @QtCore.Slot(QtCore.QModelIndex)
    def on_referencedAssetTreeView_clicked(self, index):
        """
        Slot method for the `referencedAssetTreeView` widget's `clicked` signal.

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

        # Evaluated selected referenced asset
        #
        if self.selectedReferencedAsset is None:

            QtWidgets.QMessageBox.warning(self, 'Export Ranges', 'No referenced asset selected to export from!')
            return

        # Export selected range
        #
        self.save()

        for row in self.getSelectedRows():

            self.selectedReferencedAsset.exportRanges[row].export(checkout=self.checkout)

    @QtCore.Slot()
    def on_exportAllPushButton_clicked(self):
        """
        Slot method for the `exportAllPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Check if sequencer exists
        #
        if self.selectedReferencedAsset is None:

            QtWidgets.QMessageBox.warning(self, 'Export Ranges', 'No referenced asset selected to export from!')
            return

        # Export all ranges
        #
        self.save()

        for exportRange in self.selectedReferencedAsset.exportRanges:

            exportRange.export(checkout=self.checkout)

    @QtCore.Slot(bool)
    def on_batchRollout_expandedChanged(self, expanded):
        """
        Slot method for the `batchRollout` widget's `expanded` signal.

        :type expanded: bool
        :rtype: None
        """

        with qsignalblocker.QSignalBlocker(self.referencedAssetRollout):

            self.referencedAssetRollout.setExpanded(not expanded)

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

            # Export ranges from referenced assets
            #
            self.manager.exportAnimation(directory=directory, checkout=checkout)
            self.batchProgressBar.setValue(progress)
    # endregion
