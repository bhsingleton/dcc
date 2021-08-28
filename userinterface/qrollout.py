from PySide2 import QtCore, QtWidgets, QtGui

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


QWIDGETSIZE_MAX = (1 << 24) - 1  # https://code.qt.io/cgit/qt/qtbase.git/tree/src/widgets/kernel/qwidget.h#n873


class QRolloutViewport(QtWidgets.QWidget):
    """
    Overload of QWidget used to represent the viewport for a rollout widget.
    """

    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        """
        Private method called after a new instance has been created.
        By default this button will be expanded on initialize.

        :type parent: QtWidgets.QWidget
        :type f: int
        """

        # Call parent method
        #
        super(QRolloutViewport, self).__init__(parent=parent, f=f)

        # Modify widget properties
        #
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)

    def paintEvent(self, event):
        """
        The event for any paint requests made to this widget.

        :type event: QtGui.QPaintEvent
        :rtype: None
        """

        # Initialize painter
        #
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # Get brush from palette
        #
        brush = QtGui.QBrush(QtGui.QColor(73, 73, 73), style=QtCore.Qt.SolidPattern)
        rect = self.rect()

        # Paint background
        #
        path = QtGui.QPainterPath()
        path.addRoundedRect(rect, 4, 4)

        painter.setPen(QtCore.Qt.NoPen)
        painter.fillPath(path, brush)


