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

        :rtype: str
        """

        return uuid4().hex

    def addFileOpenedCallback(self, func):
        """
        Adds a callback whenever a new scene is opened.

        :type func: method
        :rtype: str
        """

        uuid = self.generateID()
        pymxs.runtime.callbacks.addScript('filePostOpen', func, id=uuid)

        return uuid

    def addSelectionChangedCallback(self, func):
        """
        Adds a callback whenever the active selection is changed.

        :type func: method
        :rtype: str
        """

        uuid = self.generateID()
        pymxs.runtime.callbacks.addScript('selectionSetChanged', func, id=uuid)

        return uuid

    def addComponentSelectionChangedCallback(self, func):
        """
        Adds a callback whenever the active component selection is changed.

        :type func: method
        :rtype: Union[int, str]
        """

        return pymxs.runtime.nodeEventCallback(subobjectSelectionChanged=func)

    def removeCallback(self, callbackId):
        """
        Removes a callback that is currently in use.

        :type callbackId: Union[str, int]
        :rtype: None
        """

        if isinstance(callbackId, string_types):

            pymxs.runtime.callbacks.removeScripts(id=callbackId)
