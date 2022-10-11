from abc import ABCMeta, abstractmethod
from six import with_metaclass

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AbstractDecorator(with_metaclass(ABCMeta, object)):
    """
    Abstract base class used to standardize decorator behavior.
    This pattern can also be used alongside 'with' statements.
    """

    # region Dunderscores
    __slots__ = ('_instance', '_owner', '_func')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(AbstractDecorator, self).__init__()

        # Declare public variables
        #
        self._instance = None
        self._owner = None
        self._func = None

        # Inspect arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            self._func = args[0]

    def __get__(self, instance, owner):
        """
        Private method called whenever this object is accessed via attribute lookup.

        :type instance: object
        :type owner: Type[AbstractDecorator]
        :rtype: AbstractDecorator
        """

        self._instance = instance
        self._owner = owner

        return self

    def __call__(self, *args, **kwargs):
        """
        Private method that is called whenever this instance is evoked.

        :rtype: Any
        """

        # Execute order of operations
        #
        self.__enter__(*args, **kwargs)
        results = self.func(*args, **kwargs)
        self.__exit__(None, None, None)

        return results

    @abstractmethod
    def __enter__(self, *args, **kwargs):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Private method that is called when this instance is exited using a with statement.

        :type exc_type: Any
        :type exc_val: Any
        :type exc_tb: Any
        :rtype: None
        """

        pass
    # endregion

    # region Properties
    @property
    def instance(self):
        """
        Returns the instance currently bound to this decorator.

        :rtype: object
        """

        return self._instance

    @property
    def owner(self):
        """
        Returns the class associated with the bound instance.

        :rtype: Type[AbstractDecorator]
        """

        return self._owner

    @property
    def func(self):
        """
        Getter method used to return the wrapped function.
        If this is a descriptor object then the function will be bound to the instance.

        :rtype: Callable
        """

        if self._instance is not None:

            return self._func.__get__(self._instance, self._owner)

        else:

            return self._func
    # endregion
