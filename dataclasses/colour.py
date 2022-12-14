import math

from dataclasses import dataclass, fields, replace
from six import string_types, integer_types
from six.moves import collections_abc
from ..decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class Colour(collections_abc.Sequence):
    """
    Data class for RGB colours.
    """

    # region Fields
    r: float = 0
    g: float = 0
    b: float = 0
    a: float = 1.0
    # endregion

    # region Dunderscores
    def __post_init__(self):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Validate vector
        #
        if all(isinstance(x, (int, float)) for x in self):

            return

        # Check if sequence was passed to constructor
        #
        arg = self.x

        if hasattr(arg, '__getitem__') and hasattr(arg, '__len__'):

            # Un-package items into vector
            #
            for (i, item) in enumerate(arg):

                self[i] = item

        else:

            raise TypeError(f'__post_init__() expects either an int or float ({type(arg).__name__} given)!')

    def __getitem__(self, key):
        """
        Private method that returns an indexed item.

        :type key: Union[str, int]
        :rtype: float
        """

        # Evaluate key type
        #
        if isinstance(key, string_types):

            return getattr(self, key)

        elif isinstance(key, integer_types):

            dataFields = fields(self.__class__)
            numDataFields = len(dataFields)

            if 0 <= key < numDataFields:

                return getattr(self, dataFields[key].name)

            else:

                raise IndexError('__getitem__() index is out of range!')

        else:

            raise TypeError(f'__getitem__() expects either a str or int ({type(key).__name__} given)!')

    def __setitem__(self, key, value):
        """
        Private method that updates an indexed item.

        :type key: Union[str, int]
        :type value: float
        :rtype: None
        """

        # Evaluate key type
        #
        if isinstance(key, string_types):

            return setattr(self, key, value)

        elif isinstance(key, integer_types):

            dataFields = fields(self.__class__)
            numDataFields = len(dataFields)

            if 0 <= key < numDataFields:

                return setattr(self, dataFields[key].name, value)

            else:

                raise IndexError('__setitem__() index is out of range!')

        else:

            raise TypeError(f'__setitem__() expects either a str or int ({type(key).__name__} given)!')

    def __eq__(self, other):
        """
        Private method that implements the equal operator.

        :type other: Colour
        :rtype: bool
        """

        return self.isEquivalent(other)

    def __ne__(self, other):
        """
        Private method that implements the not equal operator.

        :type other: Colour
        :rtype: bool
        """

        return not self.isEquivalent(other)

    def __neg__(self):
        """
        Private method that implements the inversion operator.

        :rtype: Colour
        """

        return self.inverse()

    def __iter__(self):
        """
        Private method that returns a generator that yields data field values.

        :rtype: Iterator[float]
        """

        return iter((self.r, self.g, self.b, self.a))

    def __len__(self):
        """
        Private method that returns the number of fields belonging to this class.

        :rtype: int
        """

        return 4
    # endregion

    # region Properties
    @classproperty
    def red(cls):
        """
        Getter method that returns the x-axis vector.

        :rtype: Vector
        """

        return Colour(1.0, 0.0, 0.0)

    @classproperty
    def green(cls):
        """
        Getter method that returns the y-axis vector.

        :rtype: Vector
        """

        return Colour(0.0, 1.0, 0.0)

    @classproperty
    def blue(cls):
        """
        Getter method that returns the z-axis vector.

        :rtype: Vector
        """

        return Colour(0.0, 0.0, 1.0)

    @classproperty
    def black(cls):
        """
        Getter method that returns the origin vector.

        :rtype: Vector
        """

        return Colour(0.0, 0.0, 0.0)

    @classproperty
    def white(cls):
        """
        Getter method that returns a one vector.

        :rtype: Vector
        """

        return Colour(1.0, 1.0, 1.0)
    # endregion

    # region Methods
    def hexify(self):
        """
        Converts this colour to a hex string.

        :rtype: str
        """

        return '#{:X}{:X}{:X}'.format(int(self.r * 255.0), int(self.g * 255.0), int(self.b * 255.0))

    def inverse(self):
        """
        Returns an inversed copy of this colour.

        :rtype: Colour
        """

        return Colour(1.0 - self.r, 1.0 - self.g, 1.0 - self.b, self.a)

    def isEquivalent(self, other, tolerance=1e-3):
        """
        Evaluates if the two supplied colours are equivalent.

        :type other: Colour
        :type tolerance: float
        :rtype: bool
        """

        return all(math.isclose(x, y, abs_tol=tolerance) for (x, y) in zip(self, other))

    def copy(self):
        """
        Returns a copy of this colour.

        :rtype: Colour
        """

        return replace(self)

    def toList(self):
        """
        Converts this colour to a list.

        :rtype: List[float]
        """

        return list(self)
    # endregion
