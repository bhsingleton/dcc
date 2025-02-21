from maya.api import OpenMaya as om
from ..abstract.afnnotify import AFnNotify

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnNotify(AFnNotify):
    """
    Overload of AFnNotify that interfaces with callbacks in Maya.
    """

    __slots__ = ()

    def unregisterNotify(self, callbackId):
        """
        Unregisters the supplied Maya callback ID.

        :type callbackId: Any
        :rtype: None
        """

        log.info('Removing callback: %s' % callbackId)
        om.MMessage.removeCallback(callbackId)

    def addPreFileOpenNotify(self, func):
        """
        Adds notify before a new scene is opened.

        :type func: Callable
        :rtype: None
        """

        callbackId = om.MSceneMessage.addCallback(om.MSceneMessage.kBeforeOpen, func)
        self.registerNotify(self.Notification.PreFileOpen, callbackId)

    def addPostFileOpenNotify(self, func):
        """
        Adds notify after a new scene is opened.

        :type func: Callable
        :rtype: None
        """

        callbackId = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, func)
        self.registerNotify(self.Notification.PostFileOpen, callbackId)

    def addSelectionChangedNotify(self, func):
        """
        Adds notify when the active selection is changed.

        :type func: Callable
        :rtype: None
        """

        callbackId = om.MEventMessage.addEventCallback('SelectionChanged', func)
        self.registerNotify(self.Notification.SelectionChanged, callbackId)

    def addUndoNotify(self, func):
        """
        Adds notify when the user undoes a command.

        :type func: Callable
        :rtype: None
        """

        callbackId = om.MEventMessage.addEventCallback('Undo', func)
        self.registerNotify(self.Notification.Undo, callbackId)

    def addRedoNotify(self, func):
        """
        Adds notify when the user redoes a command.

        :type func: Callable
        :rtype: None
        """

        callbackId = om.MEventMessage.addEventCallback('Redo', func)
        self.registerNotify(self.Notification.Redo, callbackId)
