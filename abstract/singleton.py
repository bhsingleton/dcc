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
    def getInstance(cls):
        """
        Returns an instance of this class.

        :rtype: Singleton
        """

        return cls.__instances__.get(cls.className)

    def weakReference(self):
        """
        Returns a weak reference to this instance.

        :rtype: weakref.ref
        """

        return weakref.ref(self)
    # endregion