class QRollout(QtWidgets.QWidget):
    """
    Overload of QWidget used to provide a collapsible viewport triggered by a button.
    This widget relies on toggling the visibility of the viewport widget to emulate Maya and Max's rollouts.
    Any tinkering with the underlying hierarchy will result in unpredictable behaviour!
    """

    expandedChanged = QtCore.Signal(bool)
    stateChanged = QtCore.Signal(bool)

    def __init__(self, title, parent=None, f=QtCore.Qt.WindowFlags()):
        """
        Private method called after a new instance has been created.

        :type parent: QtWidgets.QWidget
        :type f: int
        :rtype: None
        """

        # Call inherited method
        #
        super(QRollout, self).__init__(parent=parent, f=f)

        # Declare class variables
        #
        self._title = title
        self._expanded = True
        self._checked = False
        self._checkable = False
        self._checkBoxVisible = False
        self._gripperVisible = False

        self._viewport = QRolloutViewport(parent=self)
        self._viewport.installEventFilter(self)  # Overload eventFilter to take advantage of this!

        # Add widgets to layout
        #
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self._viewport)

        self.layout().setAlignment(QtCore.Qt.AlignTop)
        self.layout().setContentsMargins(0, 20, 0, 0)

        # Modify color palette
        #
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Button, QtGui.QColor(93, 93, 93))
        palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(81, 121, 148))

        self.setPalette(palette)

        # Modify widget properties
        #
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setMouseTracking(True)

        # Connect signal
        #
        self.expandedChanged.connect(self._viewport.setVisible)

    def viewport(self):
        """
        Returns the viewport widget for this rollout.
        By default this viewport is created with no rollout.
        It's up to the developer to add this themself.

        :rtype: QRolloutViewport
        """

        return self._viewport

    def title(self):
        """
        Returns the header title for this rollout.

        :rtype: str
        """

        return self._title

    def setTitle(self, title):
        """
        Updates the header title for this rollout.

        :rtype: str
        """

        self._title = title
        self.repaint()

    def checkable(self):
        """
        Returns the checkable state for this rollout.

        :rtype: bool
        """

        return self._checkable

    def setCheckable(self, checkable):
        """
        Updates the checkable state for this rollout.

        :type checkable: bool
        :rtype: None
        """

        self._checkable = checkable

    def checked(self):
        """
        Returns the checked state for this rollout.
        This rollout must be checkable for this value to have any significance.

        :rtype: bool
        """

        return self._checked

    def setChecked(self, checked):
        """
        Updates the checked state for this rollout.
        This method will emit the "stateChanged" signal if successful.

        :rtype: bool
        """

        # Update private value
        # Be sure to check for redundancy
        #
        if checked == self._checked or not self._checkable:

            return

        self._checked = checked

        # Redraw widget and emit signal
        #
        self.repaint()
        self.stateChanged.emit(self._checked)

    def showCheckBox(self):
        """
        Shows the check box for this rollout.
        This widget must be checkable for this to have any effect.

        :rtype: None
        """

        # Check if widget is checkable
        #
        if not self._checkable:

            return

        self._checkBoxVisible = True

    def hideCheckBox(self):
        """
        Hides the check box for this rollout.
        This widget must be checkable for this to have any effect.

        :rtype: None
        """

        # Check if widget is checkable
        #
        if not self._checkable:

            return

        self._checkBoxVisible = False

    def showGripper(self):
        """
        Show the gripper icon for this rollout.

        :rtype: None
        """

        self._gripperVisible = True

    def hideGripper(self):
        """
        Hides the gripper icon for this rollout.

        :rtype: None
        """

        self._gripperVisible = False

    def expanded(self):
        """
        Returns the expanded state for this rollout.

        :rtype: bool
        """

        return self._expanded

    def setExpanded(self, expanded):
        """
        Updates the expanded state for this rollout.
        This will in turn emit the "expandedChanged" signal with the new value.

        :type expanded: bool
        :rtype: None
        """

        # Update private value
        # Be sure to check for redundancy
        #
        if expanded == self._expanded:

            return

        self._expanded = expanded

        # Modify size properties
        #
        if self._expanded:

            self.setFixedSize(QtCore.QSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX))
            self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        else:

            self.setFixedSize(QtCore.QSize(QWIDGETSIZE_MAX, 20))
            self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        # Repaint widget and emit signal
        #
        self.repaint()
        self.expandedChanged.emit(self._expanded)

    def headerRect(self):
        """
        Returns the header bounding box.

        :rtype: QtCore.QRectF
        """

        return QtCore.QRectF(0, 0, self.rect().width(), 20)

    def titleRect(self):
        """
        Returns the title bounding box.

        :rtype: QtCore.QRectF
        """

        return QtCore.QRectF(20, 0, self.rect().width() - 40, 20)

    def expanderRect(self):
        """
        Returns the expander bounding box.

        :rtype: QtCore.QRectF
        """

        return QtCore.QRectF(0, 0, 20, 20)

    def gripperRect(self):
        """
        Returns the gripper bounding box.

        :rtype: QtCore.QRectF
        """

        return QtCore.QRectF(self.rect().width() - 20, 0, 20, 20)

    def expander(self):
        """
        Returns the polygonal shape for the expander icon.

        :rtype: QtGui.QPolygon
        """

        # Shrink bounding box
        #
        rect = self.expanderRect()
        rect.adjust(7, 7, -7, -7)

        # Check if expanded
        # This will determine the orientation of the arrow
        #
        polygon = QtGui.QPolygon()

        if self._expanded:

            polygon.append(QtCore.QPoint(rect.left(), rect.top()))
            polygon.append(QtCore.QPoint(rect.right(), rect.top()))
            polygon.append(QtCore.QPoint(rect.center().x(), rect.bottom()))

        else:

            polygon.append(QtCore.QPoint(rect.left(), rect.top()))
            polygon.append(QtCore.QPoint(rect.right(), rect.center().y()))
            polygon.append(QtCore.QPoint(rect.left(), rect.bottom()))

        return polygon

    def gripper(self):
        """
        Returns the points that make up the gripper.

        :rtype: list
        """

        # Shrink bounding box
        #
        rect = self.gripperRect()
        rect.adjust(7, 7, -7, -7)

        return (
            QtCore.QPointF(rect.left(), rect.top()),
            QtCore.QPointF(rect.center().x(), rect.top()),
            QtCore.QPointF(rect.right(), rect.top()),
            QtCore.QPointF(rect.left(), rect.center().y()),
            QtCore.QPointF(rect.center().x(), rect.center().y()),
            QtCore.QPointF(rect.right(), rect.center().y()),
            QtCore.QPointF(rect.left(), rect.bottom()),
            QtCore.QPointF(rect.center().x(), rect.bottom()),
            QtCore.QPointF(rect.right(), rect.bottom()),
        )

    def enterEvent(self, event):
        """
        The event for whenever the mouse enters this widget.
        To get mouse highlighting we need to force a repaint operation here.

        :type event: QtGui.QEvent
        :rtype: None
        """

        # Force re-paint
        #
        self.repaint()

        # Call inherited method
        #
        super(QRollout, self).enterEvent(event)

    def leaveEvent(self, event):
        """
        The event for whenever the mouse leaves this widget.
        To get mouse highlighting we need to force a repaint operation here.

        :type event: QtGui.QEvent
        :rtype: None
        """

        # Force re-paint
        #
        self.repaint()

        # Call inherited method
        #
        super(QRollout, self).leaveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        The event for whenever the mouse button has been released from this widget.

        :type event: QtGui.QMouseReleaseEvent
        :rtype: None
        """

        # Check if expander was pressed
        #
        if self.expanderRect().contains(event.pos()):

            self.toggleExpanded()

        elif self.titleRect().contains(event.pos()):

            self.toggleChecked()

        else:

            pass

        # Call inherited method
        #
        super(QRollout, self).mouseReleaseEvent(event)

    def paintEvent(self, event):
        """
        The event for any paint requests made to this widget.

        :type event: QtGui.QPaintEvent
        :rtype: None
        """

        # Initialize painter
        #
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # Get brush from palette
        #
        palette = self.palette()
        pen = QtGui.QPen(palette.highlightedText(), 1) if self.underMouse() else QtGui.QPen(palette.text(), 1)

        # Paint background
        #
        path = QtGui.QPainterPath()
        path.addRoundedRect(self.headerRect(), 4, 4)

        painter.setPen(QtCore.Qt.NoPen)
        painter.fillPath(path, palette.highlight() if self.checked() else palette.button())

        # Paint title
        #
        titleRect = self.titleRect()

        if self._checkable and self._checkBoxVisible:

            # Define check box options
            #
            options = QtWidgets.QStyleOptionButton()
            options.state |= QtWidgets.QStyle.State_On if self._checked else QtWidgets.QStyle.State_Off
            options.state |= QtWidgets.QStyle.State_Enabled
            options.text = self._title
            options.rect = QtCore.QRect(titleRect.x(), titleRect.y(), titleRect.width(), titleRect.height())

            # Draw check box control
            #
            style = QtWidgets.QApplication.style()
            style.drawControl(QtWidgets.QStyle.CE_CheckBox, options, painter)

        else:

            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawText(titleRect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, self._title, boundingRect=titleRect)

        # Paint expander
        #
        path = QtGui.QPainterPath()
        path.addPolygon(self.expander())

        painter.setPen(QtCore.Qt.NoPen)
        painter.fillPath(path, palette.highlightedText() if self.underMouse() else palette.text())

        # Paint mover
        #
        if self._gripperVisible:

            points = self.gripper()

            painter.setPen(pen)
            painter.drawPoints(points)

    def toggleExpanded(self):
        """
        Toggles the expanded state of this rollout.

        :rtype: None
        """

        self.setExpanded(not self._expanded)

    def toggleChecked(self):
        """
        The event for whenever the header button is checked.
        If checkable is not enabled then the status will not be inversed.

        :rtype: None
        """

        # Check if widget is checkable
        #
        if not self._checkable:

            return

        self.setChecked(not self._checked)
