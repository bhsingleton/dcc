# -*- coding: utf-8 -*-
from Qt import QtCore, QtWidgets, QtGui
from six import string_types
from dcc import fnqt

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
        self._menu = None
        self._qt = fnqt.FnQt()

        # Edit widget properties
        #
        self.setMouseTracking(True)
        self.customContextMenuRequested.connect(self.executeMenu)

        # Evaluate arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            # Inspect argument
            #
            arg = args[0]

            if isinstance(arg, string_types):

                self.setText(arg)

            elif isinstance(arg, QtWidgets.QWidget):

                self.setParent(arg)

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

            pass
    # endregion

    # region Properties
    @property
    def qt(self):
        """
        Getter method that returns the qt function set.

        :rtype: fnqt.FnQt
        """

        return self._qt
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

    def menu(self):
        """
        Returns the drop-down menu.

        :rtype: QtWidgets.QMenu
        """

        if isinstance(self._menu, QtWidgets.QMenu):

            return self._menu

        else:

            return self.findChildMenu()

    def setMenu(self, menu):
        """
        Updates the drop-down menu.

        :rtype: QtWidgets.QMenu
        """

        self._menu = menu

    def findChildMenu(self):
        """
        Returns the first menu derived from this widget's children.

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
        """
        Returns a size hint for this widget.

        :rtype: QtCore.QSize
        """

        fontMetric = self.fontMetrics()
        width = fontMetric.width(self.text())
        height = fontMetric.height()

        return QtCore.QSize(width, height)

    def hitButton(self, pos):
        """
        Returns true if pos is inside the clickable button rectangle; otherwise returns false.

        :type pos: QtCore.QPoint
        :rtype: bool
        """

        return self.pushButtonRect().contains(pos)

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
    # endregion

    # region Events
    def enterEvent(self, event):
        """
        Event for whenever the mouse enters this widget.

        :type event: QtGui.QMouseEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QDropDownButton, self).enterEvent(event)

        # Repaint widget
        #
        self.repaint()

    def leaveEvent(self, event):
        """
        Event for whenever the mouse leaves this widget.

        :type event: QtGui.QMouseEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QDropDownButton, self).leaveEvent(event)

        # Repaint widget
        #
        self.repaint()

    def mouseMoveEvent(self, event):
        """
        Event for whenever the mouse is moving over this widget.

        :type event: QtGui.QMouseEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QDropDownButton, self).mouseMoveEvent(event)

        # Repaint widget
        #
        self.repaint()

    def mouseReleaseEvent(self, event):
        """
        Event for whenever a mouse button has been released on this widget.

        :type event: QtGui.QMouseEvent
        :rtype: None
        """

        # Evaluate which button was released
        #
        dropDownMenuRect = self.dropDownMenuButtonRect()
        mouseButton = event.button()
        mousePos = event.pos()

        if dropDownMenuRect.contains(mousePos) and mouseButton == QtCore.Qt.LeftButton:

            self.customContextMenuRequested.emit(mousePos)

        # Call parent method
        #
        super(QDropDownButton, self).mouseReleaseEvent(event)

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

        style = self.qt.getApplication().style()

        # Paint push button control
        #
        pushButtonStyleOption = QtWidgets.QStyleOptionButton()
        self.initPushButtonStyleOption(pushButtonStyleOption)

        style.drawControl(QtWidgets.QStyle.CE_PushButton, pushButtonStyleOption, painter)

        # Paint drop-down menu control
        #
        dropDownMenuButtonStyleOption = QtWidgets.QStyleOptionButton()
        self.initDropDownMenuButtonStyleOption(dropDownMenuButtonStyleOption)

        style.drawControl(QtWidgets.QStyle.CE_PushButton, dropDownMenuButtonStyleOption, painter)
    # endregion

    # region Slots
    @QtCore.Slot()
    def executeMenu(self):
        """
        Custom context menu requested slot method responsible for executing the associated menu.

        :rtype: None
        """

        # Check if menu exists
        #
        menu = self.menu()

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
