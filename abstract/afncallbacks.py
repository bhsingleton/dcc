from abc import ABCMeta, abstractmethod
from six import with_metaclass

from . import afnbase

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AFnCallbacks(with_metaclass(ABCMeta, afnbase.AFnBase)):
    """
    Overload of AFnBase that outlines function set behaviour for DCC callbacks.
    """

    __slots__ = ()

    @abstractmethod
    def addFileOpenedCallback(self, func):
        """
        Adds a callback whenever a new scene is opened.

        :type func: method
        :rtype: Union[int, str]
        """

        pass

    @abstractmethod
    def addUndoCallback(self, func):
        """
        Adds a callback whenever undo is used.

        :type func: method
        :rtype: Union[int, str]
        """

        pass

    @abstractmethod
    def addRedoCallback(self, func):
        """
        Adds a callback whenever redo is used.

        :type func: method
        :rtype: Union[int, str]
        """

        pass

    @abstractmethod
    def addSelectionChangedCallback(self, func):
        """
        Adds a callback whenever the active selection is changed.

        :type func: method
        :rtype: Union[int, str]
        """

        pass

    @abstractmethod
    def addComponentSelectionChangedCallback(self, func):
        """
        Adds a callback whenever the active component selection is changed.

        :type func: method
        :rtype: Union[int, str]
        """
        pass

    @abstractmethod
    def removeCallback(self, callbackId):
        """
        Removes a callback that is currently in use.

        :type callbackId: Union[str, int]
        :rtype: None
        """

        pass

    def removeCallbacks(self, callbackIds):
        """
        Removes a list of callbacks that are currently in use.

        :type callbackIds: list
        :rtype: None
        """

        for callbackId in callbackIds:

            self.removeCallback(callbackId)
