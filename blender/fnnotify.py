from ..abstract.afnnotify import AFnNotify

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnNotify(AFnNotify):
    """
    Overload of `AFnNotify` that implements the notify interface for Blender.
    """

    __slots__ = ()

    def unregisterNotify(self, callbackId):
        """
        Unregisters the supplied Maya callback ID.

        :type callbackId: Any
        :rtype: None
        """

        pass

    def addPreFileOpenNotify(self, func):
        """
        Adds notify before a new scene is opened.

        :type func: Callable
        :rtype: None
        """

        pass

    def addPostFileOpenNotify(self, func):
        """
        Adds notify after a new scene is opened.

        :type func: Callable
        :rtype: None
        """

        pass

    def addSelectionChangedNotify(self, func):
        """
        Adds notify when the active selection is changed.

        :type func: Callable
        :rtype: None
        """

        pass

    def addUndoNotify(self, func):
        """
        Adds notify when the user undoes a command.

        :type func: Callable
        :rtype: None
        """

        pass

    def addRedoNotify(self, func):
        """
        Adds notify when the user redoes a command.

        :type func: Callable
        :rtype: None
        """

        pass
