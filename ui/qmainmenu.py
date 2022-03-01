from PySide2 import QtCore, QtWidgets, QtGui

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QMainMenu(QtWidgets.QMenu):
    """
    Overload of QMenu used to affix a menu to a DCC's main menubar.
    """

    def __init__(self, title, **kwargs):
        """
        Private method called after a new instance is created.

        :type title: str
        :key parent: QtWidgets.QObject
        :rtype: None
        """

        # Call parent method
        #
        parent = kwargs.get('parent', None)
        super(QMainMenu, self).__init__(title, parent)

        # Modify menu properties
        #
        self.setObjectName(title.replace(' ', '_'))
        self.setSeparatorsCollapsible(False)
        self.setTearOffEnabled(kwargs.get('tearOff', True))
        self.setWindowTitle(title)

        # Install event filter onto parent
        #
        parent.installEventFilter(self)

    def eventFilter(self, source, event):
        """
        Intercepts events from registered objects.
        The return value determines if the event is blocked.

        :type source: QtWidgets.QObject
        :type event: QtCore.QEvent
        :rtype: bool
        """

        # Inspect source object
        # Ignore anything that isn't the menu bar
        #
        if not isinstance(source, QtWidgets.QMenuBar):

            return super(QMainMenu, self).eventFilter(source, event)

        # Inspect event type
        # At this time the QActionEvent class is missing the action method!
        #
        eventType = event.type()

        if eventType == QtCore.QEvent.ActionAdded:

            # Check if the help menu was added
            # If so then this means the user workspace was reset
            #
            menuBar = self.parentWidget()  # type: QtWidgets.QMenuBar
            actions = menuBar.actions()
            lastAction = actions[-1]

            if self.menuAction() not in actions and lastAction.text().endswith('Help'):

                log.info('Re-inserting menu: %s' % self.title())
                menuBar.insertMenu(lastAction, self)

        elif eventType == QtCore.QEvent.ActionRemoved:

            # Check if this menu has been removed
            #
            menuBar = self.parentWidget()  # type: QtWidgets.QMenuBar
            actions = menuBar.actions()

            if self.menuAction() not in actions:

                log.warning('Main menu has been removed: %s' % self.title())

        else:

            pass

        # Call parent method
        #
        return super(QMainMenu, self).eventFilter(source, event)

    def deleteLater(self, *args, **kwargs):
        """
        Marks this object for delete.
        Overloading this method to cleanup any references.

        :rtype: None
        """

        # Remove self from parent
        #
        parent = self.parentWidget()  # type: QtWidgets.QMenuBar
        parent.removeEventFilter(self)
        parent.removeAction(self.menuAction())

        # Cleanup references
        #
        self.setParent(None)
        del self.__instances__[self.title()]

        # Call parent method
        #
        return super(QMainMenu, self).deleteLater()
