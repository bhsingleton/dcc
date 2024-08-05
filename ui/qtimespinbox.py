from Qt import QtCore, QtWidgets, QtGui
from enum import IntEnum
from dcc import fnscene

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class DefaultType(IntEnum):
    """
    Enum class that contains all the valid reset types.
    """

    NONE = -1
    START_TIME = 0
    END_TIME = 1
    CURRENT_TIME = 2


class QTimeSpinBox(QtWidgets.QSpinBox):
    """
    Overload of QSpinBox used to display time range values.
    """

    # region Enums
    DefaultType = DefaultType
    # endregion

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
        super(QTimeSpinBox, self).__init__(parent=parent)

        # Declare public variables
        #
        self._scene = fnscene.FnScene()
        self._defaultType = kwargs.get('defaultType', DefaultType.NONE)
    # endregion

    # region Properties
    @property
    def scene(self):
        """
        Getter method that returns the scene function set.

        :rtype: fnscene.FnScene
        """

        return self._scene
    # endregion

    # region Methods
    def defaultValue(self):
        """
        Returns the default value for this time box.

        :rtype: int
        """

        defaultType = self.defaultType()

        if defaultType == DefaultType.NONE:

            return self.minimum()

        elif defaultType == DefaultType.START_TIME:

            return self.scene.getStartTime()

        elif defaultType == DefaultType.END_TIME:

            return self.scene.getEndTime()

        elif defaultType == DefaultType.CURRENT_TIME:

            return self.scene.getTime()

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

        self._defaultType = DefaultType(defaultType)

    def minimum(self):
        """
        Returns the minimum value.

        :rtype: int
        """

        return self.scene.getStartTime()

    def maximum(self):
        """
        Returns the maximum value.

        :rtype: int
        """

        return self.scene.getEndTime()
    # endregion

    # region Events
    def wheelEvent(self, event):
        """
        Event method used to extend the behavior of the scroll wheel on spin boxes.
        This overload will ignore any input!

        :type event: QtGui.QWheelEvent
        :rtype: None
        """

        event.ignore()

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

            # Check if either arrows were right-clicked
            # If they were then consume this event and reset the spinner value
            #
            upRect = QtWidgets.QApplication.style().subControlRect(QtWidgets.QStyle.CC_SpinBox, options, QtWidgets.QStyle.SC_SpinBoxUp, self)
            downRect = QtWidgets.QApplication.style().subControlRect(QtWidgets.QStyle.CC_SpinBox, options, QtWidgets.QStyle.SC_SpinBoxDown, self)
            mousePos = self.mapFromGlobal(QtGui.QCursor.pos())

            if upRect.contains(mousePos) or downRect.contains(mousePos):

                event.accept()
                self.setValue(self.defaultValue())

            else:

                super(QTimeSpinBox, self).contextMenuEvent(event)

        else:

            super(QTimeSpinBox, self).contextMenuEvent(event)
    # endregion

