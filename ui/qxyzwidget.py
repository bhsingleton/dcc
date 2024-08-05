from Qt import QtCore, QtWidgets, QtGui

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QXyzWidget(QtWidgets.QWidget):
    """
    Overload of `QWidget` that provides an interface for specifying XYZ axes.
    """

    # region Dunderscores
    def __init__(self, *args, parent=None, f=QtCore.Qt.WindowFlags()):
        """
        Private method called after a new instance has been created.

        :type args: Union[str, None]
        :type parent: QtWidgets.QWidget
        :type f: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        super(QXyzWidget, self).__init__(parent=parent)

        # Initialize cartesian buttons
        #
        numArgs = len(args)
        text = args[0] if (numArgs == 1) else ''

        self.cartesianPushButton = QtWidgets.QPushButton(text)
        self.cartesianPushButton.setObjectName('cartesianPushButton')
        self.cartesianPushButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.cartesianPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.cartesianPushButton.setCheckable(True)
        self.cartesianPushButton.toggled.connect(self.on_cartesianPushButton_toggled)

        self.cartesianXPushButton = QtWidgets.QPushButton('X')
        self.cartesianXPushButton.setObjectName('cartesianXPushButton')
        self.cartesianXPushButton.setMinimumWidth(16.0)
        self.cartesianXPushButton.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.cartesianXPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.cartesianXPushButton.setCheckable(True)

        self.cartesianYPushButton = QtWidgets.QPushButton('Y')
        self.cartesianYPushButton.setObjectName('cartesianYPushButton')
        self.cartesianYPushButton.setMinimumWidth(16.0)
        self.cartesianYPushButton.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.cartesianYPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.cartesianYPushButton.setCheckable(True)

        self.cartesianZPushButton = QtWidgets.QPushButton('Z')
        self.cartesianZPushButton.setObjectName('cartesianZPushButton')
        self.cartesianZPushButton.setMinimumWidth(16.0)
        self.cartesianZPushButton.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.cartesianZPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.cartesianZPushButton.setCheckable(True)

        self.cartesianButtonGroup = QtWidgets.QButtonGroup(parent=self)
        self.cartesianButtonGroup.setObjectName('cartesianButtonGroup')
        self.cartesianButtonGroup.setExclusive(False)
        self.cartesianButtonGroup.addButton(self.cartesianXPushButton, id=0)
        self.cartesianButtonGroup.addButton(self.cartesianYPushButton, id=1)
        self.cartesianButtonGroup.addButton(self.cartesianZPushButton, id=2)
        self.cartesianButtonGroup.buttonToggled.connect(self.on_cartesianButtonGroup_buttonToggled)

        # Initialize central layout
        #
        centralLayout = QtWidgets.QHBoxLayout()
        centralLayout.setObjectName('centralLayout')
        centralLayout.setSpacing(1)
        centralLayout.setContentsMargins(0, 0, 0, 0)
        centralLayout.addWidget(self.cartesianPushButton)
        centralLayout.addWidget(self.cartesianXPushButton)
        centralLayout.addWidget(self.cartesianYPushButton)
        centralLayout.addWidget(self.cartesianZPushButton)

        self.setLayout(centralLayout)
    # endregion

    # region Methods
    def text(self):
        """
        Returns the button text.

        :rtype: str
        """

        return self.cartesianPushButton.text()

    def setText(self, text):
        """
        Updates the button text.

        :type text: str
        :rtype: None
        """

        self.cartesianPushButton.setText(text)

    def checkStates(self, inverse=False):
        """
        Returns a list of check states from each button.

        :type inverse: bool
        :rtype: Tuple[bool, bool, bool]
        """

        if inverse:

            return [not x.isChecked() for x in self.cartesianButtonGroup.buttons()]

        else:

            return [x.isChecked() for x in self.cartesianButtonGroup.buttons()]

    def setCheckStates(self, checkStates):
        """
        Updates the check states for each button.

        :type checkStates: Tuple[bool, bool, bool]
        :rtype: None
        """

        for (index, checkState) in enumerate(checkStates):

            self.cartesianButtonGroup.button(index).setChecked(checkState)

    def flags(self, prefix='', inverse=False):
        """
        Returns the check states but in the form of key-value pairs.

        :type prefix: str
        :type inverse: bool
        :rtype: Dict[str, bool]
        """

        return {f'{prefix}{axis}': checked for (checked, axis) in zip(self.checkStates(inverse=inverse), ('X', 'Y', 'Z'))}
    # endregion

    # region Slots
    @QtCore.Slot(bool)
    def on_cartesianPushButton_toggled(self, state):
        """
        Slot method for the `cartesianPushButton` widget's `toggled` signal.
        This slot is responsible for overriding the button group state.

        :type state: bool
        :rtype: None
        """

        for button in self.cartesianButtonGroup.buttons():

            button.setChecked(state)

    @QtCore.Slot(int)
    def on_cartesianButtonGroup_buttonToggled(self, index):
        """
        Slot method for the `cartesianButtonGroup` widget's `buttonToggled` signal.
        This slot is responsible for syncing the master button with the button group.

        :type index: int
        :rtype: None
        """

        isChecked = self.cartesianPushButton.isChecked()
        checkStates = self.checkStates()

        if isChecked and not all(checkStates):

            self.cartesianPushButton.setChecked(False)
            self.setCheckStates(checkStates)

        elif not isChecked and all(checkStates):

            self.cartesianPushButton.setChecked(True)

        else:

            pass
    # endregion
