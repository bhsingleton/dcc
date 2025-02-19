import inspect

from abc import abstractmethod
from . import singleton
from ..python import importutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ProxyFactory(singleton.Singleton):
    """
    Overload of `Singleton` that outlines the behavior for factory interfaces.
    """

    # region Dunderscores
    __slots__ = ('__classes__',)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(ProxyFactory, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self.__classes__ = dict(self.iterClassesFromPackage(*self.packages()))

    def __iter__(self):
        """
        Private method that returns a generator that yields all available classes.

        :rtype: iter
        """

        return self.iterClassesFromPackage(*self.packages())

    def __getitem__(self, key):
        """
        Private method that returns an indexed item.

        :type key: Union[int, str]
        :rtype: type
        """

        return self.getClass(key)

    def __len__(self):
        """
        Private method that evaluates the number of classes belonging to this factory.

        :rtype: int
        """

        pass
    # endregion

    # region Methods
    @abstractmethod
    def packages(self):
        """
        Returns a list of packages to be inspected for classes.

        :rtype: List[module]
        """

        pass

    @abstractmethod
    def classFilter(self):
        """
        Returns the base class used to filter out objects when searching for classes.

        :rtype: class
        """

        pass

    def classAttr(self):
        """
        Returns the attribute name to be used to organize the class dictionary.
        By default, this is set to '__name__' but you can change this to whatever you want.

        :rtype: str
        """

        return '__name__'

    def classes(self):
        """
        Returns a dictionary of classes that can be instantiated.
        The structure of this dictionary is dictated by the classAttr method!

        :rtype: Dict[str, type]
        """

        return self.__classes__

    def getClass(self, key):
        """
        Returns a class constructor based on the supplied key.

        :type key: Union[str, int]
        :rtype: class
        """

        return self.__classes__.get(key, None)

    def iterClassesFromModule(self, *modules, **kwargs):
        """
        Returns a generator that yields the classes from the supplied modules.
        Optional keywords can be used to override the factory defaults.

        :key classAttr: str
        :key classFilter: type
        :rtype: Iterator[type]
        """

        # Iterate through arguments
        #
        classAttr = kwargs.get('classAttr', self.classAttr())
        classFilter = kwargs.get('classFilter', self.classFilter())

        for module in modules:

            # Check if this is a module
            #
            if not inspect.ismodule(module):

                continue

            # Iterate through module items
            #
            for (name, cls) in importutils.iterClasses(module, classFilter=classFilter):

                # Check if class has required key identifier
                #
                if not hasattr(cls, classAttr):

                    log.info(f'Skipping class: {cls}')
                    continue

                # Yield key-value pair
                #
                key = getattr(cls, classAttr)

                if isinstance(key, (tuple, list)):

                    for item in key:

                        yield item, cls

                else:

                    yield key, cls

    def iterClassesFromPackage(self, *packages, **kwargs):
        """
        Returns a generator that yields the classes from the supplied packages.
        Optional keywords can be used to override the factory defaults.

        :rtype: Iterator[module]
        """

        # Iterate through arguments
        #
        for package in packages:

            # Check if this is a package
            #
            if not inspect.ismodule(package):

                continue

            # Iterate through modules
            #
            modules = list(importutils.iterModules(package))

            for (key, cls) in self.iterClassesFromModule(*modules, **kwargs):

                yield key, cls
    # endregion
