"""
Developer notes:
Defining DCC agnostic behavior for notifies is aggravating to say the least.
There is no consist naming convention: script jobs, events, notifies, callbacks, etc...
Nor is there any consistent typing for IDs.
In order to circumvent this we will create classes for each notify we want to leverage.
These classes will act as the point of contact for the DCC.
Once the DCC triggers the notify class we will go through and call all of its registered functions.
This way we can create predictable behavior for each DCC and maintain consistent typing.
"""
import weakref
import inspect
import sys

from abc import ABCMeta, abstractmethod
from six import with_metaclass
from enum import IntEnum

from dcc.abstract import afnbase

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class WeakMethod(object):
    """
    Base class used to create references to methods.
    """

    __slots__ = ('_instance', '_function')

    def __init__(self, func):
        """
        Private method called after a new instance has been created.

        :type func: callable
        :rtype: None
        """

        # Call parent method
        #
        super(WeakMethod, self).__init__()

        # Declare private variables
        #
        if self.isUnboundMethod(func):

            self._function = weakref.ref(func, )

        elif self.isBoundMethod(func):

            self._instance = weakref.ref(func.__self__)
            self._function = weakref.ref(func.__func__)

        else:

            raise TypeError('WeakMethod() expects a valid method!')

    def __call__(self, *args, **kwargs):
        """
        Private method that returns the method associated with this reference.

        :rtype: function
        """

        # Check if instance and function are alive
        #
        if not self.isAlive():

            return None

        # Check if this is a bound method
        #
        func = self._function()

        if hasattr(self, '_instance'):

            # Bind method to instance
            #
            instance = self._instance()

            method = func.__get__(instance, type(instance))
            setattr(instance, func.__name__, method)

            return method

        else:

            return func

    @staticmethod
    def isUnboundMethod(obj):
        """
        Evaluates if the supplied obj is an unbound method.

        :type obj: callable
        :rtype: bool
        """

        return inspect.isfunction(obj)

    @staticmethod
    def isBoundMethod(obj):
        """
        Evaluates if the supplied object is a bound method.

        :type obj: callable
        :rtype: bool
        """

        return hasattr(obj, '__self__') and hasattr(obj, '__func__')

    def isAlive(self):
        """
        Evaluates if this reference is still alive.

        :rtype: bool
        """

        # Inspect method binding
        #
        if hasattr(self, '_instance'):

            # Check if weak refs are alive
            #
            instance = self._instance()
            function = self._function()

            if instance is None or function is None:

                return False

            # Check if the module is derived from the system modules
            # If not then the module has been reloaded
            #
            module = inspect.getmodule(instance)
            return module == sys.modules[module.__name__]

        else:

            return self._function() is not None


class Notifications(IntEnum):
    """
    Collection of notification types.
    """

    Unknown = 0
    PreFileOpen = 1
    PostFileOpen = 2
    Undo = 3
    Redo = 4
    SelectionChanged = 5


