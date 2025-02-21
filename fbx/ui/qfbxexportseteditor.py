import os
import webbrowser

from copy import copy
from ..libs import fbxio, fbxasset, fbxexportset, FbxFileType, FbxFileVersion
from ... import fnscene, fnnode, fnskin, fnnotify
from ...python import stringutils
from ...json import jsonutils
from ...ui import qsingletonwindow, qdirectoryedit, qfileedit
from ...ui.dialogs import qlistdialog
from ...ui.models import qpsonitemmodel, qpsonstyleditemdelegate
from ...vendor.Qt import QtCore, QtWidgets, QtGui

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QFbxExportSetEditor(qsingletonwindow.QSingletonWindow):
    """
    Overload of `QSingletonWindow` that interfaces with FBX export-set data.
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

    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QFbxExportSetEditor, self).__setup_ui__(*args, **kwargs)

        # Initialize main window
        #
        self.setWindowTitle("|| Fbx Export Set Editor")
        self.setMinimumSize(QtCore.QSize(400, 700))

        # Initialize main menu-bar
        #
        mainMenuBar = QtWidgets.QMenuBar()
        mainMenuBar.setObjectName('mainMenuBar')

        self.setMenuBar(mainMenuBar)

        # Initialize file menu
        #
        self.fileMenu = mainMenuBar.addMenu('&File')
        self.fileMenu.setObjectName('fileMenu')
        self.fileMenu.setTearOffEnabled(True)

        self.saveAction = QtWidgets.QAction(QtGui.QIcon(':dcc/icons/save_file.svg'), '&Save', parent=self.fileMenu)
        self.saveAction.setObjectName('saveAction')
        self.saveAction.triggered.connect(self.on_saveAction_triggered)

        self.importAction = QtWidgets.QAction(QtGui.QIcon(':dcc/icons/import_file.svg'), '&Import', parent=self.fileMenu)
        self.importAction.setObjectName('importAction')
        self.importAction.triggered.connect(self.on_importAction_triggered)

        self.exportAction = QtWidgets.QAction(QtGui.QIcon(':dcc/icons/export_file.svg'), '&Export', parent=self.fileMenu)
        self.exportAction.setObjectName('exportAction')
        self.exportAction.triggered.connect(self.on_exportAction_triggered)

        self.fileMenu.addAction(self.saveAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addActions([self.importAction, self.exportAction])

        # Initialize settings menu
        #
        self.settingsMenu = mainMenuBar.addMenu('&Settings')
        self.settingsMenu.setObjectName('fileMenu')
        self.settingsMenu.setTearOffEnabled(True)

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
        self.helpMenu = mainMenuBar.addMenu('&Help')
        self.helpMenu.setObjectName('helpMenu')
        self.helpMenu.setTearOffEnabled(True)

        self.usingFbxExportSetEditorAction = QtWidgets.QAction('Using Fbx Export Set Editor', parent=self.helpMenu)
        self.usingFbxExportSetEditorAction.setObjectName('usingFbxExportSetEditorAction')
        self.usingFbxExportSetEditorAction.triggered.connect(self.on_usingFbxExportSetEditorAction_triggered)

        self.helpMenu.addAction(self.usingFbxExportSetEditorAction)

        # Initialize central widget
        #
        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('centralLayout')

        centralWidget = QtWidgets.QWidget()
        centralWidget.setObjectName('centralWidget')
        centralWidget.setLayout(centralLayout)

        self.setCentralWidget(centralWidget)

        # Initialize asset group-box
        #
        self.assetLayout = QtWidgets.QGridLayout()
        self.assetLayout.setObjectName('assetLayout')

        self.assetGroupBox = QtWidgets.QGroupBox('Asset:')
        self.assetGroupBox.setObjectName('assetGroupBox')
        self.assetGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.assetGroupBox.setLayout(self.assetLayout)

        self.assetNameLabel = QtWidgets.QLabel('Name:')
        self.assetNameLabel.setObjectName('assetNameLabel')
        self.assetNameLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.assetNameLabel.setFixedSize(QtCore.QSize(60, 24))
        self.assetNameLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.assetNameLineEdit = QtWidgets.QLineEdit()
        self.assetNameLineEdit.setObjectName('assetNameLineEdit')
        self.assetNameLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.assetNameLineEdit.setFixedHeight(24)
        self.assetNameLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.assetNameLineEdit.setClearButtonEnabled(True)
        self.assetNameLineEdit.textChanged.connect(self.on_assetNameLineEdit_textChanged)

        self.savePushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/save_file.svg'), '')
        self.savePushButton.setObjectName('savePushButton')
        self.savePushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.savePushButton.setFixedSize(QtCore.QSize(24, 24))
        self.savePushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.savePushButton.clicked.connect(self.on_savePushButton_clicked)

        self.assetDirectoryLabel = QtWidgets.QLabel('Directory:')
        self.assetDirectoryLabel.setObjectName('assetDirectoryLabel')
        self.assetDirectoryLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.assetDirectoryLabel.setFixedSize(QtCore.QSize(60, 24))
        self.assetDirectoryLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.assetDirectoryLineEdit = QtWidgets.QLineEdit()
        self.assetDirectoryLineEdit.setObjectName('assetDirectoryLineEdit')
        self.assetDirectoryLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.assetDirectoryLineEdit.setFixedHeight(24)
        self.assetDirectoryLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.assetDirectoryLineEdit.setClearButtonEnabled(True)
        self.assetDirectoryLineEdit.textChanged.connect(self.on_assetDirectoryLineEdit_textChanged)

        self.assetDirectoryPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/open_folder.svg'), '')
        self.assetDirectoryPushButton.setObjectName('assetDirectoryPushButton')
        self.assetDirectoryPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.assetDirectoryPushButton.setFixedSize(QtCore.QSize(24, 24))
        self.assetDirectoryPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.assetDirectoryPushButton.clicked.connect(self.on_assetDirectoryPushButton_clicked)

        self.fileTypeLabel = QtWidgets.QLabel('File Type:')
        self.fileTypeLabel.setObjectName('fileTypeLabel')
        self.fileTypeLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.fileTypeLabel.setFixedSize(QtCore.QSize(60, 24))
        self.fileTypeLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.fileTypeComboBox = QtWidgets.QComboBox()
        self.fileTypeComboBox.setObjectName('fileTypeComboBox')
        self.fileTypeComboBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.fileTypeComboBox.setFixedHeight(24)
        self.fileTypeComboBox.addItems([str(member.name) for member in FbxFileType])
        self.fileTypeComboBox.currentIndexChanged.connect(self.on_fileTypeComboBox_currentIndexChanged)

        self.fileVersionLabel = QtWidgets.QLabel('File Version:')
        self.fileVersionLabel.setObjectName('fileVersionLabel')
        self.fileVersionLabel.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.fileVersionLabel.setFixedSize(QtCore.QSize(60, 24))
        self.fileVersionLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.fileVersionComboBox = QtWidgets.QComboBox()
        self.fileVersionComboBox.setObjectName('fileVersionComboBox')
        self.fileVersionComboBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.fileVersionComboBox.setFixedHeight(24)
        self.fileVersionComboBox.addItems([str(member.name) for member in FbxFileVersion])
        self.fileVersionComboBox.currentIndexChanged.connect(self.on_fileVersionComboBox_currentIndexChanged)

        self.assetLayout.addWidget(self.assetNameLabel, 0, 0)
        self.assetLayout.addWidget(self.assetNameLineEdit, 0, 1)
        self.assetLayout.addWidget(self.savePushButton, 0, 2)
        self.assetLayout.addWidget(self.assetDirectoryLabel, 1, 0)
        self.assetLayout.addWidget(self.assetDirectoryLineEdit, 1, 1)
        self.assetLayout.addWidget(self.assetDirectoryPushButton, 1, 2)
        self.assetLayout.addWidget(self.fileTypeLabel, 2, 0)
        self.assetLayout.addWidget(self.fileTypeComboBox, 2, 1, 1, 2)
        self.assetLayout.addWidget(self.fileVersionLabel, 3, 0)
        self.assetLayout.addWidget(self.fileVersionComboBox, 3, 1, 1, 2)

        centralLayout.addWidget(self.assetGroupBox)

        # Initialize export-sets group-box
        #
        self.exportSetLayout = QtWidgets.QVBoxLayout()
        self.exportSetLayout.setObjectName('exportSetLayout')

        self.exportSetGroupBox = QtWidgets.QGroupBox('Export Sets:')
        self.exportSetGroupBox.setObjectName('exportSetGroupBox')
        self.exportSetGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.exportSetGroupBox.setLayout(self.exportSetLayout)

        self.exportSetComboBox = QtWidgets.QComboBox()
        self.exportSetComboBox.setObjectName('exportSetComboBox')
        self.exportSetComboBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.exportSetComboBox.setFixedHeight(24)
        self.exportSetComboBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.exportSetComboBox.currentIndexChanged.connect(self.on_exportSetComboBox_currentIndexChanged)

        self.newExportSetPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/new_file.svg'), '')
        self.newExportSetPushButton.setObjectName('newExportSetPushButton')
        self.newExportSetPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.newExportSetPushButton.setFixedSize(QtCore.QSize(24, 24))
        self.newExportSetPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.newExportSetPushButton.clicked.connect(self.on_newExportSetPushButton_clicked)

        self.duplicateExportSetPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/copy_file.svg'), '')
        self.duplicateExportSetPushButton.setObjectName('duplicateExportSetPushButton')
        self.duplicateExportSetPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.duplicateExportSetPushButton.setFixedSize(QtCore.QSize(24, 24))
        self.duplicateExportSetPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.duplicateExportSetPushButton.clicked.connect(self.on_duplicateExportSetPushButton_clicked)

        self.renameExportSetPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/rename.svg'), '')
        self.renameExportSetPushButton.setObjectName('renameExportSetPushButton')
        self.renameExportSetPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.renameExportSetPushButton.setFixedSize(QtCore.QSize(24, 24))
        self.renameExportSetPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.renameExportSetPushButton.clicked.connect(self.on_renameExportSetPushButton_clicked)

        self.reorderExportSetPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/reorder.svg'), '')
        self.reorderExportSetPushButton.setObjectName('reorderExportSetPushButton')
        self.reorderExportSetPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.reorderExportSetPushButton.setFixedSize(QtCore.QSize(24, 24))
        self.reorderExportSetPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.reorderExportSetPushButton.clicked.connect(self.on_reorderExportSetPushButton_clicked)

        self.deleteExportSetPushButton = QtWidgets.QPushButton(QtGui.QIcon(':/dcc/icons/delete.svg'), '')
        self.deleteExportSetPushButton.setObjectName('deleteExportSetPushButton')
        self.deleteExportSetPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        self.deleteExportSetPushButton.setFixedSize(QtCore.QSize(24, 24))
        self.deleteExportSetPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.deleteExportSetPushButton.clicked.connect(self.on_deleteExportSetPushButton_clicked)

        self.exportSetButtonsLayout = QtWidgets.QHBoxLayout()
        self.exportSetButtonsLayout.setObjectName('exportSetButtonsLayout')
        self.exportSetButtonsLayout.setContentsMargins(0, 0, 0, 0)
        self.exportSetButtonsLayout.addWidget(self.exportSetComboBox)
        self.exportSetButtonsLayout.addWidget(self.newExportSetPushButton)
        self.exportSetButtonsLayout.addWidget(self.duplicateExportSetPushButton)
        self.exportSetButtonsLayout.addWidget(self.renameExportSetPushButton)
        self.exportSetButtonsLayout.addWidget(self.reorderExportSetPushButton)
        self.exportSetButtonsLayout.addWidget(self.deleteExportSetPushButton)

        self.exportSetTreeView = QtWidgets.QTreeView()
        self.exportSetTreeView.setObjectName('exportSetTreeView')
        self.exportSetTreeView.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.exportSetTreeView.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.exportSetTreeView.setMouseTracking(True)
        self.exportSetTreeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.exportSetTreeView.setStyleSheet('QTreeView::item { height: 24px; }')
        self.exportSetTreeView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.exportSetTreeView.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | QtWidgets.QAbstractItemView.EditKeyPressed)
        self.exportSetTreeView.setDragEnabled(True)
        self.exportSetTreeView.setDragDropOverwriteMode(False)
        self.exportSetTreeView.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.exportSetTreeView.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.exportSetTreeView.setAlternatingRowColors(True)
        self.exportSetTreeView.setSelectionMode(QtWidgets.QAbstractItemView.ContiguousSelection)
        self.exportSetTreeView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.exportSetTreeView.setUniformRowHeights(True)
        self.exportSetTreeView.setAnimated(True)
        self.exportSetTreeView.setExpandsOnDoubleClick(False)
        self.exportSetTreeView.customContextMenuRequested.connect(self.on_exportSetTreeView_customContextMenuRequested)

        self.exportSetTreeHeader = self.exportSetTreeView.header()
        self.exportSetTreeHeader.setDefaultSectionSize(200)
        self.exportSetTreeHeader.setMinimumSectionSize(100)
        self.exportSetTreeHeader.setStretchLastSection(True)
        self.exportSetTreeHeader.setVisible(True)

        self.exportSetItemModel = qpsonitemmodel.QPSONItemModel(parent=self.exportSetTreeView)
        self.exportSetItemModel.setObjectName('exportSetItemModel')

        self.exportSetTreeView.setModel(self.exportSetItemModel)

        self.exportSetItemDelegate = qpsonstyleditemdelegate.QPSONStyledItemDelegate(parent=self.exportSetTreeView)
        self.exportSetItemDelegate.setObjectName('exportSetItemDelegate')

        self.exportSetTreeView.setItemDelegate(self.exportSetItemDelegate)

        self.exportSetLayout.addLayout(self.exportSetButtonsLayout)
        self.exportSetLayout.addWidget(self.exportSetTreeView)

        centralLayout.addWidget(self.exportSetGroupBox)

        # Initialize export group-box
        #
        self.exportLayout = QtWidgets.QVBoxLayout()
        self.exportLayout.setObjectName('exportLayout')

        self.exportGroupBox = QtWidgets.QGroupBox('Export:')
        self.exportGroupBox.setObjectName('exportGroupBox')
        self.exportGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.exportGroupBox.setLayout(self.exportLayout)

        self.exportPathLineEdit = QtWidgets.QLineEdit()
        self.exportPathLineEdit.setObjectName('exportPathLineEdit')
        self.exportPathLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.exportPathLineEdit.setFixedHeight(24)
        self.exportPathLineEdit.setFocusPolicy(QtCore.Qt.NoFocus)
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

        self.exportSelectionPushButton = QtWidgets.QPushButton('Export Selection')
        self.exportSelectionPushButton.setObjectName('exportSelectionPushButton')
        self.exportSelectionPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.exportSelectionPushButton.setFixedHeight(24)
        self.exportSelectionPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.exportSelectionPushButton.clicked.connect(self.on_exportSelectionPushButton_clicked)

        self.exportSubsetPushButton = QtWidgets.QPushButton('Export Subset')
        self.exportSubsetPushButton.setObjectName('exportSubsetPushButton')
        self.exportSubsetPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.exportSubsetPushButton.setFixedHeight(24)
        self.exportSubsetPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.exportSubsetPushButton.clicked.connect(self.on_exportSubsetPushButton_clicked)

        self.exportAllPushButton = QtWidgets.QPushButton('Export All')
        self.exportAllPushButton.setObjectName('exportAllPushButton')
        self.exportAllPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.exportAllPushButton.setFixedHeight(24)
        self.exportAllPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.exportAllPushButton.clicked.connect(self.on_exportAllPushButton_clicked)

        self.exportButtonsLayout = QtWidgets.QGridLayout()
        self.exportButtonsLayout.setObjectName('exportButtonsLayout')
        self.exportButtonsLayout.setContentsMargins(0, 0, 0, 0)
        self.exportButtonsLayout.addWidget(self.exportPushButton, 0, 0)
        self.exportButtonsLayout.addWidget(self.exportSelectionPushButton, 0, 1)
        self.exportButtonsLayout.addWidget(self.exportSubsetPushButton, 1, 0)
        self.exportButtonsLayout.addWidget(self.exportAllPushButton, 1, 1)

        self.exportLayout.addLayout(self.exportPathLayout)
        self.exportLayout.addLayout(self.exportButtonsLayout)

        centralLayout.addWidget(self.exportGroupBox)

        # Initialize custom context-menu
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
        super(QFbxExportSetEditor, self).saveSettings(settings)

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
        super(QFbxExportSetEditor, self).loadSettings(settings)

        # Load user settings
        #
        self.checkout = bool(settings.value('editor/checkout', defaultValue=1, type=int))

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

    # region Slots
    @QtCore.Slot()
    def on_saveAction_triggered(self):
        """
        Slot method for the `saveAction` widget's `triggered` signal.

        :rtype: None
        """

        self.manager.saveAsset(self.asset)
        self.scene.save()

    @QtCore.Slot()
    def on_importAction_triggered(self):
        """
        Slot method for the `importAction` widget's `triggered` signal.

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

    @QtCore.Slot()
    def on_exportAction_triggered(self):
        """
        Slot method for the `exportAction` widget's `triggered` signal.

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
        Slot method for the `assetNameLineEdit` widget's `textChanged` signal.

        :type text: str
        :rtype: None
        """

        self.asset.name = text

    @QtCore.Slot(bool)
    def on_useBuiltinSerializerAction_triggered(self, checked=False):
        """
        Slot method for the `useBuiltinSerializerAction` widget's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        self.asset.useBuiltinSerializer = checked

    @QtCore.Slot()
    def on_savePushButton_clicked(self):
        """
        Slot method for the `savePushButton` widget's `clicked` signal.

        :rtype: None
        """

        self.manager.saveAsset(self.asset)
        self.scene.save()
        
    @QtCore.Slot(str)
    def on_assetDirectoryLineEdit_textChanged(self, text):
        """
        Slot method for the `assetDirectoryLineEdit` widget's `textChanged` signal.

        :type text: str
        :rtype: None
        """

        self.asset.directory = os.path.normpath(text)
        self.invalidateExportPath()

    @QtCore.Slot()
    def on_assetDirectoryPushButton_clicked(self):
        """
        Slot method for the `assetDirectoryPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Prompt user for save path
        #
        currentDirectory = os.path.expandvars(self.asset.directory)

        directory = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption='Select Asset Directory',
            dir=currentDirectory,
            options=QtWidgets.QFileDialog.ShowDirsOnly
        )

        # Check if path is valid
        #
        if not stringutils.isNullOrEmpty(directory):

            directory = self.scene.makePathVariable(directory, '$P4ROOT')
            self.assetDirectoryLineEdit.setText(directory)

        else:

            log.info('Operation aborted...')

    @QtCore.Slot(int)
    def on_fileTypeComboBox_currentIndexChanged(self, index):
        """
        Slot method for the `fileTypeComboBox` widget's `currentIndexChanged` signal.

        :type index: int
        :rtype: None
        """

        self.asset.fileType = index

    @QtCore.Slot(int)
    def on_fileVersionComboBox_currentIndexChanged(self, index):
        """
        Slot method for the `fileVersionComboBox` widget's `currentIndexChanged` signal.

        :type index: int
        :rtype: None
        """

        self.asset.fileVersion = index

    @QtCore.Slot(QtCore.QPoint)
    def on_exportSetTreeView_customContextMenuRequested(self, point):
        """
        Slot method for the `exportSetTreeView` widget's `customContextMenuRequested` signal.

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

    @QtCore.Slot()
    def on_copySelectionAction_triggered(self):
        """
        Slot method for the `copySelectionAction` widget's `triggered` signal.

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

    @QtCore.Slot()
    def on_copyInfluencesAction_triggered(self):
        """
        Slot method for the `copyInfluencesAction` widget's `triggered` signal.

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
        influenceNames = set()

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

            influenceNames = influenceNames.union({influenceName for influenceName in usedInfluenceNames if influenceName not in currentNames})

        # Extend row from influence names
        #
        numInfluenceNames = len(influenceNames)

        if numInfluenceNames > 0:

            model.extendRow(sorted(influenceNames), parent=index)

    @QtCore.Slot()
    def on_clearItemsAction_triggered(self):
        """
        Slot method for the `clearItemsAction` widget's `triggered` signal.

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
        Slot method for the `exportSetComboBox` widget's `currentIndexChanged` signal.

        :type index: int
        :rtype: None
        """

        sender = self.sender()

        if 0 <= index < sender.count():

            self._currentExportSet = self.asset.exportSets[index]
            self.invalidateExportSet()

    @QtCore.Slot()
    def on_newExportSetPushButton_clicked(self):
        """
        Slot method for the `newExportSetPushButton` widget's `clicked` signal.

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

    @QtCore.Slot()
    def on_duplicateExportSetPushButton_clicked(self):
        """
        Slot method for the `duplicateExportSetPushButton` widget's `clicked` signal.

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

    @QtCore.Slot()
    def on_renameExportSetPushButton_clicked(self):
        """
        Slot method for the `renameExportSetPushButton` widget's `clicked` signal.

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

    @QtCore.Slot()
    def on_reorderExportSetPushButton_clicked(self):
        """
        Slot method for the `reorderExportSetPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Check if current export set is valid
        #
        if len(self.asset.exportSets) == 0:

            log.warning('No export sets available to reorder!')
            return

        # Prompt user
        #
        items = {x.name: x for x in self.asset.exportSets}
        success, edits = qlistdialog.QListDialog.editItems(list(items.keys()), title='Reorder Export Sets', textFilter=stringutils.slugify, parent=self)

        if not success:

            log.info('Operation aborted...')
            return

        # Reassign fbx export sets
        #
        numEdits = len(edits)
        exportSets = [None] * numEdits

        for i in range(numEdits):

            item = edits[i]
            exportSets[i] = items.get(item, fbxexportset.FbxExportSet(name=item))

        # Assign reordered list back to asset
        #
        self.asset.exportSets = exportSets

        self.exportSetComboBox.clear()
        self.exportSetComboBox.addItems([x.name for x in self.asset.exportSets])

    @QtCore.Slot()
    def on_deleteExportSetPushButton_clicked(self):
        """
        Slot method for the `deleteExportSetPushButton` widget's `clicked` signal.

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

    @QtCore.Slot()
    def on_exportPushButton_clicked(self):
        """
        Slot method for the `exportPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Check if export set exists
        #
        if self.currentExportSet is None:

            QtWidgets.QMessageBox.warning(self, 'Export Set', 'No set available to export!')
            return

        # Export current set
        #
        self.currentExportSet.export(checkout=self.checkout)

    @QtCore.Slot()
    def on_exportSelectionPushButton_clicked(self):
        """
        Slot method for the `exportSelectionPushButton` widget's `clicked` signal.

        :rtype: None
        """

        QtWidgets.QMessageBox.information(self, 'Export Selection', 'Coming Soon!')

    @QtCore.Slot()
    def on_exportSubsetPushButton_clicked(self):
        """
        Slot method for the `exportSubsetPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Prompt user for subset
        #
        items = [x.name for x in self.asset.exportSets]
        success, selectedItems = qlistdialog.QListDialog.getItems(items, title='Export Subset', parent=self)

        if not success:

            log.info('Operation aborted...')
            return

        # Iterate through export sets
        #
        for item in selectedItems:

            index = items.index(item)
            self.asset.exportSets[index].export(checkout=self.checkout)

    @QtCore.Slot()
    def on_exportAllPushButton_clicked(self):
        """
        Slot method for the `exportAllPushButton` widget's `clicked` signal.

        :rtype: None
        """

        # Check if export set exists
        #
        if self.asset is None:

            QtWidgets.QMessageBox.warning(self, 'Export Sets', 'No asset available to export from!')
            return

        # Export all sets
        #
        for exportSet in self.asset.exportSets:

            exportSet.export(checkout=self.checkout)

    @QtCore.Slot()
    def on_usingFbxExportSetEditorAction_triggered(self):
        """
        Slot method for the `usingFbxExportSetEditorAction` widget's `clicked` signal.

        :rtype: None
        """

        webbrowser.open('https://github.com/bhsingleton/dcc')
    # endregion
