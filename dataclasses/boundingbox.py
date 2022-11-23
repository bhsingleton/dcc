import math

from dataclasses import dataclass, fields, field, replace
from six import string_types, integer_types
from . import vector

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class BoundingBox:
    """
    Data class for bounding boxes.
    """

    # region Fields
    min: vector.Vector = field(default_factory=lambda: vector.Vector.one)
    max: vector.Vector = field(default_factory=lambda: -vector.Vector.one)
    # endregion

    # region Dunderscores
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

    def __contains__(self, point):
        """
        Private method that implements the `in` operator.

        :type point: vector.Vector
        :rtype: bool
        """

        return self.contains(point)
    # endregion

    # region Methods
    def width(self):
        """
        Returns the width of this bounding box.

        :rtype: float
        """

        return abs((self.max - self.min).x)

    def height(self):
        """
        Returns the height of this bounding box.

        :rtype: float
        """

        return abs((self.max - self.min).y)

    def depth(self):
        """
        Returns the depth of this bounding box.

        :rtype: float
        """

        return abs((self.max - self.min).z)

    def center(self):
        """
        Returns the center of this bounding box.

        :rtype: vector.Vector
        """

        return (self.min * 0.5) + (self.max * 0.5)

    def contains(self, point):
        """
        Evaluates if the supplied point is inside this bounding box.

        :type point: vector.Vector
        :rtype: bool
        """

        return self.min <= point <= self.max
    # endregion
