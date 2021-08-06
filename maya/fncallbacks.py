import maya.api.OpenMaya as om

from ..abstract import afncallbacks

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnCallbacks(afncallbacks.AFnCallbacks):
    """
    Overload of AFnCallbacks that interfaces with callbacks in Maya.
    """

    __slots__ = ()

    def addFileOpenedCallback(self, func):
        """
        Adds a callback whenever a new scene is opened.

        :type func: method
        :rtype: Union[int, str]
        """

        return om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, func)

    def addSelectionChangedCallback(self, func):
        """
        Adds a callback whenever the active selection is changed.

        :type func: method
        :rtype: Union[int, str]
        """

        return om.MEventMessage.addEventCallback('selectionChanged', func)

    def addComponentSelectionChangedCallback(self, func):
        """
        Adds a callback whenever the active component selection is changed.

        :type func: method
        :rtype: Union[int, str]
        """

        return self.addSelectionChangedCallback(func)

    def removeCallback(self, callbackId):
        """
        Removes a callback that is currently in use.

        :type callbackId: Union[str, int]
        :rtype: None
        """

        om.MMessage.removeCallback(callbackId)
