from PySide2 import QtCore, QtWidgets, QtGui

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QDropDownButton(QtWidgets.QAbstractButton):
    """
    Overload of QAbstractButton used as a push button with drop-down menu options.
    """

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :rtype: None
        """

        # Call parent method
        #
        parent = kwargs.get('parent', None)
        super(QDropDownButton, self).__init__(parent=parent)

        # Declare private variables
        #
        self._application = QtWidgets.QApplication.instance()  # type: QtWidgets.QApplication
        self._applicationFont = self._application.font()  # type: QtGui.QFont
        self._applicationStyle = self._application.style()  # type: QtWidgets.QStyle

        # Connect signal/slots
        #
        self.customContextMenuRequested.connect(self.executeCustomContextMenu)

        # Evaluate arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            self.setText(args[0])

        elif numArgs == 2:

            self.setIcon(args[0])
            self.setText(args[1])

        else:

            pass
    # endregion

    # region Methods
    def pushButtonRect(self):
        """
        Returns the bounding box for the push button component.

        :rtype: QtCore.QRect
        """

        return QtCore.QRect(0, 0, self.width() - 12, self.height())

    def dropDownMenuButtonRect(self):
        """
        Returns the bounding box for the drop-down menu button component.

        :rtype: QtCore.QRect
        """

        return QtCore.QRect(self.width() - 12, 0, 12, self.height())

    def customContextMenu(self):
        """
        Returns a context menu from this widget's children.
        A TypeError will be raised if multiple widgets are found!

        :rtype: QtWidgets.QMenu
        """

        menus = [x for x in self.children() if isinstance(x, QtWidgets.QMenu)]
        numMenus = len(menus)

        if numMenus == 0:

            return None

        elif numMenus == 1:

            return menus[0]

        else:

            raise TypeError('customContextMenu() multiple context menus found in children!')

    def sizeHint(self):

        fontMetric = QtGui.QFontMetrics(self._applicationFont)
        width = fontMetric.width(self.text())
        height = fontMetric.height()

        return QtCore.QSize(width, height)

    def hitButton(self, pos):
        """
        Returns true if pos is inside the clickable button rectangle; otherwise returns false.

        :type pos: QtCore.QPoint
        :rtype: bool
        """

        return True

    def initPushButtonStyleOption(self, styleOption):
        """
        Initializes the supplied push button style option.

        :type styleOption: QtWidgets.QStyleOptionButton
        :rtype: None
        """

        # Edit button features
        #
        styleOption.rect = self.pushButtonRect()
        styleOption.text = self.text()
        styleOption.icon = self.icon()
        styleOption.iconSize = self.iconSize()

        # Edit enabled state
        #
        if self.isEnabled():

            styleOption.state |= QtWidgets.QStyle.State_Enabled

        # Edit focus state
        #
        if self.hasFocus():

            styleOption.state |= QtWidgets.QStyle.State_HasFocus

        # Edit mouse over state
        #
        if self.underMouse():

            styleOption.state |= QtWidgets.QStyle.State_MouseOver

        # Edit down state
        #
        mousePos = self.mapFromGlobal(QtGui.QCursor.pos())
        underMouse = styleOption.rect.contains(mousePos)

        if self.isDown() and underMouse:

            styleOption.state |= QtWidgets.QStyle.State_On

        else:

            styleOption.state |= QtWidgets.QStyle.State_Off

        return styleOption

    def initDropDownMenuButtonStyleOption(self, styleOption):
        """
        Initializes the supplied drop-down menu button style option.

        :type styleOption: QtWidgets.QStyleOptionButton
        :rtype: None
        """

        # Edit button features
        #
        styleOption.rect = self.dropDownMenuButtonRect()
        styleOption.text = '▼'

        # Edit enabled state
        #
        if self.isEnabled():

            styleOption.state |= QtWidgets.QStyle.State_Enabled

        # Edit focus state
        #
        if self.hasFocus():

            styleOption.state |= QtWidgets.QStyle.State_HasFocus

        # Edit mouse over state
        #
        if self.underMouse():

            styleOption.state |= QtWidgets.QStyle.State_MouseOver

        # Edit down state
        #
        mousePos = self.mapFromGlobal(QtGui.QCursor.pos())
        underMouse = styleOption.rect.contains(mousePos)

        if self.isDown() and underMouse:

            styleOption.state |= QtWidgets.QStyle.State_On

        else:

            styleOption.state |= QtWidgets.QStyle.State_Off
    # endregion

    # region Events
    def mouseReleaseEvent(self, event):
        """
        Event for whenever a mouse button has been released on this widget.

        :type event: QtGui.QMouseEvent
        :rtype: None
        """

        # Take the event
        #
        event.accept()

        # Evaluate which button was released
        #
        pushButtonRect = self.pushButtonRect()
        dropDownMenuRect = self.dropDownMenuButtonRect()
        localPos = self.mapFromGlobal(event.globalPos())

        self.setDown(False)  # Don't forget to release the button!

        if pushButtonRect.contains(localPos):

            self.clicked.emit()

        elif dropDownMenuRect.contains(localPos):

            self.customContextMenuRequested.emit(localPos)

        else:

            pass

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
        self.initPushButtonStyleOption(pushButtonStyleOption)

        self._applicationStyle.drawControl(QtWidgets.QStyle.CE_PushButton, pushButtonStyleOption, painter)

        # Paint drop-down menu control
        #
        dropDownMenuButtonStyleOption = QtWidgets.QStyleOptionButton()
        self.initDropDownMenuButtonStyleOption(dropDownMenuButtonStyleOption)

        self._applicationStyle.drawControl(QtWidgets.QStyle.CE_PushButton, dropDownMenuButtonStyleOption, painter)
    # endregion

    # region Slots
    @QtCore.Slot()
    def executeCustomContextMenu(self):
        """
        Custom context menu requested slot method responsible for executing the associated menu.

        :rtype: None
        """

        # Check if menu exists
        #
        menu = self.customContextMenu()

        if menu is None:

            return

        # Synchronize width with button
        #
        menu.setMinimumWidth(self.width())

        # Execute context menu
        #
        localPos = self.rect().bottomLeft()
        globalPos = self.mapToGlobal(localPos)
        menu.exec_(globalPos)
    # endregion
