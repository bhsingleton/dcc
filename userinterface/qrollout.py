from PySide2 import QtCore, QtWidgets, QtGui
from dcc.userinterface import qdivider, qseparator

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


QWIDGETSIZE_MAX = (1 << 24) - 1  # https://code.qt.io/cgit/qt/qtbase.git/tree/src/widgets/kernel/qwidget.h#n873


class QRollout(QtWidgets.QWidget):
    """
    Overload of QWidget used to provide a collapsible viewport triggered by a button.
    This widget relies on toggling the visibility of the viewport widget to emulate Maya and Max's rollouts.
    Any tinkering with the underlying hierarchy will result in unpredictable behaviour!
    """

    expandedChanged = QtCore.Signal(bool)
    stateChanged = QtCore.Signal(bool)

    # region Dunderscores
    __thickness__ = 20.0  # Global thickness for the rollout bar

    def __init__(self, title, parent=None, f=QtCore.Qt.WindowFlags()):
        """
        Private method called after a new instance has been created.

        :type parent: QtWidgets.QWidget
        :type f: int
        :rtype: None
        """

        # Call parent method
        #
        super(QRollout, self).__init__(parent=parent, f=f)

        # Declare class variables
        #
        self._title = title
        self._dragging = False
        self._divider = None
        self._dividers = None
        self._insertAt = 0
        self._expanded = True
        self._checked = False
        self._checkable = False
        self._checkBoxVisible = False
        self._grippable = False

        # Modify widget properties
        #
        self.setContentsMargins(0, self.__thickness__, 0, 0)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

        # Modify color palette
        #
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Button, QtGui.QColor(93, 93, 93))
        palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(81, 121, 148))

        self.setPalette(palette)

        # Assign default vertical layout
        #
        layout = QtWidgets.QVBoxLayout()
        layout.setObjectName('MainLayout')
        layout.setAlignment(QtCore.Qt.AlignTop)

        self.setLayout(layout)

        # Assign custom context menu
        #
        self.customContextMenu = QtWidgets.QMenu('', parent=self)
        self.customContextMenu.setObjectName('CustomContextMenu')

        self.expandAction = QtWidgets.QAction('Expand', parent=self.customContextMenu)
        self.expandAction.setObjectName('ExpandAction')
        self.expandAction.setMenu(self.customContextMenu)
        self.expandAction.triggered.connect(self.expandAction_triggered)

        self.collapseAction = QtWidgets.QAction('Collapse', parent=self.customContextMenu)
        self.collapseAction.setObjectName('CollapseAction')
        self.collapseAction.setMenu(self.customContextMenu)
        self.collapseAction.triggered.connect(self.collapseAction_triggered)

        self.expandAllAction = QtWidgets.QAction('Expand All', parent=self.customContextMenu)
        self.expandAllAction.setObjectName('ExpandAllAction')
        self.expandAllAction.setMenu(self.customContextMenu)
        self.expandAllAction.triggered.connect(self.expandAllAction_triggered)

        self.collapseAllAction = QtWidgets.QAction('Collapse All', parent=self.customContextMenu)
        self.collapseAllAction.setObjectName('CollapseAllAction')
        self.collapseAllAction.setMenu(self.customContextMenu)
        self.collapseAllAction.triggered.connect(self.collapseAllAction_triggered)

        self.customContextMenu.addActions(
            [
                self.expandAction,
                self.collapseAction,
                qseparator.QSeparator('', parent=self.customContextMenu),
                self.expandAllAction,
                self.collapseAllAction
            ]
        )
    # endregion

    # region Methods
    def setLayout(self, layout):
        """
        Updates the layout manager for this widget to layout.

        :type layout: QtWidgets.QLayout
        :rtype: None
        """

        # Check if event filter should be removed from current layout
        #
        currentLayout = self.layout()

        if currentLayout is not None:

            currentLayout.removeEventFilter(self)

        # Install new event filter
        #
        layout.installEventFilter(self)

        # Call parent method
        #
        super(QRollout, self).setLayout(layout)

    def parentLayout(self):
        """
        Returns the layout this widget is parented to.

        :rtype: QtWidgets.QLayout
        """

        return self.parentWidget().layout()

    def iterSiblingWidgets(self):
        """
        Returns a generator that yields sibling rollouts.

        :rtype: iter
        """

        # Check if parent layout exists
        #
        parentLayout = self.parentLayout()

        if parentLayout is None:

            return

        # Iterate through widgets
        #
        layoutCount = parentLayout.count()

        for i in range(layoutCount):

            widget = parentLayout.itemAt(i).widget()

            if isinstance(widget, QRollout) and widget is not self:

                yield widget

            else:

                continue

    def siblingWidgets(self):
        """
        Returns a list of sibling rollouts.

        :rtype: list[QRollout]
        """

        return list(self.iterSiblingWidgets())

    def showContextMenu(self, pos):
        """
        Displays the custom context menu at the specified position.

        :type pos: QtCore.QPointF
        :rtype: None
        """

        if self.gripperRect().contains(pos):

            self.customContextMenu.exec_(self.mapToGlobal(pos))

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

    def isChecked(self):
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

        self._grippable = True

    def hideGripper(self):
        """
        Hides the gripper icon for this rollout.

        :rtype: None
        """

        self._grippable = False

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

        # Check for redundancy
        #
        if expanded == self._expanded:

            return

        # Update private value and modify sizes
        #
        self._expanded = expanded

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

    def toggleExpanded(self):
        """
        Toggles the expanded state of this rollout.

        :rtype: None
        """

        self.setExpanded(not self._expanded)

    def headerRect(self):
        """
        Returns the header bounding box.

        :rtype: QtCore.QRectF
        """

        return QtCore.QRectF(0.0, 0.0, self.rect().width(), self.__thickness__)

    def titleRect(self):
        """
        Returns the title bounding box.

        :rtype: QtCore.QRectF
        """

        return QtCore.QRectF(self.__thickness__, 0.0, self.rect().width() - (self.__thickness__ * 2.0), self.__thickness__)

    def viewportRect(self):
        """
        Returns the viewport bounding box.

        :rtype: QtCore.QRectF
        """

        return QtCore.QRectF(0.0, self.__thickness__, self.rect().width(), self.rect().height() - self.__thickness__)

    def expanderRect(self):
        """
        Returns the expander bounding box.

        :rtype: QtCore.QRectF
        """

        return QtCore.QRectF(0, 0, self.__thickness__, self.__thickness__)

    def gripperRect(self):
        """
        Returns the gripper bounding box.

        :rtype: QtCore.QRectF
        """

        return QtCore.QRectF(self.rect().width() - self.__thickness__, 0, self.__thickness__, self.__thickness__)

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

    def isDragging(self):
        """
        Evaluates if the rollout is currently being dragged.

        :rtype: bool
        """

        return self._dragging

    def beginDragging(self):
        """
        Setups all of the internal components required for dragging.

        :rtype: None
        """

        self._dragging = True
        self._dividers = self.dividers()

        self._divider = qdivider.QDivider(QtCore.Qt.Horizontal)
        self._divider.setStyleSheet('background-color: darkCyan; border: 4px solid darkCyan;')

        self.setCursor(QtGui.QCursor(QtCore.Qt.ClosedHandCursor))

    def endDragging(self):
        """
        Cleans up all of the internal components used for dragging.

        :rtype: None
        """

        self._dragging = False
        self._divider.deleteLater()

        self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def gripper(self):
        """
        Returns the points that make up the gripper.

        :rtype: list[QtCore.QPointF]
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

    def dividers(self):
        """
        Returns all of the divider bounding box consideration for dragging.

        :rtype: list[QtCore.QRect]
        """

        parentLayout = self.parentLayout()

        layoutCount = parentLayout.count()
        rects = [parentLayout.itemAt(x).geometry() for x in range(layoutCount)]

        dividers = [None] * layoutCount

        for (i, rect) in enumerate(rects):

            if i == 0:

                dividers[i] = QtCore.QRect(QtCore.QPoint(rect.left(), rect.top()), QtCore.QPoint(rect.right(), rect.center().y()))

            else:

                dividers[i] = QtCore.QRect(QtCore.QPoint(rects[i-1].left(), rects[i-1].center().y()), QtCore.QPoint(rect.right(), rect.center().y()))

        return dividers
    # endregion

    # region Events
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

        # Call parent method
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

        # Call parent method
        #
        super(QRollout, self).leaveEvent(event)

    def eventFilter(self, watched, event):
        """
        Filters events if this object has been installed as an event filter for the watched object.

        :type watched: QtCore.QObject
        :type event: QtCore: QEvent
        :rtype: bool
        """

        # Check if a widget was added to the layout manager
        #
        if watched is self.layout() and isinstance(event, QtCore.QChildEvent):

            child = event.child()

            if event.added():

                log.info('Adding child: %s' % child)
                self.expandedChanged.connect(child.setVisible)

            elif event.removed():

                log.debug('Removing child: %s' % child)
                self.expandedChanged.disconnect(child.setVisible)

            else:

                pass

        # Call parent method
        #
        super(QRollout, self).eventFilter(watched, event)

    def mousePressEvent(self, event):
        """
        The event for when a mouse button has been pressed on this widget

        :type event: QtGui.QMouseEvent
        :rtype: None
        """

        # Check if the gripper was pressed
        #
        if self.gripperRect().contains(event.pos()) and event.button() == QtCore.Qt.LeftButton and self._grippable:

            self.beginDragging()

        # Call parent method
        #
        super(QRollout, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        The event for when the mouse is moving over this widget.

        :type event: QtGui.QMouseEvent
        :rtype: None
        """

        # Check if widget is being dragged
        #
        parentWidget = self.parentWidget()
        parentLayout = parentWidget.layout()

        if self.isDragging() and parentLayout is not None:

            pos = parentWidget.mapFromGlobal(event.globalPos())
            collisions = [x.contains(pos) for x in self._dividers]
            insertAt = collisions.index(True) if any(collisions) else self._insertAt

            if insertAt != self._insertAt:

                self._insertAt = insertAt
                parentLayout.removeWidget(self._divider)
                parentLayout.insertWidget(self._insertAt, self._divider)

        # Call parent method
        #
        super(QRollout, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        The event for when a mouse button has been released on this widget.

        :type event: QtGui.QMouseEvent
        :rtype: None
        """

        # Check if widget was being dragged
        #
        if self.isDragging():

            self.endDragging()

            parentLayout = self.parentLayout()
            parentLayout.removeWidget(self)
            parentLayout.insertWidget(self._insertAt, self)

        else:

            # Check if expander was pressed
            #
            if self.expanderRect().contains(event.pos()) and event.button() == QtCore.Qt.LeftButton:

                self.toggleExpanded()

            elif self.titleRect().contains(event.pos()) and event.button() == QtCore.Qt.LeftButton:

                self.toggleChecked()

            else:

                pass

        # Call parent method
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
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.fillPath(path, palette.highlight() if self._checked else palette.button())

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

        # Paint mover if grippable
        #
        if self._grippable:

            points = self.gripper()

            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawPoints(points)

        # Paint viewport if expanded
        #
        if self._expanded:

            brush = QtGui.QBrush(QtGui.QColor(73, 73, 73), style=QtCore.Qt.SolidPattern)

            path = QtGui.QPainterPath()
            path.addRoundedRect(self.viewportRect(), 4, 4)

            painter.setPen(QtCore.Qt.NoPen)
            painter.fillPath(path, brush)
    # endregion

    # region Slots
    def expandAction_triggered(self, checked=False):
        """
        Triggered slot method responsible for expanding this rollout.

        :type checked: bool
        :rtype: None
        """

        self.setExpanded(True)

    def expandAllAction_triggered(self, checked=False):
        """
        Triggered slot method responsible for expanding all sibling rollouts.

        :type checked: bool
        :rtype: None
        """

        self.setExpanded(True)

        for rollout in self.iterSiblingWidgets():

            rollout.setExpanded(True)

    def collapseAction_triggered(self, checked=False):
        """
        Triggered slot method responsible for collapsing this rollout.

        :type checked: bool
        :rtype: None
        """

        self.setExpanded(False)

    def collapseAllAction_triggered(self, checked=False):
        """
        Triggered slot method responsible for collapsing all sibling rollouts.

        :type checked: bool
        :rtype: None
        """

        self.setExpanded(False)

        for rollout in self.iterSiblingWidgets():

            rollout.setExpanded(False)
    # endregion
