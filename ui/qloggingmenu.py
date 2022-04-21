from Qt import QtWidgets
from .qmainmenu import QMainMenu
from .qseparator import QSeparator

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


LOG_LEVELS = list(range(0, logging.CRITICAL + 1, 10))
LEVEL_NAMES = [logging.getLevelName(n) for n in range(0, logging.CRITICAL + 1, 10)]


class QLoggingMenu(QMainMenu):
    """
    Overload of QMainMenu used to create a logging interface for modifying logger levels.
    """

    def __init__(self, name, parent=None):
        """
        Private method called after a new instance is created.

        :type name: str
        :type parent: QtWidgets.QObject
        :rtype: None
        """

        # Call parent method
        #
        super(QLoggingMenu, self).__init__(name, parent=parent)

        # Modify menu properties
        #
        self.setSeparatorsCollapsible(False)
        self.setTearOffEnabled(True)
        self.setWindowTitle('Logging Control')
        self.aboutToShow.connect(self.syncLevel)

        # Declare public variables
        #
        self.actionGroups = {}

        # Refresh menu actions
        #
        self.refresh()

    def createLevelActionGroup(self, name, parent=None):
        """
        Returns a action group for switching logging levels.

        :rtype: QtWidgets.QActionGroup
        """

        # Create action group
        #
        actionGroup = QtWidgets.QActionGroup(parent)
        actionGroup.setObjectName(name)
        actionGroup.setExclusive(True)
        actionGroup.triggered.connect(self.levelChanged)

        # Create level actions
        #
        for level in range(0, logging.CRITICAL + 1, 10):

            action = QtWidgets.QAction(logging.getLevelName(level), parent)
            action.setActionGroup(actionGroup)
            action.setCheckable(True)
            parent.addAction(action)

        return actionGroup

    def levelChanged(self, *args, **kwargs):
        """
        Callback to any user changes made to a logger level.

        :rtype: None
        """

        # Get checked level
        #
        actionGroup = self.sender()  # type: QtWidgets.QActionGroup

        action = actionGroup.checkedAction()
        level = LOG_LEVELS[actionGroup.actions().index(action)]

        # Update associated logger
        #
        logger = logging.getLogger(actionGroup.objectName())
        logger.setLevel(level)

    def syncLevel(self, *args, **kwargs):
        """
        Synchronizes the logger level associated with the sender.

        :rtype: None
        """

        # Get associated logger from sender
        #
        menu = self.sender()  # type: QtWidgets.QMenu

        name = 'root' if menu is self else menu.title()
        logger = logging.getLogger(name)

        # Synchronize action group
        #
        actions = self.actionGroups[name].actions()
        index = LOG_LEVELS.index(logger.level)

        actions[index].setChecked(True)

    def refresh(self, *args, **kwargs):
        """
        Forces the logging menu to refresh all of it's child actions.

        :rtype: None
        """

        # Clear all existing actions
        #
        self.clear()

        # Add root action group
        #
        self.addAction(QSeparator('Root Logger:', parent=self))
        self.actionGroups['root'] = self.createLevelActionGroup('root', parent=self)

        # Add child action groups
        #
        self.addAction(QSeparator('Child Loggers:', parent=self))

        for (key, value) in sorted(logging.Logger.manager.loggerDict.items()):

            # Check value type
            #
            if not isinstance(value, logging.Logger):

                continue

            # Create sub menu
            #
            subMenu = QtWidgets.QMenu(value.name, self)
            subMenu.aboutToShow.connect(self.syncLevel)

            self.addMenu(subMenu)

            # Create child action group
            #
            self.actionGroups[value.name] = self.createLevelActionGroup(value.name, parent=subMenu)

        self.addSeparator()

        # Add refresh action
        #
        action = QtWidgets.QAction('Refresh', self)
        action.triggered.connect(self.refresh)

        self.addAction(action)
