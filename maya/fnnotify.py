import maya.cmds as mc
import maya.api.OpenMaya as om

from functools import partial
from dcc.abstract.afnnotify import AFnNotify, AbstractNotification, Notifications

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Message(AbstractNotification):
    """
    Overload of Notification used to interface with max callbacks.
    """

    # region Dunderscores
    __slots__ = ('_messageCls', '_messageAttr', '_messageType')

    def __init__(self, T, **kwargs):
        """
        Private method called after a new instance is created.

        :type T: type
        :key messageAttr: str
        :key messageType: Union[int, str]
        :rtype: None
        """

        # Declare private variables
        #
        self._messageCls = T
        self._messageAttr = kwargs.get('messageAttr', 'addCallback')
        self._messageType = kwargs.get('messageType', None)

        # Call parent method
        #
        super(Message, self).__init__(**kwargs)
    # endregion

    # region Methods
    def creator(self):
        """
        Returns a new callback handle for this instance.

        :rtype: Any
        """

        func = getattr(self._messageCls, self._messageAttr)
        return func(self._messageType, self.delegate)

    def destroy(self):
        """
        Destroys the callback handle from this instance.

        :rtype: None
        """

        om.MMessage.removeCallback(self._handle)
        self._handle = None
    # endregion


class FnNotify(AFnNotify):
    """
    Overload of AFnNotify that interfaces with callbacks in Maya.
    """

    __slots__ = ()

    @classmethod
    def register(cls):
        """
        Registers all the notification constructors for this function set.

        :rtype: None
        """

        cls.registerNotification(partial(Message, om.MSceneMessage, messageType=om.MSceneMessage.kBeforeOpen), typeId=Notifications.PreFileOpen)
        cls.registerNotification(partial(Message, om.MSceneMessage, messageType=om.MSceneMessage.kAfterOpen), typeId=Notifications.PostFileOpen)
        cls.registerNotification(partial(Message, om.MEventMessage, messageAttr='addEventCallback', messageType='Undo'), typeId=Notifications.Undo)
        cls.registerNotification(partial(Message, om.MEventMessage, messageAttr='addEventCallback', messageType='Redo'), typeId=Notifications.Redo)
        cls.registerNotification(partial(Message, om.MEventMessage, messageAttr='addEventCallback', messageType='SelectionChanged'), typeId=Notifications.SelectionChanged)
