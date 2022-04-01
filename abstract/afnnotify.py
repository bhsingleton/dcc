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
from six import with_metaclass, string_types
from functools import partial
from enum import IntEnum
from collections import namedtuple
from dcc.abstract import afnbase
from dcc.collections import sparsearray

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


Notify = namedtuple('Notify', ['typeId', 'weakMethod'])


class WeakMethod(object):
    """
    Base class used to create weak references to methods.
    """

    # region Dunderscores
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

    def __eq__(self, other):
        """
        Evaluates if this ref is equivalent to the supplied object.

        :type other: object
        :rtype: bool
        """

        return self.__call__() == other

    def __ne__(self, other):
        """
        Evaluates if this ref is not equivalent to the supplied object.

        :type other: object
        :rtype: bool
        """

        return self.__call__() != other
    # endregion

    # region Methods
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
    # endregion


class Notifications(IntEnum):
    """
    Collection of notification types.
    """

    Unknown = -1
    PreFileOpen = 0
    PostFileOpen = 1
    Undo = 2
    Redo = 3
    SelectionChanged = 4


class AbstractNotification(with_metaclass(ABCMeta, object)):
    """
    Abstract base class used as a delegate for DCC notifies.
    Each DCC should derive its overloads from this class for each notification type.
    """

    # region Dunderscores
    __slots__ = ('_typeId', '_delegate', '_handle')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :type name: str
        :type handle: Any
        :rtype: None
        """

        # Call parent method
        #
        super(AbstractNotification, self).__init__()

        # Declare private variables
        #
        self._typeId = kwargs.get('typeId', Notifications.Unknown)
        self._delegate = kwargs.get('delegate', None)
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
    # endregion

    # region Properties
    @property
    def typeId(self):
        """
        Getter method that returns the type id for this instance.

        :rtype: Notifications
        """

        return self._typeId

    @property
    def typeName(self):
        """
        Getter method that returns the type name for this instance.

        :rtype: str
        """

        return self.typeId.name

    @property
    def delegate(self):
        """
        Getter method that returns the function hook for this notification.

        :rtype: function
        """

        return self._delegate

    @property
    def handle(self):
        """
        Getter method that returns the handle for this notify.

        :rtype: Any
        """

        return self._handle
    # endregion

    # region Methods
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
    # endregion


def delegate(*args, **kwargs):
    """
    Notify hook used to delegate to the associated function set.
    By using an unbound method we can avoid reference counts to function set instances.
    Once all references to a function set are gone we can clean up all notification handles.

    :rtype: None
    """

    # Get associated object id
    #
    objectId = kwargs.pop('objectId', 0)
    ref = AFnNotify.__instances__.get(objectId)

    instance = None

    if callable(ref):

        instance = ref()

    # Check if instance still exists
    #
    if isinstance(instance, AFnNotify):

        instance.notify(*args, **kwargs)


class AFnNotify(with_metaclass(ABCMeta, afnbase.AFnBase)):
    """
    Overload of AFnBase that outlines function set behaviour for DCC callbacks.
    For the sake of backwards compatibility each overload should register its callbacks with this class.
    From there this class will handle notifying all the associated functions.
    That way we're not shooting ourselves in the foot by purely relying on string execution.
    """

    # region Dunderscores
    __slots__ = ('_notifications', '_functions', '__weakref__')
    __notifications__ = {}
    __instances__ = {}

    def __new__(cls, *args, **kwargs):
        """
        Private methods called before a new instance is created.

        :rtype: AFnNotify
        """

        # Check if notifications have been registered
        #
        if not cls.hasRegistered():

            cls.register()

        # Call parent method
        #
        instance = super(AFnNotify, cls).__new__(cls)
        cls.__instances__[id(instance)] = weakref.ref(instance)

        return instance

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(AFnNotify, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._notifications = {typeId: T(typeId=typeId, delegate=self.delegate(typeId)) for (typeId, T) in self.__notifications__.items()}
        self._functions = sparsearray.SparseArray()

    def __del__(self):
        """
        Private method called before this instance is sent for garbage collection.

        :rtype: None
        """

        self.deleteLater()
    # endregion

    # region Methods
    def notify(self, *args, **kwargs):
        """
        Notifies all the functions associated with the given code.

        :rtype: None
        """

        # Iterate through functions
        #
        typeId = kwargs.pop('typeId', Notifications.Unknown)
        log.debug('Notify received: %s, args = %s, kwargs = %s' % (typeId, args, kwargs))

        for func in self.iterFunctions(typeId=typeId):

            func(*args, **kwargs)

    def hasNotifyType(self, typeId):
        """
        Evaluates if the supplied notify type exists.

        :type typeId: int
        :rtype: bool
        """

        return typeId in self._notifications

    def nextAvailableId(self):
        """
        Returns a unique id for a new notify.

        :rtype: int
        """

        return self._functions.nextAvailableIndex()

    def delegate(self, typeId):
        """
        Returns an unbound delegate for notifies.

        :type typeId: Notifications
        :rtype: function
        """

        return partial(delegate, objectId=id(self), typeId=typeId)

    def iterFunctions(self, typeId=None):
        """
        Returns a generator that yields all notified functions.
        This method will also clean up dead references on use!

        :type typeId: Notifications
        :rtype: iter
        """

        # Iterate through notifies
        #
        deleteLater = []

        for (notifyId, notify) in self._functions.items():

            # Inspect type id
            #
            if isinstance(typeId, Notifications) and notify.typeId != typeId:

                continue

            # Get weak reference
            #
            func = notify.weakMethod()

            if callable(func):

                yield func

            else:

                deleteLater.append(notifyId)
                continue

        # Cleanup dead methods
        #
        for notifyId in deleteLater:

            del self._functions[notifyId]

    def hasNotify(self, func):
        """
        Evaluates if the supplied function already has a notify.

        :type func: function
        :rtype: bool
        """

        return func in list(self.iterFunctions())

    def addPreFileOpenNotify(self, func):
        """
        Adds notify before a new scene is opened.

        :type func: method
        :rtype: int
        """

        return self.addNotify(Notifications.PreFileOpen, func)

    def addPostFileOpenNotify(self, func):
        """
        Adds notify after a new scene is opened.

        :type func: method
        :rtype: int
        """

        return self.addNotify(Notifications.PostFileOpen, func)

    def addUndoNotify(self, func):
        """
        Adds notify when the user undoes a command.

        :type func: method
        :rtype: int
        """

        return self.addNotify(Notifications.Undo, func)

    def addRedoNotify(self, func):
        """
        Adds notify when the user redoes a command.

        :type func: method
        :rtype: int
        """

        return self.addNotify(Notifications.Redo, func)

    def addSelectionChangedNotify(self, func):
        """
        Adds notify when the active selection is changed.

        :type func: method
        :rtype: int
        """

        return self.addNotify(Notifications.SelectionChanged, func)

    def addNotify(self, typeId, func):
        """
        Adds a new notify using the specified notify type.

        :type typeId: int
        :type func: function
        :rtype: int
        """

        # Inspect type id
        #
        if isinstance(typeId, string_types):

            typeId = Notifications['typeId']

        # Check if notify type exists
        #
        if not self.hasNotifyType(typeId):

            raise TypeError('addNotify() expects a valid notify type (%s given)!' % typeId)

        # Check if function already notified
        #
        if not self.hasNotify(func):

            index = self.nextAvailableId()
            self._functions[index] = Notify(typeId=typeId, weakMethod=WeakMethod(func))

            return index

        else:

            return list(self.iterFunctions()).index(func)

    def removeNotify(self, notifyId):
        """
        Removes the specified notify.

        :type notifyId: int
        :rtype: bool
        """

        if self._functions.hasIndex(notifyId):

            del self._functions[notifyId]
            return True

        else:

            return False

    @classmethod
    def hasRegistered(cls):
        """
        Evaluates if the notification constructors have been registered.

        :rtype: bool
        """

        return len(cls.__notifications__) > 0

    @classmethod
    @abstractmethod
    def register(cls):
        """
        Registers all the notification constructors for this function set.

        :rtype: None
        """

        pass

    @classmethod
    def registerNotification(cls, notification, typeId=Notifications.Unknown):
        """
        Registers the supplied notification as the specified type.

        :type notification: Union[type, function]
        :type typeId: Notifications
        :rtype: None
        """

        cls.__notifications__[typeId] = notification

    @classmethod
    def unregisterNotification(cls, typeId):
        """
        Unregisters the specified type.

        :type typeId: Notifications
        :rtype: None
        """

        del cls.__notifications__[typeId]

    def deleteLater(self):
        """
        Removes all notifications along with their registered functions.

        :rtype: None
        """

        # Iterate through notifications
        #
        for (typeId, notification) in self._notifications.items():

            log.info('Destroying %s notification...' % notification.typeName)
            notification.destroy()

        # Clear arrays
        #
        self._notifications.clear()
        self._functions.clear()

        # Delete self reference
        #
        del self.__instances__[id(self)]
    # endregion
