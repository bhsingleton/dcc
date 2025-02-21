import weakref

from abc import ABCMeta, abstractmethod
from ..decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class SingletonMeta(ABCMeta):
    """
    Overload of `ABCMeta` that implements singleton patterns.
    """

    # region Dunderscores
    __instances__ = {}

    def __call__(cls, *args, **kwargs):
        """
        Private method that's called whenever this class is evoked.

        :rtype: SingletonMeta
        """

        return cls.getInstance(*args, **kwargs)
    # endregion

    # region Methods
    def creator(cls, *args, **kwargs):
        """
        Returns a new instance of this class.

        :rtype: SingletonMeta
        """

        instance = super(SingletonMeta, cls).__call__(*args, **kwargs)
        cls.__instances__[cls.__name__] = instance

        return instance

    def hasInstance(cls):
        """
        Evaluates if an instance of this class already exists.

        :rtype: bool
        """

        return cls.__instances__.get(cls.__name__, None) is not None

    def getInstance(cls, *args, **kwargs):
        """
        Returns an instance of this class.

        :key asWeakReference: bool
        :rtype: Union[SingletonMeta, weakref.ref]
        """

        # Check if instance exists
        #
        instance = None

        if cls.hasInstance():

            instance = cls.__instances__[cls.__name__]

        else:

            instance = cls.creator()

        # Check if weak reference should be returned
        #
        asWeakReference = kwargs.get('asWeakReference', False)

        if asWeakReference:

            return instance.weakReference()

        else:

            return instance
    # endregion


class Singleton(object, metaclass=SingletonMeta):
    """
    Abstract base class used for singleton objects.
    """

    # region Dunderscores
    __slots__ = ('__weakref__',)
    # endregion

    # region Properties
    @classproperty
    def className(cls):
        """
        Getter method that returns the name of this class.

        :rtype: str
        """

        return cls.__name__

    @classproperty
    def nullWeakReference(cls):
        """
        Returns a null weak reference that is still callable.

        :rtype: lambda
        """

        return lambda: None
    # endregion

    # region Methods
    def weakReference(self):
        """
        Returns a weak reference to this instance.

        :rtype: weakref.ref
        """

        return weakref.ref(self)
    # endregion
