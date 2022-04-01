import pymxs

from functools import partial
from uuid import uuid4
from dcc.python import pythonutils
from dcc.abstract.afnnotify import AFnNotify, AbstractNotification, Notifications

MaxPlus = pythonutils.tryImport('MaxPlus')

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Callback(AbstractNotification):
    """
    Overload of Notification used to interface with 3ds max callbacks.
    """

    # region Dunderscores
    __slots__ = ('_callbackName', '_callbackId', '_callbackCode')

    def __init__(self, callbackName, **kwargs):
        """
        Private method called after a new instance is created.

        :type callbackName: str
        :rtype: None
        """

        # Declare private variables
        #
        self._callbackName = pymxs.runtime.Name(callbackName)
        self._callbackId = pymxs.runtime.Name(uuid4().hex)
        self._callbackCode = self.getCallbackCode(self._callbackName)

        # Call parent method
        #
        super(Callback, self).__init__(**kwargs)
    # endregion

    # region Properties
    @property
    def callbackName(self):
        """
        Getter method that returns the associated callback name.

        :rtype: pymxs.runtime.name
        """

        return self._callbackName

    @property
    def callbackId(self):
        """
        Getter method that returns the associated callback id.

        :rtype: pymxs.runtime.name
        """

        return self._callbackId

    @property
    def callbackCode(self):
        """
        Getter method that returns the associated callback code.

        :rtype: int
        """

        return self._callbackCode
    # endregion

    # region Methods
    @staticmethod
    def upperfirst(string):
        """
        Returns a string where the first letter is capitalized.

        :type string: str
        :rtype: str
        """

        return '{char}{letters}'.format(char=string[0].upper(), letters=string[1:])

    @staticmethod
    def supportsMaxPlus():
        """
        Returns an executable string that can trigger this instance.

        :rtype: str
        """
        
        return MaxPlus is not None

    @classmethod
    def getCallbackCode(cls, callbackName):
        """
        Returns the callback code associated with the given name.

        :type callbackName: pymxs.runtime.Name
        :rtype: int
        """

        if cls.supportsMaxPlus():

            return getattr(MaxPlus.NotificationCodes, cls.upperfirst(str(callbackName)))

        else:

            return None

    def creator(self):
        """
        Returns a new callback handle for this instance.

        :rtype: Any
        """

        # Evaluate if MaxPlus still exists
        #
        if self.supportsMaxPlus():

            return MaxPlus.NotificationManager.Register(
                self.callbackCode,
                self.delegate
            )

        else:

            pymxs.runtime.callbacks.addScript(
                self.callbackName,
                self.delegate,
                id=self.callbackId,
                persistent=False
            )

            return self.callbackId

    def destroy(self):
        """
        Destroys the callback handle from this instance.

        :rtype: None
        """

        if self.supportsMaxPlus():

            MaxPlus.NotificationManager.Unregister(self._handle)
            self._handle = None

            pymxs.runtime.gc(light=True)

        else:

            pymxs.runtime.callbacks.removeScripts(id=self._handle)
            self._handle = None

            pymxs.runtime.gc(light=True)
    # endregion


class NodeEventCallback(AbstractNotification):
    """
    Overload of Notification used to interface with 3ds Max node event callbacks.
    """

    # region Dunderscores
    __slots__ = ('_callbacks',)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.
        """

        # Declare private variables
        #
        self._callbacks = args

        # Call parent method
        #
        super(NodeEventCallback, self).__init__(**kwargs)
    # endregion

    # region Methods
    def creator(self):
        """
        Returns a new callback handle for this instance.

        :rtype: Any
        """

        kwargs = {x: self.delegate for x in self._callbacks}
        return pymxs.runtime.nodeEventCallback(**kwargs)

    def destroy(self):
        """
        Destroys the callback handle from this instance.

        :rtype: None
        """

        self._handle = None  # NodeEventCallback object will be deleted by GC
        pymxs.runtime.gc(light=True)
    # endregion


class FnNotify(AFnNotify):
    """
    Overload of AFnCallbacks that interfaces with callbacks in 3DS Max.
    """

    __slots__ = ()

    @classmethod
    def register(cls):
        """
        Registers all the notification constructors for this function set.

        :rtype: None
        """

        cls.registerNotification(partial(Callback, 'filePreOpen'), typeId=Notifications.PreFileOpen)
        cls.registerNotification(partial(Callback, 'filePostOpen'), typeId=Notifications.PostFileOpen)
        cls.registerNotification(partial(Callback, 'sceneUndo'), typeId=Notifications.Undo)
        cls.registerNotification(partial(Callback, 'sceneRedo'), typeId=Notifications.Redo)
        cls.registerNotification(partial(NodeEventCallback, 'selectionChanged', 'subobjectSelectionChanged'), typeId=Notifications.SelectionChanged)
