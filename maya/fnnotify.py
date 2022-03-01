import maya.cmds as mc
import maya.api.OpenMaya as om

from ..abstract.afnnotify import AFnNotify, Notification, Notifications

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Message(Notification):
    """
    Overload of Notification used to interface with max callbacks.
    """

    __slots__ = ('_message', '_messageAttr', '_messageType')

    def __init__(self, message, **kwargs):
        """
        Private method called after a new instance is created.

        :type message: type
        :key messageAttr: str
        :key messageType: Union[int, str]
        :rtype: None
        """

        # Declare private variables
        #
        self._message = message
        self._messageAttr = kwargs.get('messageAttr', 'addCallback')
        self._messageType = kwargs.get('messageType', None)

        # Call parent method
        #
        super(Message, self).__init__(**kwargs)

    def creator(self):
        """
        Returns a new callback handle for this instance.

        :rtype: Any
        """

        func = getattr(self._message, self._messageAttr)
        return func(self._messageType, self.notify)

    def destroy(self):
        """
        Destroys the callback handle from this instance.

        :rtype: None
        """

        om.MMessage.removeCallback(self._handle)
        self._handle = None


class FnNotify(AFnNotify):
    """
    Overload of AFnNotify that interfaces with callbacks in Maya.
    """

    __slots__ = ()

    @classmethod
    def initialize(cls):
        """
        Registers all of the required notifications for Maya.

        :rtype: None
        """

        cls.registerNotification(Message(om.MSceneMessage, messageType=om.MSceneMessage.kBeforeOpen, notifyType=Notifications.PreFileOpen))
        cls.registerNotification(Message(om.MSceneMessage, messageType=om.MSceneMessage.kAfterOpen, notifyType=Notifications.PostFileOpen))
        cls.registerNotification(Message(om.MEventMessage, messageAttr='addEventCallback', messageType='Undo', notifyType=Notifications.Undo))
        cls.registerNotification(Message(om.MEventMessage, messageAttr='addEventCallback', messageType='Redo', notifyType=Notifications.Redo))
        cls.registerNotification(Message(om.MEventMessage, messageAttr='addEventCallback', messageType='SelectionChanged', notifyType=Notifications.SelectionChanged))
