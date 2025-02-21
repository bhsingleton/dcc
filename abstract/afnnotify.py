"""
Defining DCC agnostic behavior for callbacks is aggravating to say the least.
There is no consistent naming convention: script jobs, events, notifies, callbacks, etc...
Nor is there any consistent typing for IDs.
The approach I've taken is to self contain the callbacks within each function set instance.
That way it is the responsibility of the function set to clean up callbacks upon garbage collection!
"""
from abc import ABCMeta, abstractmethod
from enum import IntEnum
from . import afnbase
from ..collections import notifylist
from ..vendor.six import with_metaclass

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Notification(IntEnum):
    """
    Enum class of all the available notifications.
    """

    PreFileOpen = 0
    PostFileOpen = 1
    SelectionChanged = 2
    Undo = 3
    Redo = 4


class AFnNotify(with_metaclass(ABCMeta, afnbase.AFnBase)):
    """
    Overload of `AFnBase` that outlines function set behaviour for DCC callbacks.
    """

    # region Enums
    Notification = Notification
    # endregion

    # region Dunderscores
    __slots__ = ('_notifications', '__weakref__')

    __notifications__ = {
        Notification.PreFileOpen: 'addPreFileOpenNotify',
        Notification.PostFileOpen: 'addPostFileOpenNotify',
        Notification.SelectionChanged: 'addSelectionChangedNotify',
        Notification.Undo: 'addUndoNotify',
        Notification.Redo: 'addRedoNotify',
    }

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(AFnNotify, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._notifications = {}

        for member in Notification:

            self._notifications[member] = notifylist.NotifyList()
            self._notifications[member].addCallback('itemRemoved', self.notifyRemoved)

    def __del__(self):
        """
        Private method called before this instance is sent for garbage collection.

        :rtype: None
        """

        self.clear()

    def __len__(self):
        """
        Private method that returns the size of this instance.

        :rtype: int
        """

        return sum(map(len, self._notifications.values()))
    # endregion

    # region Callbacks
    def notifyRemoved(self, value):
        """
        Callback method to whenever a DCC callback requires unregistering.

        :type value: Any
        :rtype: None
        """

        self.unregisterNotify(value)
    # endregion

    # region Methods
    def addNotify(self, notification, func):
        """
        Adds a new notify using the specified notify type.

        :type notification: Notification
        :type func: Callable
        :rtype: None
        """

        # Check if function already notified
        #
        funcName = self.__notifications__.get(notification, '')
        delegate = getattr(self, funcName, None)

        if callable(delegate):

            return delegate(func)

        else:

            raise TypeError('addNotify() expects a valid notification (%s given)!' % notification)

    def removeNotify(self, notification):
        """
        Removes the specified notify from the scene.

        :type notification: Notification
        :rtype: None
        """

        self._notifications[notification].clear()

    def registerNotify(self, notification, notifyId):
        """
        Registers a new notify with the internal tracker.
        You must call this method after creating a DCC callback for it to be tracked properly!

        :type notification: Notification
        :type notifyId: Any
        :rtype: None
        """

        self._notifications[notification].append(notifyId)

    @abstractmethod
    def unregisterNotify(self, notifyId):
        """
        Unregisters the supplied DCC notification ID.
        Do not call this method unless you know what you're doing!

        :type notifyId: Any
        :rtype: None
        """

        pass

    @abstractmethod
    def addPreFileOpenNotify(self, func):
        """
        Adds notify before a new scene is opened.

        :type func: Callable
        :rtype: None
        """

        pass

    @abstractmethod
    def addPostFileOpenNotify(self, func):
        """
        Adds notify after a new scene is opened.

        :type func: Callable
        :rtype: None
        """

        pass

    @abstractmethod
    def addSelectionChangedNotify(self, func):
        """
        Adds notify when the active selection is changed.

        :type func: Callable
        :rtype: None
        """

        pass

    @abstractmethod
    def addUndoNotify(self, func):
        """
        Adds notify when the user undoes a command.

        :type func: Callable
        :rtype: None
        """

        pass

    @abstractmethod
    def addRedoNotify(self, func):
        """
        Adds notify when the user redoes a command.

        :type func: Callable
        :rtype: None
        """

        pass

    def clear(self):
        """
        Removes all notifications.

        :rtype: None
        """

        for (notification, notifyIds) in self._notifications.items():

            notifyIds.clear()
    # endregion
