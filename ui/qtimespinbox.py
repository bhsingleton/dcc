from PySide2 import QtCore, QtWidgets, QtGui
from enum import IntEnum
from dcc import fnscene

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class DefaultType(IntEnum):

    StartTime = 0
    EndTime = 1
    CurrentTime = 2


class QTimeSpinBox(QtWidgets.QSpinBox):
    """
    Overload of QSpinBox used to display time range values.
    """

    # region Dunderscores
    def __init__(self, parent=None):
        """
        Private method called after a new instance has been created.

        :type parent: QtWidgets.QWidget
        :rtype: None
        """

        # Call parent method
        #
        super(QTimeSpinBox, self).__init__(parent=parent)

        # Declare public variables
        #
        self._fnScene = fnscene.FnScene()
        self._defaultType = DefaultType.StartTime
    # endregion

    # region Properties
    @property
    def fnScene(self):
        """
        Getter method that returns the scene function set.

        :rtype: fnscene.FnScene
        """

        return self._fnScene
    # endregion

    # region Methods
    def defaultValue(self):
        """
        Returns the default value for this time box.

        :rtype: int
        """

        defaultType = self.defaultType()

        if defaultType == DefaultType.StartTime:

            return self.fnScene.getStartTime()

        elif defaultType == DefaultType.EndTime:

            return self.fnScene.getEndTime()

        elif defaultType == DefaultType.CurrentTime:

            return self.fnScene.getTime()

        else:

            raise TypeError('Unexpected default type!')

    def defaultType(self):
        """
        Returns the default type for time box.

        :rtype: DefaultType
        """

        return self._defaultType

    def setDefaultType(self, defaultType):
        """
        Updates the default type for this time box.

        :type defaultType: DefaultType
        :rtype: None
        """

        self._defaultType = defaultType

    def minimum(self):
        """
        Returns the minimum value.

        :rtype: int
        """

        return self.fnScene.getStartTime()

    def maximum(self):
        """
        Returns the maximum value.

        :rtype: int
        """

        return self.fnScene.getEndTime()

    def contextMenuEvent(self, event):
        """
        Event method used to extend the right click behavior on the spin box arrows.
        This overload will reset the value back to its minimum.

        :type event: QtGui.QContextMenuEvent
        :rtype: None
        """

        # Check which button was related
        #
        if event.reason() == QtGui.QContextMenuEvent.Mouse:

            # Initialize style options
            #
            options = QtWidgets.QStyleOptionSpinBox()
            options.initFrom(self)

            # Check if either arrows were clicked
            # If they were then ignore this event and reset the value
            #
            style = QtWidgets.QApplication.instance().style()

            upRect = style.subControlRect(QtWidgets.QStyle.CC_SpinBox, options, QtWidgets.QStyle.SC_SpinBoxUp, widget=self)
            downRect = style.subControlRect(QtWidgets.QStyle.CC_SpinBox, options, QtWidgets.QStyle.SC_SpinBoxDown, widget=self)
            mousePos = event.pos()

            if upRect.contains(mousePos) or downRect.contains(mousePos):

                self.setValue(self.defaultValue())
                event.accept()

            else:

                super(QTimeSpinBox, self).contextMenuEvent(event)

        else:

            super(QTimeSpinBox, self).contextMenuEvent(event)
    # endregion
