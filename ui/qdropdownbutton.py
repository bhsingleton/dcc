# -*- coding: utf-8 -*-
from ..vendor.Qt import QtCore, QtWidgets, QtGui
from ..vendor.six import string_types

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QDropDownButton(QtWidgets.QToolButton):
    """
    Overload of `QToolButton` used as a push button with drop-down menu options.
    The style has also been overriden to closely resemble the default push button.
    """

    # region Dunderscores
    def __init__(self, *args, parent=None):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :rtype: None
        """

        # Call parent method
        #
        super(QDropDownButton, self).__init__(parent)

        # Edit widget properties
        #
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.setAutoRaise(False)
        self.setArrowType(QtCore.Qt.DownArrow)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)

        # Evaluate arguments
        #
        numArgs = len(args)

        if numArgs == 0:

            pass

        elif numArgs == 1:

            # Inspect argument
            #
            arg = args[0]

            if isinstance(arg, string_types):

                self.setText(arg)

            else:

                raise TypeError('__init__() expects a str (%s given)!' % type(arg).__name__)

        elif numArgs == 2:

            # Inspect arguments
            #
            icon, text = args

            if isinstance(icon, QtGui.QIcon) and isinstance(text, string_types):

                self.setIcon(icon)
                self.setText(text)

            else:

                raise TypeError('__init__() expects an icon and str!')

        else:

            raise TypeError('__init__() expects 1 or 2 arguments (%s given)!' % numArgs)
    # endregion

    # region Methods
    def hasMenu(self):
        """
        Evaluates if this button already has a menu.

        :rtype: bool
        """

        return self.menu() is not None

    def setMenu(self, menu):
        """
        Associates the given menu with this tool button.
        The menu will be shown according to the button's popupMode.
        Ownership of the menu is not transferred to the tool button.

        :type menu: QtWidgets.QMenu
        :rtype: None
        """

        # Cleanup any former connections
        #
        if self.hasMenu():

            self.menu().aboutToShow.disconnect(self.aboutToShowMenu)

        # Call parent method
        #
        super(QDropDownButton, self).setMenu(menu)

        # Connect display signal to this button
        #
        menu.aboutToShow.connect(self.aboutToShowMenu)

    def initStyleOption(self, styleOption):
        """
        Initializes the supplied push button style option.

        :type styleOption: Union[QtWidgets.QStyleOptionToolButton, QtWidgets.QStyleOptionButton]
        :rtype: None
        """

        # Evaluate option type
        #
        if isinstance(styleOption, QtWidgets.QStyleOptionToolButton):

            # Call parent method
            #
            super(QDropDownButton, self).initStyleOption(styleOption)

        elif isinstance(styleOption, QtWidgets.QStyleOptionButton):

            # Edit button features
            #
            styleOption.rect = self.rect()
            styleOption.text = self.text()
            styleOption.icon = self.icon()
            styleOption.iconSize = self.iconSize()
            styleOption.features = QtWidgets.QStyleOptionButton.HasMenu

            # Edit enabled state
            #
            if not self.isEnabled():

                styleOption.state = QtWidgets.QStyle.State_None
                return

            # Edit focus state
            #
            styleOption.state = QtWidgets.QStyle.State_Active | QtWidgets.QStyle.State_Enabled

            if self.hasFocus():

                styleOption.state |= QtWidgets.QStyle.State_HasFocus

            # Edit mouse over state
            #
            mousePos = self.mapFromGlobal(QtGui.QCursor.pos())
            underMouse = styleOption.rect.contains(mousePos)

            if underMouse:

                styleOption.state |= QtWidgets.QStyle.State_MouseOver

            # Edit down state
            #
            if self.isDown() and underMouse:

                styleOption.state |= QtWidgets.QStyle.State_On

            else:

                styleOption.state |= QtWidgets.QStyle.State_Off

        else:

            raise TypeError('initStyleOption() expects a QStyleOptionToolButton (%s given)!' % type(styleOption).__name__)
    # endregion

    # region Events
    def paintEvent(self, event):
        """
        Event for whenever this widget needs to be re-painted.

        :type event: QtGui.QPaintEvent
        :rtype: None
        """

        # Initialize painter
        #
        painter = QtGui.QPainter(self)
        self.initPainter(painter)

        # Paint push button control
        #
        pushButtonStyleOption = QtWidgets.QStyleOptionButton()
        self.initStyleOption(pushButtonStyleOption)

        QtWidgets.QApplication.style().drawControl(QtWidgets.QStyle.CE_PushButton, pushButtonStyleOption, painter)
    # endregion

    # region Slots
    @QtCore.Slot()
    def aboutToShowMenu(self):
        """
        Slot method that updates the sender menu's minimum width before displaying.

        :rtype: None
        """

        self.sender().setMinimumWidth(self.width())
    # endregion
