import os
import sys

from PySide2 import QtWidgets, QtCore, QtGui
from dcc.ui import quicwindow, qrollout, qdivider, qtimespinbox
from dcc.fbx import fbxsequence

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QFbxSequenceRollout(qrollout.QRollout):
    """
    Overload of QRollout used to edit fbx sequence data.
    """

    def __init__(self, sequence, parent=None, f=QtCore.Qt.WindowFlags()):
        """
        Private method called after a new instance has been created.

        :type sequence: fbxsequence.FbxSequence
        :type parent: QtWidgets.QWidget
        :type f: int
        :rtype: None
        """

        # Call parent method
        #
        super(QFbxSequenceRollout, self).__init__('', parent=parent, f=f)

        # Declare private variables
        #
        self._sequence = sequence

        # Create name widgets
        #
        self.nameLabel = QtWidgets.QLabel('Name:')
        self.nameLabel.setObjectName('nameLabel')
        self.nameLabel.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        self.nameLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.nameLabel.setFixedSize(QtCore.QSize(50, 24))

        self.nameLineEdit = QtWidgets.QLineEdit('')
        self.nameLineEdit.setObjectName('nameLineEdit')
        self.nameLineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.nameLineEdit.setFixedHeight(24)
        self.nameLineEdit.setText(self.sequence.name)
        self.nameLineEdit.editingFinished.connect(self.on_nameLineEdit_editingFinished)

        self.nameLayout = QtWidgets.QHBoxLayout()
        self.nameLayout.setObjectName('nameLayout')
        self.nameLayout.addWidget(self.nameLabel)
        self.nameLayout.addWidget(self.nameLineEdit)

        # Create directory widgets
        #
        self.directoryLabel = QtWidgets.QLabel('Directory:')
        self.directoryLabel.setObjectName('directoryLabel')
        self.directoryLabel.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        self.directoryLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.directoryLabel.setFixedSize(QtCore.QSize(50, 24))

        self.directoryLineEdit = QtWidgets.QLineEdit('')
        self.directoryLineEdit.setObjectName('directoryLineEdit')
        self.directoryLineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.directoryLineEdit.setFixedHeight(24)
        self.directoryLineEdit.setText(self.sequence.directory)
        self.directoryLineEdit.editingFinished.connect(self.on_directoryLineEdit_editingFinished)

        self.directoryPushButton = QtWidgets.QPushButton(QtGui.QIcon(':dcc/icons/open_file'), '')
        self.directoryPushButton.setObjectName('directoryPushButton')
        self.directoryPushButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.directoryPushButton.setFixedSize(QtCore.QSize(24, 24))
        self.directoryPushButton.clicked.connect(self.on_directoryPushButton_clicked)

        self.directoryLayout = QtWidgets.QHBoxLayout()
        self.directoryLayout.setObjectName('directoryLayout')
        self.directoryLayout.addWidget(self.directoryLabel)
        self.directoryLayout.addWidget(self.directoryLineEdit)
        self.directoryLayout.addWidget(self.directoryPushButton)

        # Create path layout
        #
        self.pathLayout = QtWidgets.QVBoxLayout()
        self.pathLayout.setObjectName('pathLayout')
        self.pathLayout.addLayout(self.nameLayout)
        self.pathLayout.addLayout(self.directoryLayout)

        # Create start frame widgets
        #
        self.startLabel = QtWidgets.QLabel('Start:')
        self.startLabel.setObjectName('startLabel')
        self.startLabel.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        self.startLabel.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.startLabel.setFixedHeight(24)

        self.startTimeBox = qtimespinbox.QTimeSpinBox()
        self.startTimeBox.setObjectName('startTimeBox')
        self.startTimeBox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.startTimeBox.setFixedSize(QtCore.QSize(40, 24))
        self.startTimeBox.setMinimum(-sys.maxsize)
        self.startTimeBox.setMaximum(sys.maxsize)
        self.startTimeBox.setValue(self.sequence.startFrame)
        self.startTimeBox.valueChanged.connect(self.on_startTimeBox_valueChanged)

        self.startLayout = QtWidgets.QHBoxLayout()
        self.startLayout.addWidget(self.startLabel)
        self.startLayout.addWidget(self.startTimeBox)

        # Create end frame widgets
        #
        self.endLabel = QtWidgets.QLabel('End:')
        self.endLabel.setObjectName('endLabel')
        self.endLabel.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        self.endLabel.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.endLabel.setFixedHeight(24)

        self.endTimeBox = qtimespinbox.QTimeSpinBox(defaultType=qtimespinbox.DefaultType.EndTime)
        self.endTimeBox.setObjectName('endTimeBox')
        self.endTimeBox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.endTimeBox.setFixedSize(QtCore.QSize(40, 24))
        self.endTimeBox.setMinimum(-sys.maxsize)
        self.endTimeBox.setMaximum(sys.maxsize)
        self.endTimeBox.setValue(self.sequence.endFrame)
        self.endTimeBox.valueChanged.connect(self.on_endTimeBox_valueChanged)

        self.endLayout = QtWidgets.QHBoxLayout()
        self.endLayout.setObjectName('endLayout')
        self.endLayout.addWidget(self.endLabel)
        self.endLayout.addWidget(self.endTimeBox)

        self.durationLayout = QtWidgets.QHBoxLayout()
        self.durationLayout.setObjectName('durationLayout')
        self.durationLayout.addLayout(self.startLayout)
        self.durationLayout.addLayout(self.endLayout)

        # Create frame step widgets
        #
        self.stepLabel = QtWidgets.QLabel('Step:')
        self.stepLabel.setObjectName('stepLabel')
        self.stepLabel.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        self.stepLabel.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.stepLabel.setFixedHeight(24)

        self.stepSpinBox = QtWidgets.QSpinBox()
        self.stepSpinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.stepSpinBox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.stepSpinBox.setFixedSize(QtCore.QSize(40, 24))
        self.stepSpinBox.setMinimum(-sys.maxsize)
        self.stepSpinBox.setMaximum(sys.maxsize)
        self.stepSpinBox.setValue(self.sequence.step)
        self.stepSpinBox.valueChanged.connect(self.on_stepSpinBox_valueChanged)

        self.stepLayout = QtWidgets.QHBoxLayout()
        self.stepLayout.setObjectName('stepLayout')
        self.stepLayout.addWidget(self.stepLabel)
        self.stepLayout.addWidget(self.stepLineEdit)

        # Create time layout
        #
        self.timeLayout = QtWidgets.QVBoxLayout()
        self.timeLayout.addLayout(self.durationLayout)
        self.timeLayout.addLayout(self.stepLayout)

        # Create export set widget
        #
        self.exportSetLabel = QtWidgets.QLabel('Export Set:')
        self.exportSetLabel.setObjectName('exportSetLabel')
        self.exportSetLabel.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        self.exportSetLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.exportSetLabel.setFixedSize(QtCore.QSize(60, 24))

        self.exportSetComboBox = QtWidgets.QComboBox()
        self.exportSetComboBox.setObjectName('exportSetComboBox')
        self.exportSetComboBox.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.exportSetComboBox.setFixedHeight(24)
        self.exportSetComboBox.addItems([x.name for x in self.sequence.asset.exportSets])
        self.exportSetComboBox.setCurrentIndex(self.source.exportSetId)
        self.exportSetComboBox.currentIndexChanged.connect(self.on_exportSetComboBox_currentIndexChanged)

        self.exportSetLayout = QtWidgets.QHBoxLayout()
        self.exportSetLayout.setObjectName('exportSetLayout')
        self.exportSetLayout.addWidget(self.exportSetLabel)
        self.exportSetLayout.addWidget(self.exportSetComboBox)

        # Edit central layout
        #
        centralLayout = QtWidgets.QHBoxLayout()
        centralLayout.addLayout(self.timeLayout)
        centralLayout.addWidget(qdivider.QDivider(QtCore.Qt.Vertical))
        centralLayout.addLayout(self.pathLayout)
        centralLayout.addWidget(qdivider.QDivider(QtCore.Qt.Vertical))
        centralLayout.addLayout(self.exportSetLayout)

        self.setLayout(centralLayout)
    # endregion

    # region Properties
    @property
    def sequence(self):
        """
        Getter method that returns the associated fbx sequence.

        :rtype: fbxsequence.FbxSequence
        """

        return self._sequence
    # endregion

    # region Methods
    def projectPath(self):
        """
        Returns the current project path.

        :rtype: str
        """

        pass

    def getExistingDirectory(self):
        """
        Prompts the user for an existing directory.

        :rtype: str
        """

        # Prompt user for save path
        #
        projectPath = os.path.expandvars(self.projectPath())

        return QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption='Select Directory',
            dir=projectPath,
            options=QtWidgets.QFileDialog.ShowDirsOnly
        )

    def invalidate(self):
        """
        Method used to preview the resolved file path.
        This method will take the project path and join it with the relative file path.
        All environment variables will be expanded for debugging purposes.

        :rtype: None
        """

        # Concatenate path
        #
        self.setTitle(
            os.path.join(
                os.path.expandvars(self.projectPath()),
                os.path.expandvars(self.sequence.directory),
                '{name}.fbx'.format(name=self.sequence.name)
            )
        )
    # endregion

    # region Events
    def eventFilter(self, watched, event):
        """
        Inherited method called whenever a widget event requires inspection.
        The only events we're interested in here are child and focus events.
        This allows us to auto-check the rollout whenever the user changes focus.

        :type watched: QtWidgets.QWidget
        :type event: QtCore.QEvent
        :rtype: bool
        """

        # Inspect event type
        #
        if event.type() == QtCore.QEvent.ChildAdded:

            event.child().installEventFilter(self)

        elif event.type() == QtCore.QEvent.ChildRemoved:

            event.child().removeEventFilter(self)

        elif event.type() == QtCore.QEvent.FocusIn:

            self.setChecked(True)  # SUPER dirty but it gets the job done~

        else:

            pass

        # Call parent method
        #
        return super(QFbxSequenceRollout, self).eventFilter(watched, event)
    # endregion

    # region Slots
    @QtCore.Slot(int)
    def on_startTimeBox_valueChanged(self, value):
        """
        Value changed slot method responsible for updating the start time.

        :type value: int
        :rtype: None
        """

        pass

    @QtCore.Slot(int)
    def on_endTimeBox_valueChanged(self, value):
        """
        Value changed slot method responsible for updating the end time.

        :type value: int
        :rtype: None
        """

        pass

    @QtCore.Slot(int)
    def on_stepSpinBox_valueChanged(self, value):
        """
        Value changed slot method responsible for updating the bake increment.

        :type value: int
        :rtype: None
        """

        pass

    @QtCore.Slot(int)
    def on_exportSetComboBox_currentIndexChanged(self, index):
        """
        Current index changed slot method responsible for updating the associated export set.

        :type index: int
        :rtype: None
        """

        self.sequence.exportSetId = index

    @QtCore.Slot()
    def on_nameLineEdit_editingFinished(self):
        """
        Editing finished slot method responsible for updating the sequence name.

        :rtype: None
        """

        self.sequence.name = self.sender().text()
        self.invalidate()

    @QtCore.Slot()
    def on_directoryLineEdit_editingFinished(self):
        """
        Editing finished slot method responsible for updating the sequence directory.

        :rtype: None
        """

        self.sequence.directory = self.sender().text()
        self.invalidate()

    @QtCore.Slot(bool)
    def on_directoryPushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for updating the sequence directory.

        :type checked: bool
        :rtype: None
        """

        directory = self.getExistingDirectory()

        if directory:

            self.sequence.directory = directory
            self.invalidate()
    # endregion


class QFbxSequenceEditor(quicwindow.QUicWindow):
    """
    Overload of QUicWindow used to edit fbx sequence data.
    """

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :keyword parent: QtWidgets.QWidget
        :keyword flags: QtCore.Qt.WindowFlags
        """

        # Call parent method
        #
        super(QFbxSequenceEditor, self).__init__(*args, **kwargs)

        # Define class variables
        #
        self._assets = None
        self._currentAsset = None
        self._sequences = None
        self._currentSequence = None
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

    def closeEvent(self, event):
        """
        Event method called after the window has been closed.

        :type event: QtGui.QCloseEvent
        :rtype: None
        """

        # Call inherited method
        #
        super(QFbxSequenceEditor, self).closeEvent(event)
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
    def on_addSequencePushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for adding a new fbx sequence.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(bool)
    def on_removeSequencePushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for remove the current fbx sequence.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(bool)
    def on_startTimePushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for adopting the current fbx sequence's start time.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(bool)
    def on_endTimePushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for adopting the current fbx sequence's end time.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(bool)
    def on_timeRangePushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for adopting the current fbx sequence's time range.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(bool)
    def on_timelinePushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for adopting the current fbx sequence's time range.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(bool)
    def on_exportPushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for exporting the current fbx sequence.

        :type checked: bool
        :rtype: None
        """

        pass

    @QtCore.Slot(bool)
    def on_exportAllPushButton_clicked(self, checked=False):
        """
        Clicked slot method responsible for exporting all of the fbx sequences.

        :type checked: bool
        :rtype: None
        """

        pass
    # endregion
