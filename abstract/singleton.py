import weakref

from abc import ABCMeta, abstractmethod
from six import with_metaclass
from dcc.decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Singleton(with_metaclass(ABCMeta, object)):
    """
    Base class used for singleton objects.
    """

    # region Dunderscores
    __slots__ = ('__weakref__',)
    __instances__ = {}

    def __new__(cls, *args, **kwargs):
        """
        Private method called before a new instance is created.

        :rtype: Singleton
        """

        instance = cls.__instances__.get(cls.className, None)

        if instance is None:

            instance = super(Singleton, cls).__new__(cls)
            cls.__instances__[cls.className] = instance

        return instance

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(Singleton, self).__init__()
    # endregion

    # region Properties
    @classproperty
    def className(cls):
        """
        Getter method that returns the name of this class.

        :rtype: str
        """

        return cls.__name__
    # endregion

    # region Methods
    def isInitialized(self):
        """
        Evaluates if this instance has been initialized.

        :rtype: bool
        """

        return all([hasattr(self, attr) for attr in self.__class__.__slots__])

    @classmethod
    def creator(cls):
        """
        Returns a new instance of this class.
        Overload this method to change the way instances are created.

        :rtype: Singleton
        """

        return cls()

    @classmethod
    def hasInstance(cls):
        """
        Evaluates if an instance of this class already exists.

        :rtype: bool
        """

        return cls.className in cls.__instances__

    @classmethod
    def getInstance(cls, asWeakReference=False):
        """
        Returns an instance of this class.

        :type asWeakReference: bool
        :rtype: Union[Singleton, weakref.ref]
        """

        # Check if instance exists
        #
        instance = None

        if cls.hasInstance():

            instance = cls.__instances__.get(cls.className)

        else:

            instance = cls.creator()

        # Check if weak reference should be returned
        #
        if asWeakReference:

            return instance.weakReference()

        else:

            return instance

    def weakReference(self):
        """
        Returns a weak reference to this instance.

        :rtype: weakref.ref
        """

        return weakref.ref(self)
    # endregion
