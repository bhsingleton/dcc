import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ClassProperty(object):
    """
    Base class used to decorate class properties.
    See the following for details:
    https://stackoverflow.com/questions/5189699/how-to-make-a-class-property
    """

    __slots__ = ('fget', 'fset', 'fdel')

    def __init__(self, fget, fset=None, fdel=None):
        """
        Private method called after a new instance has been created.

        :type fget: function
        :type fset: function
        :type fdel: function
        :rtype: None
        """

        # Call parent method
        #
        super(ClassProperty, self).__init__()

        # Declare class variables
        #
        self.fget = fget
        self.fset = fset
        self.fdel = fdel

    def __get__(self, instance, owner):
        """
        Private method called whenever the user attempts to get a value.

        :type instance: object
        :type owner: class
        :rtype: Any
        """

        # Check if owner was supplied
        #
        if owner is None:

            owner = type(instance)

        return self.fget.__get__(instance, owner)()

    def __set__(self, instance, value):
        """
        Dunderscore method called whenever the user attempts to update a property.

        :type instance: object
        :type value: Any
        :rtype: None
        """

        # Check if setter exists
        #
        if not self.fset:

            raise AttributeError("can't set attribute")

        return self.fset.__get__(instance, type(instance))(value)

    def __delete__(self, instance):
        """
        Dunderscore method called whenever the user attempts to delete a property.

        :type instance: object
        :rtype: None
        """

        # Check if setter exists
        #
        if not self.fdel:

            raise AttributeError("can't delete attribute")

        return self.fdel.__get__(instance, type(instance))()

    def setter(self, func):
        """
        Decorator hook used to override the setter function.

        :type func: function
        :rtype: object
        """

        # Check if function needs classmethod wrapper
        #
        if not isinstance(func, classmethod):

            func = classmethod(func)

        # Update fset function
        #
        self.fset = func
        return self

    def deleter(self, func):
        """
        Decorator hook used to override the delete function.

        :type func: function
        :rtype: object
        """

        # Check if function needs classmethod wrapper
        #
        if not isinstance(func, classmethod):

            func = classmethod(func)

        # Update fset function
        #
        self.fdel = func
        return self


def classproperty(func):
    """
    Returns a class property object to be used as a decorator.

    :type func: method
    :rtype: ClassProperty
    """

    # Check if function needs classmethod wrapper
    #
    if not isinstance(func, classmethod):

        func = classmethod(func)

    return ClassProperty(func)
