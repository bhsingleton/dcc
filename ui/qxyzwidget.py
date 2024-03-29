from Qt import QtCore, QtWidgets, QtGui

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QXyzWidget(QtWidgets.QWidget):
    """
    Overload of QWidget used to edit match flags for XYZ transform components.
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

        # Create push buttons
        #
        numArgs = len(args)
        text = args[0] if numArgs == 1 else ''

        self.matchPushButton = QtWidgets.QPushButton(text)
        self.matchPushButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.matchPushButton.setCheckable(True)
        self.matchPushButton.toggled.connect(self.on_matchPushButton_toggled)

        self.matchXPushButton = QtWidgets.QPushButton('X')
        self.matchXPushButton.setMinimumWidth(16.0)
        self.matchXPushButton.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.matchXPushButton.setCheckable(True)

        self.matchYPushButton = QtWidgets.QPushButton('Y')
        self.matchYPushButton.setMinimumWidth(16.0)
        self.matchYPushButton.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.matchYPushButton.setCheckable(True)

        self.matchZPushButton = QtWidgets.QPushButton('Z')
        self.matchZPushButton.setMinimumWidth(16.0)
        self.matchZPushButton.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        self.matchZPushButton.setCheckable(True)

        self.matchButtonGroup = QtWidgets.QButtonGroup(parent=self)
        self.matchButtonGroup.setExclusive(False)
        self.matchButtonGroup.addButton(self.matchXPushButton, id=0)
        self.matchButtonGroup.addButton(self.matchYPushButton, id=1)
        self.matchButtonGroup.addButton(self.matchZPushButton, id=2)
        self.matchButtonGroup.buttonToggled.connect(self.on_matchButtonGroup_buttonToggled)

        # Assign horizontal layout
        #
        layout = QtWidgets.QHBoxLayout()
        layout.setSpacing(1)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.matchPushButton)
        layout.addWidget(self.matchXPushButton)
        layout.addWidget(self.matchYPushButton)
        layout.addWidget(self.matchZPushButton)

        self.setLayout(layout)
    # endregion

    # region Methods
    def text(self):
        """
        Returns the button text.

        :rtype: str
        """

        return self.matchPushButton.text()

    def setText(self, text):
        """
        Updates the button text.

        :type text: str
        :rtype: None
        """

        self.matchPushButton.setText(text)

    def matches(self):
        """
        Returns a list of state values for each button.

        :rtype: List[bool, bool, bool]
        """

        return [x.isChecked() for x in self.matchButtonGroup.buttons()]

    def setMatches(self, matches):
        """
        Updates the match state for each button.

        :type matches: List[bool, bool, bool]
        :rtype: None
        """

        for (index, match) in enumerate(matches):

            self.matchButtonGroup.button(index).setChecked(match)
    # endregion

    # region Slots
    @QtCore.Slot(bool)
    def on_matchPushButton_toggled(self, state):
        """
        Toggled slot method responsible for overriding the button group state.

        :type state: bool
        :rtype: None
        """

        for button in self.matchButtonGroup.buttons():

            button.setChecked(state)

    @QtCore.Slot(int)
    def on_matchButtonGroup_buttonToggled(self, index):
        """
        Id toggled slot method responsible for syncing the master button with the button group.

        :type index: int
        :rtype: None
        """

        isChecked = self.matchPushButton.isChecked()
        matches = self.matches()

        if isChecked and not all(matches):

            self.matchPushButton.setChecked(False)
            self.setMatches(matches)

        elif not isChecked and all(matches):

            self.matchPushButton.setChecked(True)

        else:

            pass
    # endregion
