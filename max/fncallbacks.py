import pymxs

from six import string_types
from uuid import uuid4

from ..abstract import afncallbacks

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnCallbacks(afncallbacks.AFnCallbacks):
    """
    Overload of AFnCallbacks that interfaces with callbacks in 3DS Max.
    """

    __slots__ = ()

    @staticmethod
    def generateID():
        """
        Returns an ID that can be used with Max callbacks.

        :rtype: pymxs.runtime.name
        """

        return pymxs.runtime.name(uuid4().hex)

    def addFileOpenedCallback(self, func):
        """
        Adds a callback whenever a new scene is opened.

        :type func: method
        :rtype: pymxs.runtime.name
        """

        uuid = self.generateID()
        pymxs.runtime.callbacks.addScript(pymxs.runtime.name('filePostOpen'), func, id=uuid)

        return uuid

    def addUndoCallback(self, func):
        """
        Adds a callback whenever undo is used.

        :type func: method
        :rtype: pymxs.runtime.name
        """

        uuid = self.generateID()
        pymxs.runtime.callbacks.addScript(pymxs.runtime.name('sceneUndo'), func, id=uuid)

        return uuid

    def addRedoCallback(self, func):
        """
        Adds a callback whenever redo is used.

        :type func: method
        :rtype: pymxs.runtime.name
        """

        uuid = self.generateID()
        pymxs.runtime.callbacks.addScript(pymxs.runtime.name('sceneRedo'), func, id=uuid)

        return uuid

    def addSelectionChangedCallback(self, func):
        """
        Adds a callback whenever the active selection is changed.

        :type func: method
        :rtype: pymxs.runtime.name
        """

        uuid = self.generateID()
        pymxs.runtime.callbacks.addScript(pymxs.runtime.name('selectionSetChanged'), func, id=uuid)

        return uuid

    def addComponentSelectionChangedCallback(self, func):
        """
        Adds a callback whenever the active component selection is changed.

        :type func: method
        :rtype: pymxs.runtime.NodeEventCallback
        """

        return pymxs.runtime.nodeEventCallback(subobjectSelectionChanged=func)

    def removeCallback(self, callbackId):
        """
        Removes a callback that is currently in use.

        :type callbackId: pymxs.runtime.name
        :rtype: None
        """

        if pymxs.runtime.classOf(callbackId) == pymxs.runtime.name:

            pymxs.runtime.callbacks.removeScripts(id=callbackId)
