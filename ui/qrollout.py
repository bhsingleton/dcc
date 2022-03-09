from PySide2 import QtCore, QtWidgets, QtGui
from six import string_types
from dcc.ui import qdivider, qseparator

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


QWIDGETSIZE_MAX = (1 << 24) - 1  # https://code.qt.io/cgit/qt/qtbase.git/tree/src/widgets/kernel/qwidget.h#n873


class QRollout(QtWidgets.QAbstractButton):
    """
    Overload of QWidget used to provide a collapsible viewport triggered by a button.
    This widget relies on toggling the visibility of the viewport widget to emulate Maya and Max's rollouts.
    Any tinkering with the underlying hierarchy will result in unpredictable behaviour!
    """

    expandedChanged = QtCore.Signal(bool)

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
        super(QRollout, self).__init__(parent=parent)

        # Declare private variables
        #
        self._thickness = 24
        self._alignment = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        self._flat = False
        self._expanded = True
        self._grippable = False

        self._dragging = False
        self._divider = None
        self._dividers = None
        self._insertAt = 0

        self._menu = QtWidgets.QMenu('', parent=self)
        self.initMenu(self._menu)

        # Edit widget properties
        #
        self.setContentsMargins(0, self._thickness, 0, 0)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.executeMenu)

        # Evaluate arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            # Inspect argument type
            #
            arg = args[0]

            if isinstance(arg, string_types):

                self.setTitle(arg)

            elif isinstance(arg, QtWidgets.QWidget):

                self.setParent(arg)

            else:

                raise TypeError('__init__() expects a str (%s given)!' % type(arg).__name__)

        elif numArgs == 2:

            # Inspect argument types
            #
            title = args[0]
            parent = args[1]

            if isinstance(title, string_types) and isinstance(parent, QtWidgets.QWidget):

                self.setTitle(title)
                self.setParent(parent)

            else:

                raise TypeError('__init__() expects a str and QWidget!')

        else:

            pass
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
        layout.setObjectName('centralLayout')
        layout.setAlignment(QtCore.Qt.AlignTop)
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

        :rtype: List[QRollout]
        """

        return list(self.iterSiblingWidgets())

    def title(self):
        """
        Returns the title of this rollout.
        This method is synonymous with ".text" for QGroupBox compatibility.

        :rtype: str
        """

        return self.text()

    def setTitle(self, title):
        """
        Updates the title of this rollout.
        This method is synonymous with ".setText" for QGroupBox compatibility.

        :type title: str
        :rtype: None
        """

        self.setText(title)

    def alignment(self):
        """
        Returns the alignment for the title text.

        :rtype: int
        """

        return self._alignment

    def setAlignment(self, alignment):
        """
        Updates the alignment for the title text.

        :type alignment: int
        :rtype: None
        """

        self._alignment = alignment
        self.repaint()

    def flat(self):
        """
        Returns the flat state for this widget.

        :rtype: bool
        """

        return self._flat

    def setFlat(self, flat):
        """
        Updates the flat state for this widget.

        :type flat: bool
        :rtype: None
        """

        self._flat = flat

    def thickness(self):
        """
        Returns the thickness of the rollout button.

        :rtype: int
        """

        return self._thickness

    def setThickness(self, thickness):
        """
        Updates the thickness of the rollout button.

        :type thickness: int
        :rtype: None
        """

        self._thickness = thickness
        self.repaint()

    def sizeHint(self):
        """
        Returns the recommended size for this rollout.

        :rtype: QtCore.QSize
        """

        return QtCore.QSize(self.fontMetrics().width(self.text()), self.thickness())

    def isGrippable(self):
        """
        Returns the grippable state for this rollout.

        :rtype: bool
        """

        return self._grippable

    def setGrippable(self, grippable):
        """
        Updates the grippable state for this rollout.

        :rtype: None
        """

        self._grippable = grippable
        self.repaint()

    def showGripper(self):
        """
        Shows the gripper icon for this rollout.

        :rtype: None
        """

        self.setGrippable(True)

    def hideGripper(self):
        """
        Hides the gripper icon for this rollout.

        :rtype: None
        """

        self.setGrippable(False)

    def isExpanded(self):
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

            self.setFixedSize(QtCore.QSize(QWIDGETSIZE_MAX, self.thickness()))
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

    def toggleChecked(self):
        """
        Toggles the check state on this rollout.

        :rtype: None
        """

        self.setChecked(not self.isChecked())

    def menu(self):
        """
        Returns the menu for this rollout.

        :rtype: QtWidgets.QMenu
        """

        return self._menu

    def initMenu(self, menu):
        """
        Initializes the supplied menu for use with this rollout.

        :type menu: QtWidgets.QMenu
        :rtype: None
        """

        expandAction = QtWidgets.QAction('&Expand', parent=menu)
        expandAction.setObjectName('expandAction')
        expandAction.triggered.connect(self.on_expandAction_triggered)

        collapseAction = QtWidgets.QAction('&Collapse', parent=menu)
        collapseAction.setObjectName('collapseAction')
        collapseAction.triggered.connect(self.on_collapseAction_triggered)

        expandAllAction = QtWidgets.QAction('&Expand All', parent=menu)
        expandAllAction.setObjectName('expandAllAction')
        expandAllAction.triggered.connect(self.on_expandAllAction_triggered)

        collapseAllAction = QtWidgets.QAction('&Collapse All', parent=menu)
        collapseAllAction.setObjectName('collapseAllAction')
        collapseAllAction.triggered.connect(self.on_collapseAllAction_triggered)

        menu.setObjectName('customContextMenu')
        menu.addActions(
            [
                expandAction,
                collapseAction,
                qseparator.QSeparator('', parent=menu),
                expandAllAction,
                collapseAllAction
            ]
        )

    def hitButton(self, pos):
        """
        Evaluates if the supplied point counts as a button click.

        :type pos: QtCore.QPoint
        :rtype: bool
        """

        return self.titleRect().contains(pos)

    def underMouse(self, headerOnly=False):
        """
        Evaluates if this widget is under the mouse.

        :type headerOnly: bool
        :rtype: bool
        """

        if headerOnly:

            return self.headerRect().contains(self.mapFromGlobal(QtGui.QCursor().pos()))

        else:

            return super(QRollout, self).underMouse()

    def headerRect(self):
        """
        Returns the header bounding box.

        :rtype: QtCore.QRectF
        """

        return QtCore.QRectF(0.0, 0.0, self.rect().width(), self._thickness)

    def titleRect(self):
        """
        Returns the title bounding box.

        :rtype: QtCore.QRectF
        """

        return QtCore.QRectF(
            QtCore.QPointF(self._thickness, 0.0),
            QtCore.QPointF(self.rect().right() - self._thickness, self._thickness)
        )

    def viewportRect(self):
        """
        Returns the viewport bounding box.

        :rtype: QtCore.QRectF
        """

        return QtCore.QRectF(0.0, self._thickness, self.rect().width(), self.rect().height() - self._thickness)

    def expanderRect(self):
        """
        Returns the expander bounding box.

        :rtype: QtCore.QRectF
        """

        return QtCore.QRectF(0, 0, self._thickness, self._thickness)

    def gripperRect(self):
        """
        Returns the gripper bounding box.

        :rtype: QtCore.QRectF
        """

        return QtCore.QRectF(self.rect().width() - self._thickness, 0, self._thickness, self._thickness)

    def expanderPolygon(self):
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

    def gripperPoints(self):
        """
        Returns the points that make up the gripper.

        :rtype: List[QtCore.QPointF]
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

    def isDragging(self):
        """
        Evaluates if the rollout is currently being dragged.

        :rtype: bool
        """

        return self._dragging

    def beginDragging(self):
        """
        Initializes all the internal components required for dragging.

        :rtype: None
        """

        self._dragging = True
        self._dividers = self.dividers()

        self._divider = qdivider.QDivider(QtCore.Qt.Horizontal)
        self._divider.setStyleSheet('background-color: darkCyan; border: 4px solid darkCyan;')

        self.setCursor(QtGui.QCursor(QtCore.Qt.ClosedHandCursor))

    def endDragging(self):
        """
        Cleans up all the internal components used for dragging.

        :rtype: None
        """

        self._dragging = False
        self._divider.deleteLater()

        self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def dividers(self):
        """
        Returns all the divider bounding box considerations for dragging.

        :rtype: List[QtCore.QRect]
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

    def initPainter(self, painter):
        """
        Initializes the supplied painter for this rollout.

        :type painter: QtGui.QPainter
        :rtype: None
        """

        # Call parent method
        #
        super(QRollout, self).initPainter(painter)

        # Enable anti-aliasing
        #
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

    def initCheckBoxStyleOption(self, styleOption):
        """
        Initializes the supplied check-box style options.

        :type styleOption: QtWidgets.QStyleOptionButton
        :rtype: None
        """

        # Check if rollout is checkable
        #
        styleOption.text = self.title()
        styleOption.rect = self.titleRect().toAlignedRect()

        if self.isCheckable():

            styleOption.state = QtWidgets.QStyle.State_Enabled

        else:

            styleOption.state = QtWidgets.QStyle.State_None
            return

        # Edit checked state
        #
        if self.isChecked():

            styleOption.state |= QtWidgets.QStyle.State_On

        else:

            styleOption.state |= QtWidgets.QStyle.State_Off

        # Edit mouse over state
        #
        if self.underMouse(headerOnly=True):

            styleOption.state |= QtWidgets.QStyle.State_MouseOver
    # endregion

    # region Events
    def eventFilter(self, watched, event):
        """
        Filters events if this object has been installed as an event filter for the watched object.

        :type watched: QtCore.QObject
        :type event: QtCore: QEvent
        :rtype: bool
        """

        # Check if layout triggered event
        #
        if watched is self.layout() and isinstance(event, QtCore.QChildEvent):

            # Check if child object is a widget
            #
            child = event.child()

            if not isinstance(child, QtWidgets.QWidget):

                return super(QRollout, self).eventFilter(watched, event)

            # Connect signal to child
            #
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
        return super(QRollout, self).eventFilter(watched, event)

    def enterEvent(self, event):
        """
        Event for whenever the mouse enters this widget.

        :type event: QtGui.QMouseEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QRollout, self).enterEvent(event)

        # Force re-paint
        #
        self.repaint()

    def leaveEvent(self, event):
        """
        Event for whenever the mouse leaves this widget.

        :type event: QtGui.QMouseEvent
        :rtype: None
        """

        # Force re-paint
        #
        self.repaint()

        # Call parent method
        #
        super(QRollout, self).leaveEvent(event)

    def mousePressEvent(self, event):
        """
        The event for when a mouse button has been pressed on this widget

        :type event: QtGui.QMouseEvent
        :rtype: None
        """

        # Check if the gripper was pressed
        #
        mousePos = event.pos()
        mouseButton = event.button()

        if self.gripperRect().contains(mousePos) and mouseButton == QtCore.Qt.LeftButton and self.isGrippable():

            self.beginDragging()

        # Call parent method
        #
        super(QRollout, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Event for whenever the mouse is moving over this widget.

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

        else:

            self.repaint()

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
            mousePos = event.pos()
            mouseButton = event.button()

            if self.expanderRect().contains(mousePos) and mouseButton == QtCore.Qt.LeftButton:

                self.toggleExpanded()

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
        self.initPainter(painter)

        # Get brush from palette
        #
        palette = self.palette()
        pen = QtGui.QPen(palette.highlightedText(), 1) if self.underMouse(headerOnly=True) else QtGui.QPen(palette.text(), 1)

        # Paint background
        #
        path = QtGui.QPainterPath()
        path.addRoundedRect(self.headerRect(), 4, 4)

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.fillPath(path, palette.highlight() if self.isChecked() else palette.button())

        # Paint title
        #
        titleRect = self.titleRect()

        if self.isCheckable():

            options = QtWidgets.QStyleOptionButton()
            self.initCheckBoxStyleOption(options)

            style = QtWidgets.QApplication.instance().style()
            style.drawControl(QtWidgets.QStyle.CE_CheckBox, options, painter)

        else:

            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawText(titleRect, self.alignment(), self.text(), boundingRect=titleRect)

        # Paint expander
        #
        path = QtGui.QPainterPath()
        path.addPolygon(self.expanderPolygon())

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.fillPath(path, palette.highlightedText() if self.underMouse(headerOnly=True) else palette.text())

        # Paint mover if grippable
        #
        if self.isGrippable():

            points = self.gripperPoints()

            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawPoints(points)

        # Paint viewport if expanded
        #
        if self.isExpanded():

            path = QtGui.QPainterPath()
            path.addRoundedRect(self.viewportRect(), 4, 4)

            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.fillPath(path, QtGui.QBrush(QtGui.QColor(73, 73, 73), style=QtCore.Qt.SolidPattern))
    # endregion

    # region Slots
    @QtCore.Slot(QtCore.QPointF)
    def executeMenu(self, pos):
        """
        Displays the custom context menu at the specified position.

        :type pos: QtCore.QPointF
        :rtype: None
        """

        if self.gripperRect().contains(pos):

            self.menu().exec_(self.mapToGlobal(pos))

    @QtCore.Slot(bool)
    def on_expandAction_triggered(self, checked=False):
        """
        Triggered slot method responsible for expanding this rollout.

        :type checked: bool
        :rtype: None
        """

        self.setExpanded(True)

    @QtCore.Slot(bool)
    def on_expandAllAction_triggered(self, checked=False):
        """
        Triggered slot method responsible for expanding all sibling rollouts.

        :type checked: bool
        :rtype: None
        """

        self.setExpanded(True)

        for rollout in self.iterSiblingWidgets():

            rollout.setExpanded(True)

    @QtCore.Slot(bool)
    def on_collapseAction_triggered(self, checked=False):
        """
        Triggered slot method responsible for collapsing this rollout.

        :type checked: bool
        :rtype: None
        """

        self.setExpanded(False)

    @QtCore.Slot(bool)
    def on_collapseAllAction_triggered(self, checked=False):
        """
        Triggered slot method responsible for collapsing all sibling rollouts.

        :type checked: bool
        :rtype: None
        """

        self.setExpanded(False)

        for rollout in self.iterSiblingWidgets():

            rollout.setExpanded(False)
    # endregion
