from Qt import QtCore, QtWidgets, QtGui

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QPersistentMenu(QtWidgets.QMenu):
    """
    Overload of `QMenu` that adds support for persistent menus.
    """

    # region Events
    def mouseReleaseEvent(self, event):
        """
        This event handler can be reimplemented in a subclass to receive mouse release events for the widget.

        :type event: QtGui.QMouseEvent
        :rtype: None
        """

        # Check if active action exists
        #
        action = self.activeAction()

        if action is None:

            return super(QPersistentMenu, self).mouseReleaseEvent(event)

        # Check if action is enabled
        #
        if action.isEnabled():

            action.setEnabled(False)
            super(QPersistentMenu, self).mouseReleaseEvent(event)
            action.setEnabled(True)
            action.trigger()

        else:

            return super(QPersistentMenu, self).mouseReleaseEvent(event)
    # endregion
