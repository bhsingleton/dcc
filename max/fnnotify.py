import pymxs

from uuid import uuid4
from ..abstract.afnnotify import AFnNotify

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnNotify(AFnNotify):
    """
    Overload of `AFnNotify` that implements the notify interface for 3ds-Max.
    """

    __slots__ = ()

    def unregisterNotify(self, callbackId):
        """
        Unregisters the supplied callback ID.

        :type callbackId: Any
        :rtype: None
        """

        if pymxs.runtime.isKindOf(callbackId, pymxs.runtime.Name):

            log.info('Removing callback: %s' % callbackId)
            pymxs.runtime.callbacks.removeScripts(id=callbackId)

    def addPreFileOpenNotify(self, func):
        """
        Adds notify before a new scene is opened.

        :type func: Callable
        :rtype: None
        """

        callbackId = pymxs.runtime.Name(uuid4().hex)

        pymxs.runtime.callbacks.addScript(pymxs.runtime.Name('filePreOpen'), func, id=callbackId, persistent=False)
        self.registerNotify(self.Notification.PreFileOpen, callbackId)

    def addPostFileOpenNotify(self, func):
        """
        Adds notify after a new scene is opened.

        :type func: Callable
        :rtype: None
        """

        callbackId = pymxs.runtime.Name(uuid4().hex)

        pymxs.runtime.callbacks.addScript(pymxs.runtime.Name('filePostOpen'), func, id=callbackId, persistent=False)
        self.registerNotify(self.Notification.PostFileOpen, callbackId)

    def addSelectionChangedNotify(self, func):
        """
        Adds notify when the active selection is changed.

        :type func: Callable
        :rtype: None
        """

        callbackId = pymxs.runtime.nodeEventCallback(selectionChanged=func, subobjectSelectionChanged=func)
        self.registerNotify(self.Notification.SelectionChanged, callbackId)

    def addUndoNotify(self, func):
        """
        Adds notify when the user undoes a command.

        :type func: Callable
        :rtype: None
        """

        callbackId = pymxs.runtime.Name(uuid4().hex)

        pymxs.runtime.callbacks.addScript(pymxs.runtime.Name('sceneUndo'), func, id=callbackId, persistent=False)
        self.registerNotify(self.Notification.Undo, callbackId)

    def addRedoNotify(self, func):
        """
        Adds notify when the user redoes a command.

        :type func: Callable
        :rtype: None
        """

        callbackId = pymxs.runtime.Name(uuid4().hex)

        pymxs.runtime.callbacks.addScript(pymxs.runtime.Name('sceneRedo'), func, id=callbackId, persistent=False)
        self.registerNotify(self.Notification.Redo, callbackId)

    def clear(self):
        """
        Removes all notifications.

        :rtype: None
        """

        # Call parent method
        #
        super(FnNotify, self).clear()

        # Perform garbage collection
        #
        pymxs.runtime.gc(light=True)
