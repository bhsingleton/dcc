from . import qmaindialog
from ...vendor.Qt import QtCore, QtWidgets, QtGui
from ...generators.inclusiverange import inclusiveRange

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QLoggerDialog(qmaindialog.QMainDialog):
    """
    Overload of `QMainDialog` that interfaces with logger levels.
    """

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QMainWindow
        :key f: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        super(QLoggerDialog, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._logLevels = dict(self.iterLogLevels())
        self._loggers = dict(self.iterLoggers())
        self._edits = {}

        # Declare public variables
        #
        self.loggerLayout = None
        self.loggerGroupBox = None
        self.loggerTableWidget = None

        self.buttonsLayout = None
        self.buttonsWidget = None
        self.okayPushButton = None
        self.cancelPushButton = None

    def __post_init__(self, *args, **kwargs):
        """
        Private method called after an instance has initialized.

        :rtype: None
        """

        # Call parent method
        #
        super(QLoggerDialog, self).__post_init__(*args, **kwargs)

        # Refresh user interface
        #
        self.refresh()

    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QLoggerDialog, self).__setup_ui__(*args, **kwargs)
        
        # Initialize dialog
        #
        self.setWindowTitle("|| Edit Logger Levels")
        self.setMinimumSize(QtCore.QSize(500, 300))

        # Initialize central layout
        #
        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('centralLayout')

        self.setLayout(centralLayout)
        
        # Initialize logging table widget
        #
        self.loggerLayout = QtWidgets.QVBoxLayout()
        self.loggerLayout.setObjectName('loggerLayout')

        self.loggerGroupBox = QtWidgets.QGroupBox('Loggers:')
        self.loggerGroupBox.setObjectName('loggerGroupBox')
        self.loggerGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.loggerGroupBox.setLayout(self.loggerLayout)

        self.loggerTableWidget = QtWidgets.QTableWidget()
        self.loggerTableWidget.setObjectName('loggerTableWidget')
        self.loggerTableWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred))
        self.loggerTableWidget.setStyleSheet('QTableWidget:item { height: 24; }')
        self.loggerTableWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.loggerTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.loggerTableWidget.setAlternatingRowColors(True)
        self.loggerTableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.loggerTableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.loggerTableWidget.setColumnCount(2)
        self.loggerTableWidget.setHorizontalHeaderLabels(['Name', 'Level'])
        
        horizontalHeader = self.loggerTableWidget.horizontalHeader()  # type: QtWidgets.QHeaderView
        horizontalHeader.setStretchLastSection(True)
        horizontalHeader.setMinimumSectionSize(50)
        horizontalHeader.setDefaultSectionSize(100)

        verticalHeader = self.loggerTableWidget.verticalHeader()  # type: QtWidgets.QHeaderView
        verticalHeader.setStretchLastSection(False)
        verticalHeader.setMinimumSectionSize(24)
        verticalHeader.setDefaultSectionSize(24)
        verticalHeader.setVisible(False)

        self.loggerLayout.addWidget(self.loggerTableWidget)

        centralLayout.addWidget(self.loggerGroupBox)

        # Initialize buttons layout
        #
        self.buttonsLayout = QtWidgets.QHBoxLayout()
        self.buttonsLayout.setObjectName('buttonsLayout')
        self.buttonsLayout.setContentsMargins(0, 0, 0, 0)

        self.buttonsWidget = QtWidgets.QWidget()
        self.buttonsWidget.setObjectName('buttonsWidget')
        self.buttonsWidget.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.buttonsWidget.setFixedHeight(24)
        self.buttonsWidget.setLayout(self.buttonsLayout)

        self.okayPushButton = QtWidgets.QPushButton('OK')
        self.okayPushButton.setObjectName('okayPushButton')
        self.okayPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred))
        self.okayPushButton.clicked.connect(self.accept)

        self.cancelPushButton = QtWidgets.QPushButton('Cancel')
        self.cancelPushButton.setObjectName('cancelPushButton')
        self.cancelPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred))
        self.cancelPushButton.clicked.connect(self.reject)

        self.buttonsLayout.addWidget(self.okayPushButton)
        self.buttonsLayout.addWidget(self.cancelPushButton)

        centralLayout.addWidget(self.buttonsWidget)
    # endregion

    # region Events
    def eventFilter(self, watched, event):
        """
        Filters events if this object has been installed as an event filter for the watched object.
        In your reimplementation of this function, if you want to filter the event out, i.e. stop it being handled further, return true; otherwise return false.

        :type watched: QtCore.QObject
        :type event: QtCore.QEvent
        :rtype bool
        """

        if isinstance(watched, QtWidgets.QComboBox) and isinstance(event, QtGui.QWheelEvent):

            return True  # This blocks the scroll-wheel from messing up influences!

        else:

            return False
    # endregion

    # region Methods
    @classmethod
    def iterLogLevels(cls):
        """
        Returns a generator that yields log level name-value pairs.

        :rtype: Iterator[Tuple[str, int]]
        """

        for level in inclusiveRange(0, logging.CRITICAL, 10):

            yield logging.getLevelName(level), level

    @classmethod
    def iterLoggers(cls):
        """
        Returns a generator that yields name-logger pairs.

        :rtype: Iterator[Tuple[str, logging.Logger]]
        """

        for (name, logger) in logging.Logger.manager.loggerDict.items():

            if isinstance(logger, logging.Logger):

                yield name, logger

            else:

                continue

    def refresh(self):
        """
        Refreshes the user interface.

        :rtype: None
        """

        # Iterate through loggers
        #
        loggers = dict(sorted(self._loggers.items(), key=lambda pair: pair[0]))
        logLevelNames = list(self._logLevels.keys())
        logLevelValues = list(self._logLevels.values())

        rowCount = len(loggers)
        self.loggerTableWidget.setRowCount(rowCount)

        for (row, (name, logger)) in enumerate(loggers.items()):

            # Create logger item
            #
            tableItem = QtWidgets.QTableWidgetItem(name)

            # Create logging level combo box
            #
            comboBox = QtWidgets.QComboBox(parent=self.loggerTableWidget)
            comboBox.setWhatsThis(name)
            comboBox.setFocusPolicy(QtCore.Qt.ClickFocus)
            comboBox.addItems(logLevelNames)
            comboBox.installEventFilter(self)
            comboBox.setCurrentIndex(logLevelValues.index(logger.level))
            comboBox.currentIndexChanged.connect(self.on_loggerComboBox_currentIndexChanged)

            # Assign items to table
            #
            self.loggerTableWidget.setItem(row, 0, tableItem)
            self.loggerTableWidget.setCellWidget(row, 1, comboBox)

        # Resize items to contents
        #
        self.loggerTableWidget.resizeColumnsToContents()
    # endregion

    # region Slots
    @QtCore.Slot(int)
    def on_loggerComboBox_currentIndexChanged(self, index):
        """
        Slot method for the logger combo-box's `currentIndexChanged` signal.

        :type index: int
        :rtype: None
        """

        sender = self.sender()
        name = sender.whatsThis()
        levels = list(self._logLevels.values())

        self._edits[name] = levels[index]

    @QtCore.Slot()
    def accept(self):
        """
        Slot method for the dialog's `accept` signal.

        :rtype: None
        """

        # Push edits to loggers
        #
        for (name, level) in self._edits.items():

            self._loggers[name].level = level

        # Call parent method
        #
        super(QLoggerDialog, self).accept()
    # endregion
