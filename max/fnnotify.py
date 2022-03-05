import pymxs

from ..abstract.afnnotify import AFnNotify, Notification, Notifications

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Callback(Notification):
    """
    Overload of Notification used to interface with max callbacks.
    """

    __slots__ = ('_callbackType', '_callbackId')

    def __init__(self, callbackType, **kwargs):
        """
        Private method called after a new instance is created.

        :type callbackType: str
        :type _id: str
        :rtype: None
        """

        # Check for none type
        #
        callbackId = kwargs.get('callbackId', None)

        if callbackId is None:

            callbackId = 'dcc{callback}'.format(callback=self.upperfirst(callbackType))

        # Declare private variables
        #
        self._callbackType = callbackType
        self._callbackId = callbackId

        # Call parent method
        #
        super(Callback, self).__init__(**kwargs)

    @property
    def callbackName(self):
        """
        Getter method that returns the associated callback name.

        :rtype: pymxs.runtime.name
        """

        return pymxs.runtime.name(self._callbackType)

    @property
    def callbackIdName(self):
        """
        Getter method that returns the associated id name.

        :rtype: pymxs.runtime.name
        """

        return pymxs.runtime.name(self._callbackId)

    @staticmethod
    def upperfirst(string):
        """
        Returns a string where the first letter is capitalized.

        :type string: str
        :rtype: str
        """

        return '{char}{letters}'.format(char=string[0].upper(), letters=string[1:])

    def createExecutable(self):
        """
        Returns an executable string that can trigger this instance.

        :rtype: str
        """
        
        return 'python.execute "from dcc import fnnotify; fnnotify.FnNotify.notify({type});"'.format(type=self.type())

    def creator(self):
        """
        Returns a new callback handle for this instance.

        :rtype: Any
        """

        pymxs.runtime.callbacks.addScript(
            self.callbackName,
            self.createExecutable(),
            id=self.callbackIdName,
            persistent=False
        )

        return self.callbackIdName

    def destroy(self):
        """
        Destroys the callback handle from this instance.

        :rtype: None
        """

        pymxs.runtime.callbacks.removeScripts(id=self._handle)
        self._handle = None


class NodeEventCallback(Notification):
    """
    Overload of Notification used to interface with max node event callbacks.
    """

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

    @property
    def callbackNames(self):
        """
        Getter method that returns a list of the associated callback names.

        :rtype: List[pymxs.runtime.name]
        """

        return [pymxs.runtime.name(x) for x in self._callbacks]

    def creator(self):
        """
        Returns a new callback handle for this instance.

        :rtype: Any
        """

        kwargs = {x: self.notify for x in self._callbacks}
        return pymxs.runtime.nodeEventCallback(**kwargs)

    def destroy(self):
        """
        Destroys the callback handle from this instance.

        :rtype: None
        """

        self._handle = None  # NodeEventCallback object will be deleted by GC
        pymxs.runtime.gc(light=True)


class FnNotify(AFnNotify):
    """
    Overload of AFnCallbacks that interfaces with callbacks in 3DS Max.
    """

    __slots__ = ()

    @classmethod
    def initialize(cls):
        """
        Registers all of the required notifications for 3ds Max.

        :rtype: None
        """

        cls.registerNotification(Callback('filePreOpen', notifyType=Notifications.PreFileOpen))
        cls.registerNotification(Callback('filePostOpen', notifyType=Notifications.PostFileOpen))
        cls.registerNotification(Callback('sceneUndo', notifyType=Notifications.Undo))
        cls.registerNotification(Callback('sceneRedo', notifyType=Notifications.Redo))
        cls.registerNotification(NodeEventCallback('selectionChanged', 'subobjectSelectionChanged', notifyType=Notifications.SelectionChanged))