class Notification(with_metaclass(ABCMeta, object)):
    """
    Abstract base class used to define behavior for notifications.
    Each DCC should derive its overloads from this class for each notification type.
    """

    __slots__ = ('_handle', '_ids', '_type')
    __functions__ = {}  # type: dict[str:callable]

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :type name: str
        :type handle: Any
        :rtype: None
        """

        # Call parent method
        #
        super(Notification, self).__init__()

        # Declare private variables
        #
        self._type = kwargs.get('notifyType', Notifications.Unknown)
        self._ids = []
        self._handle = self.creator()

    def __call__(self, *args, **kwargs):
        """
        Private method that is called when this instance is called.

        :rtype: None
        """

        self.notify()

    def __del__(self):
        """
        Private method that is called before this instance is deleted.

        :rtype: None
        """

        if self._handle is not None:

            self.destroy()

    def __delitem__(self, _id):
        """
        Private method that deletes an indexed item.

        :type _id: int
        :rtype: None
        """

        self.remove(_id)

    def __contains__(self, item):
        """
        Private method that evaluates if the given item exists.

        :type item: Union[int, function]
        :rtype: bool
        """

        if isinstance(item, int):

            return item in self._ids

        elif callable(item):

            return item in self.functions()

        else:

            return False

    @property
    def name(self):
        """
        Getter method that returns the type name for this instance.

        :rtype: str
        """

        return self._type.name

    @property
    def handle(self):
        """
        Getter method that returns the handle for this notify.

        :rtype: Any
        """

        return self._handle

    @property
    def ids(self):
        """
        Getter method that returns the ids in use by this notify.

        :rtype: list[int]
        """

        return self._ids

    def iterFunctions(self):
        """
        Returns a generator that yields all functions from this notify.

        :rtype: iter
        """

        # Iterate through ids
        #
        for _id in self._ids:

            # Check if weakref is still alive
            #
            ref = self.__class__.__functions__.get(_id, lambda: None)
            func = ref()

            if func is not None:

                yield func

            else:

                continue

    def functions(self):
        """
        Returns a list of functions from this notify.

        :rtype: list[function]
        """

        return list(self.iterFunctions())

    def notify(self, *args, **kwargs):
        """
        Calls all of the functions derived from this notification.
        The additional arguments are for any DCC callbacks.

        :rtype: None
        """

        # Iterate through ids
        #
        deleteLater = []

        for _id in self._ids:

            ref = self.__class__.__functions__[_id]

            if ref.isAlive():

                func = ref()
                func()

            else:

                deleteLater.append(_id)
                continue

        # Remove dead references
        #
        for _id in deleteLater:

            self.remove(_id)

    def type(self):
        """
        Returns the notify type constant for this instance.

        :rtype: Notifications
        """

        return self._type

    @classmethod
    def createUniqueID(cls):
        """
        Returns a unique id for a new notify.

        :rtype: int
        """

        keys = list(cls.__functions__.keys())
        numKeys = len(keys)

        if numKeys == 0:

            return 0

        else:

            return keys[-1] + 1

    def add(self, func):
        """
        Adds the supplied function to the notify list.

        :type func: function
        :rtype: int
        """

        # Check if function has already been added
        #
        if func not in self:

            # Assign func using new id
            #
            notifyId = self.createUniqueID()

            self.__class__.__functions__[notifyId] = WeakMethod(func)
            self._ids.append(notifyId)

            return notifyId

        else:

            return self.index(func)

    def remove(self, _id):
        """
        Removes the supplied notify ID.

        :type _id: int
        :rtype: bool
        """

        try:

            self._ids.remove(_id)
            del self.__class__.__functions__[_id]

            return True

        except (ValueError, KeyError) as exception:

            log.debug(exception)
            return False

    def index(self, func):
        """
        Returns the notify ID associated with the given function.

        :type func: function
        :rtype: int
        """

        try:

            functions = self.functions()
            index = functions.index(func)

            return self._ids[index]

        except ValueError as exception:

            log.debug(exception)
            return None

    @abstractmethod
    def creator(self):
        """
        Returns a new callback handle for this instance.

        :rtype: Any
        """

        pass

    @abstractmethod
    def destroy(self):
        """
        Destroys the callback handle from this instance.

        :rtype: None
        """

        pass


class AFnNotify(with_metaclass(ABCMeta, afnbase.AFnBase)):
    """
    Overload of AFnBase that outlines function set behaviour for DCC callbacks.
    For the sake of backwards compatibility each overload should register its callbacks with this class.
    From there this class will handle notifying all of the associated functions.
    That way we're not shooting ourselves in the foot by purely relying on string execution.
    """

    __slots__ = ()
    __notifications__ = {}

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(AFnNotify, self).__init__(*args, **kwargs)

        # Check if class has been initialized
        #
        if not self.isInitialized():

            log.info('Initializing notifies...')
            self.initialize()

    @classmethod
    def isInitialized(cls):
        """
        Evaluates if the function set globals have been initialized.

        :rtype: bool
        """

        return len(cls.__notifications__) > 0

    @classmethod
    @abstractmethod
    def initialize(cls):
        """
        Registers all of the required notifications for derived classes.
        Use the registerNotification method to assign a notification to the private container.

        :rtype: None
        """

        pass

    @classmethod
    def registerNotification(cls, notification):
        """
        Registers the supplied notification under the given type.

        :type notification: Notification
        :rtype: None
        """

        # Assign notification under type
        #
        cls.__notifications__[notification.type()] = notification

    @classmethod
    def notify(cls, notifyType):
        """
        Notifies all of the functions associated with the given code.

        :type notifyType: int
        :rtype: None
        """

        # Check if type is valid
        #
        if notifyType == Notifications.Unknown:

            raise TypeError('notify() cannot notify unknown type!')

        # Check for none type
        #
        notification = cls.__notifications__.get(notifyType, None)

        if notification is not None:

            notification.notify()

        else:

            raise TypeError('notify() expects a valid notify type!')

    @classmethod
    def hasNotifyType(cls, notifyType):
        """
        Evaluates if the supplied notify type exists.

        :type notifyType: int
        :rtype: bool
        """

        return notifyType in cls.__notifications__

    def addPreFileOpenNotify(self, func):
        """
        Adds a notify before a new scene is opened.

        :type func: method
        :rtype: int
        """

        return self.addNotify(Notifications.PreFileOpened, func)

    def addPostFileOpenNotify(self, func):
        """
        Adds a notify after a new scene is opened.

        :type func: method
        :rtype: int
        """

        return self.addNotify(Notifications.PostFileOpened, func)

    def addUndoNotify(self, func):
        """
        Adds a notify when the user undoes a command.

        :type func: method
        :rtype: int
        """

        return self.addNotify(Notifications.Undo, func)

    def addRedoNotify(self, func):
        """
        Adds a notify when the user redoes a command.

        :type func: method
        :rtype: int
        """

        return self.addNotify(Notifications.Redo, func)

    def addSelectionChangedNotify(self, func):
        """
        Adds a notify when the active selection is changed.

        :type func: method
        :rtype: int
        """

        return self.addNotify(Notifications.SelectionChanged, func)

    @classmethod
    def addNotify(cls, notifyType, func):
        """
        Adds a new notify using the specified notify type.

        :type notifyType: int
        :type func: function
        :rtype: int
        """

        # Check if notify type exists
        #
        if cls.hasNotifyType(notifyType):

            return cls.__notifications__[notifyType].add(func)

        else:

            raise TypeError('addNotify() no registered notify found for this type!')

    @classmethod
    def removeNotify(cls, notifyId):
        """
        Removes a notify that is currently in use.
        It's lazy but it gets the job done...

        :type notifyId: int
        :rtype: None
        """

        for notification in cls.__notifications__.values():

            notification.remove(notifyId)

    @classmethod
    def clear(cls):
        """
        Removes all notifications along with their registered functions.

        :rtype: None
        """

        notifyTypes = list(cls.__notifications__.keys())

        for notifyType in notifyTypes:

            notification = cls.__notifications__.pop(notifyType)
            notification.destroy()
