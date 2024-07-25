import math
import operator

from functools import reduce
from itertools import islice
from dataclasses import dataclass
from collections import deque
from collections.abc import Sequence, Mapping
from . import adc
from ..generators.flatten import flatten

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class Shape(adc.ADC):
    """
    Overload of `ADC` that interfaces with matrix shape data.
    """

    # region Fields
    rows: int = 0
    columns: int = 0
    # endregion

    # region Dunderscores
    def __eq__(self, other):
        """
        Private method that implements the equal operator.

        :type other: Shape
        :rtype: bool
        """

        return self.rows == other.rows and self.columns == other.columns

    def __ne__(self, other):
        """
        Private method that implements the equal operator.

        :type other: Shape
        :rtype: bool
        """

        return self.rows != other.rows or self.columns != other.columns
    # endregion

    # region Methods
    @classmethod
    def detect(cls, array):
        """
        Returns the shape configuration from the supplied array.

        :type array: Any
        :rtype: Shape
        """

        isFlat = all(isinstance(item, (float, int)) for item in array)
        isNested = all(isinstance(item, (Sequence, Mapping)) for item in array)

        if isFlat:

            return cls(1, len(array))

        elif isNested:

            columns = len(array[0])
            isConsistent = all(len(item) == columns for item in array)

            if isConsistent:

                return cls(len(array), columns)

            else:

                raise TypeError('detect() expects consistent column sizes!')

        else:

            raise TypeError('detect() expects consistent item types!')
    # endregion


class Matrix(Sequence):
    """
    Data class for matrices.
    """

    # region Dunderscores
    __slots__ = ('__shape__', '__rows__', '__precision__')
    __decimals__ = 6

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :type args: Union[int, Tuple[int, int], List[list[float]]]
        :rtype: None
        """

        # Call parent method
        #
        super(Matrix, self).__init__()

        # Declare private variables
        #
        self.__shape__ = Shape()
        self.__rows__ = deque(maxlen=0)
        self.__precision__ = kwargs.get('precision', 3)

        # Inspect supplied arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            # Check argument type
            #
            arg = args[0]

            if isinstance(arg, int):

                self.reshape(Shape(arg, arg))

            elif isinstance(arg, Shape):

                self.reshape(arg)

            elif isinstance(arg, (Sequence, Mapping)):

                self.assume(arg)

            else:

                raise TypeError(f'__init__() expects either an int or Shape ({type(arg).__name__} given)!')

        elif numArgs == 2:

            # Check argument types
            #
            rows, columns = args

            if isinstance(rows, int) and isinstance(columns, int):

                self.reshape(Shape(*args))

            else:

                raise TypeError(f'__init__() expects a pair of integers!')

        else:

            raise TypeError(f'__init__() expects either 1 or 2 arguments ({numArgs} given)!')

    def __repr__(self):
        """
        Private method that returns a string representation of this matrix.

        :rtype: str
        """

        return self.toString()

    def __str__(self):
        """
        Private method that stringifies this matrix.

        :rtype: str
        """

        return self.toString()

    def __getitem__(self, key):
        """
        Private method that returns an indexed item.

        :type key: Union[int, Tuple[int, int]]
        :rtype: Union[float, deque]
        """

        if isinstance(key, int):

            # Check if index is in range
            #
            if 0 <= key < self.shape.rows:

                return self.__rows__[key]

            else:

                raise IndexError('__getitem__() index is out of range!')

        elif isinstance(key, tuple):

            # Check if co-ordinates are valid
            #
            count = len(key)

            if count != 2:

                raise IndexError(f'__getitem__() expects 2 co-ordinates ({count} given)!')

            # Get matrix row and evaluate column type
            #
            rowIndex, columnIndex = key
            row = self.__getitem__(rowIndex)

            if isinstance(columnIndex, int):

                return round(row[columnIndex], self.__decimals__)

            elif isinstance(columnIndex, slice):

                return tuple(round(column, self.__decimals__) for column in islice(row, columnIndex.start, columnIndex.stop, columnIndex.step))

            else:

                raise TypeError('__getitem__() expects an int or slice ({type(key).__name__} given)!')

        else:

            raise TypeError(f'__getitem__() expects either an int or tuple[int, int] ({type(key).__name__} given)!')

    def __setitem__(self, key, value):
        """
        Private method that updates an indexed item.

        :type key: Union[int, Tuple[int, int]]
        :type value: Union[float, deque]
        :rtype: None
        """

        if isinstance(key, tuple) and isinstance(value, (int, float)):

            # Check if co-ordinates are valid
            #
            count = len(key)

            if count != 2:

                raise IndexError(f'__setitem__() expects 2 co-ordinates ({count} given)!')

            # Check if value is valid
            #
            if not isinstance(value, (int, float)):

                raise TypeError(f'__setitem__() expects a number ({type(value).__name__} given)!')

            # Check if co-ordinates are in range
            #
            row, column = key

            if (0 <= row < self.shape.rows) and (0 <= column < self.shape.columns):

                self.__rows__[row][column] = value

            else:

                raise IndexError('__setitem__() index is out of range!')

        elif isinstance(key, int) and isinstance(value, (Sequence, Mapping)):

            # Check if index is in range
            #
            if not (0 <= key < self.shape.rows):

                raise IndexError('__setitem__() index is out of range!')

            # Replace row elements
            #
            for (column, item) in enumerate(value):

                self[key][column] = item

        else:

            raise TypeError(f'__setitem__() expects either a str or int ({type(key).__name__} given)!')

    def __eq__(self, other):
        """
        Private method that implements the equal operator.

        :type other: Matrix
        :rtype: bool
        """

        return self.isEquivalent(other)

    def __ne__(self, other):
        """
        Private method that implements the not equal operator.

        :type other: Matrix
        :rtype: bool
        """

        return not self.isEquivalent(other)

    def __add__(self, other):
        """
        Private method that implements the addition operator.

        :type other: Matrix
        :rtype: Matrix
        """

        copy = self.copy()
        copy += other

        return copy

    def __iadd__(self, other):
        """
        Private method that implements the in-place addition operator.

        :type other: Matrix
        :rtype: Matrix
        """

        # Check if matrices are compatible
        #
        if self.shape != other.shape:

            raise TypeError('__iadd__() mismatched matrix dimensions!')

        # Perform matrix addition
        #
        for row in range(self.shape.rows):

            for column in range(self.shape.columns):

                self[row, column] += other[row, column]

        return self

    def __sub__(self, other):
        """
        Private method that implements the subtraction operator.

        :type other: Matrix
        :rtype: Matrix
        """

        copy = self.copy()
        copy -= other

        return copy

    def __isub__(self, other):
        """
        Private method that implements the in-place subtraction operator.

        :type other: Matrix
        :rtype: Matrix
        """

        # Check if matrices are compatible
        #
        if self.shape != other.shape:

            raise TypeError('__isub__() mismatched matrix dimensions!')

        # Perform matrix subtraction
        #
        for row in range(self.shape.rows):

            for column in range(self.shape.columns):

                self[row, column] -= other[row, column]

        return self

    def __mul__(self, other):
        """
        Private method that implements the multiplication operator.

        :type other: Union[float, Matrix]
        :rtype: Matrix
        """

        # Evaluate other value type
        #
        if isinstance(other, Matrix):

            # Check if matrices are compatible
            #
            if self.shape.rows != other.shape.columns:

                raise TypeError('__mul__() mismatched matrix dimensions!')

            # Perform matrix multiplication
            #
            matrix = self.__class__(self.shape.rows, other.shape.columns)

            for row in range(self.shape.rows):

                for column in range(other.shape.columns):

                    matrix[row, column] = sum(self[row, i] * other[i, column] for i in range(self.shape.columns))

            return matrix

        elif isinstance(other, (int, float)):

            # Multiply elements by number
            #
            copy = self.copy()
            copy *= other

            return copy

        else:

            raise TypeError(f'__mul__() expects a float or matrix ({type(other).__name__} given)!')

    def __imul__(self, other):
        """
        Private method that implements the in-place multiplication operator.

        :type other: Union[float, Matrix]
        :rtype: Matrix
        """

        # Evaluate other value type
        #
        if isinstance(other, Matrix):

            # Copy values from multiplied matrix
            #
            matrix = self * other
            return self.assume(matrix)

        elif isinstance(other, (int, float)):

            # Multiply elements by number
            #
            for row in range(self.shape.rows):

                for column in range(self.shape.columns):

                    self[row, column] *= other

        else:

            raise TypeError(f'__imul__() expects a float or matrix ({type(other).__name__} given)!')

        return self

    def __neg__(self):
        """
        Private method that implements the invert operator.

        :rtype: Matrix
        """

        return self.inverse()

    def __iter__(self):
        """
        Private method that returns a generator that yields data field values.

        :rtype: Iterator[deque]
        """

        return iter(self.__rows__)

    def __len__(self):
        """
        Private method that returns the number of fields belonging to this class.

        :rtype: int
        """

        return self.shape.rows

    def __copy__(self):
        """
        Private method that returns a copy of this matrix.

        :rtype: Matrix
        """

        return self.copy()
    # endregion

    # region Properties
    @property
    def shape(self):
        """
        Getter method that returns the shape configuration for this matrix.

        :rtype: Shape
        """

        return self.__shape__

    @shape.setter
    def shape(self, shape):
        """
        Setter method that updates the shape configuration for this matrix.

        :type shape: Shape
        :rtype: None
        """

        self.reshape(shape)

    @property
    def precision(self):
        """
        Getter method that returns the number of digits this matrix rounds to.

        :rtype: int
        """

        return self.__precision__

    @precision.setter
    def precision(self, precision):
        """
        Setter method that returns the number of digits this matrix rounds to.

        :type precision: int
        :rtype: None
        """

        self.__precision__ = precision
    # endregion

    # region Methods
    def walk(self):
        """
        Returns a generator that yields row-column co-ordinates to elements in this matrix.

        :rtype: Iterator[Tuple[int, int]]
        """

        for row in range(self.shape.rows):

            for column in range(self.shape.columns):

                yield row, column

    def zip(self, other):
        """
        Returns a generator that yields elements from both matrices as pairs.

        :type other: Matrix
        :rtype: Iterator[Tuple[float, float]]
        """

        # Check if matrices are compatible
        #
        if self.shape != other.shape:

            raise TypeError('zip() mismatched matrix dimensions!')

        # Yield matrix element pairs
        #
        for row in range(self.shape.rows):

            for column in range(self.shape.columns):

                yield self[row, column], other[row, column]

    def diagonal(self, column, reverse=False):
        """
        Returns a generator that yields the co-ordinates along the diagonal starting from the specified column.

        :type column: int
        :type reverse: bool
        :rtype: Iterator[Tuple[int, int]]
        """

        # Check if column is in range
        #
        if not (0 <= column < self.shape.columns):

            raise IndexError('diagonal() index is out of range!')

        # Check which direction to yield
        #
        if reverse:

            for row in range(self.shape.rows):

                yield row, (column - row) % self.shape.columns

        else:

            for row in range(self.shape.rows):

                yield row, (column + row) - (self.shape.columns * ((column + row) // self.shape.columns))

    def reshape(self, *args):
        """
        Reshapes this matrix to the specified size.

        :type args: Union[int, Tuple[int, int], Shape]
        :rtype: Matrix
        """

        # Inspect arguments
        #
        shape = None
        numArgs = len(args)

        if numArgs == 1:

            # Evaluate argument
            #
            arg = args[0]

            if isinstance(arg, Shape):

                shape = arg

            elif isinstance(arg, int):

                shape = Shape(arg, arg)

            else:

                raise TypeError(f'reshape() expects either an int or Shape ({type(arg).__name__} given)!')

        elif numArgs == 2:

            shape = Shape(*args)

        else:

            raise TypeError(f'reshape() expects 1-2 arguments ({numArgs} given)!')

        # Check if reshape is required
        #
        if self.shape.rows != shape.rows or self.shape.columns != shape.columns:

            self.__shape__ = shape
            self.__rows__ = deque(map(lambda i: deque([0.0] * shape.columns, maxlen=shape.columns), range(shape.rows)), maxlen=shape.rows)

        return self

    def fill(self, array, shape=None):
        """
        Fills this matrix with the supplied array.
        The `shape` keyword argument exists purely for optimization purposes.

        :type array: List[float]
        :type shape: Shape
        :rtype: Matrix
        """

        # Check if a shape was supplied
        #
        if shape is None:

            shape = Shape.detect(array)

        # Evaluate array configuration
        #
        if shape.rows == 1:

            # Check if matrix is large enough
            #
            size = self.shape.rows * self.shape.columns

            if shape.columns > size:

                raise TypeError(f'fill() expects at most {size} values ({shape.columns} given)!')

            # Populate arrays
            #
            for (i, value) in enumerate(array):

                row, column = divmod(i, self.shape.columns)
                self[row, column] = value

            return self

        else:

            # Check if matrix is large enough
            #
            if shape.rows > self.shape.rows:

                raise TypeError(f'fill() expects at most {self.shape.rows} rows ({shape.rows} given)!')

            elif shape.columns > self.shape.columns:

                raise TypeError(f'fill() expects at most {self.shape.columns} columns ({shape.columns} given)!')

            else:

                pass

            # Populate rows
            #
            for (row, item) in enumerate(array):

                for (column, value) in enumerate(item):

                    self[row, column] = value

            return self

    def assume(self, array):
        """
        Copies the shape and values to this matrix.

        :type array: List[float]
        :rtype: Matrix
        """

        shape = Shape.detect(array)
        self.reshape(shape.rows, shape.columns)

        return self.fill(array, shape=shape)

    @classmethod
    def identity(cls, size):
        """
        Returns an identity matrix with the specified size.

        :type size: int
        :rtype: Matrix
        """

        return cls(size, size).identitize()

    def identitize(self):
        """
        Replaces the elements along the diagonal with ones.
        All other elements will revert to zeroes.

        :rtype: Matrix
        """

        for (row, column) in self.walk():

            if row == column:

                self[row, column] = 1.0

            else:

                self[row, column] = 0.0

        return self

    def minor(self, row, column):
        """
        Returns the minor matrix for the specified row and column.

        :type row: int
        :type column: int
        :rtype: Matrix
        """

        rows = [x for x in range(self.shape.rows) if x != row]
        rowCount = len(rows)

        columns = [x for x in range(self.shape.columns) if x != column]
        columnCount = len(columns)

        minor = Matrix(rowCount, columnCount)

        for (physicalRow, logicalRow) in enumerate(rows):

            for (physicalColumn, logicalColumn) in enumerate(columns):

                minor[physicalRow, physicalColumn] = self[logicalRow, logicalColumn]

        return minor

    def cofactor(self):
        """
        Returns the cofactor expansion of this matrix.

        :rtype: float
        """

        cofactor = 0.0

        for column in range(self.shape.columns):

            cofactor += reduce(operator.mul, tuple(map(lambda coords: self[coords], self.diagonal(column))))

        for column in reversed(range(self.shape.columns)):

            cofactor -= reduce(operator.mul, tuple(map(lambda coords: self[coords], self.diagonal(column, reverse=True))))

        return cofactor

    def determinant(self):
        """
        Returns the determinant of this matrix.
        See the following for details: https://semath.info/src/determinant-four-by-four.html

        :rtype: float
        """

        determinant = 0.0

        for row in range(self.shape.rows):

            minor = self.minor(row, 0)
            cofactor = minor.cofactor()

            if (row % 2) == 0:

                determinant += self[row, 0] * cofactor

            else:

                determinant -= self[row, 0] * cofactor

        return determinant

    def transpose(self):
        """
        Returns the transpose of this matrix.
        This process involves flipping this matrix over its diagonal.

        :rtype: Matrix
        """

        transpose = Matrix(self.shape.columns, self.shape.rows)

        for (row, column) in self.walk():

            transpose[column, row] = self[row, column]

        return transpose

    def adjugate(self):
        """
        Returns the adjugate of this matrix.
        This process involves finding the cofactor for each element's minor before finally transposing the end result.
        See the following for details: https://semath.info/src/inverse-cofactor-ex4.html

        :rtype: Matrix
        """

        adjugate = Matrix(self.shape)

        for (row, column) in self.walk():

            minor = self.minor(column, row)
            sign = 1.0 if ((row + column) % 2 == 0) else -1.0

            adjugate[row, column] = minor.cofactor() * sign

        return adjugate

    def inverse(self):
        """
        Returns the inverse of this matrix.

        :rtype: Matrix
        """

        determinant = 1.0 / self.determinant()
        inverse = self.adjugate() * determinant

        return inverse

    def isEquivalent(self, other, tolerance=1e-3):
        """
        Evaluates if the two supplied matrices are equivalent.

        :type other: Matrix
        :type tolerance: float
        :rtype: bool
        """

        # Check if matrices are compatible
        #
        if self.shape == other.shape:

            return all(math.isclose(x, y, abs_tol=tolerance) for (x, y) in self.zip(other))

        else:

            return False

    def copy(self):
        """
        Returns a copy of this matrix.

        :rtype: Matrix
        """

        matrix = self.__class__(self.shape)
        matrix.fill(self, shape=self.shape)

        return matrix

    def toList(self, collapse=False):
        """
        Converts this matrix to a list.

        :type collapse: bool
        :rtype: List[List[float]]
        """

        if collapse:

            return list(flatten(self))

        else:

            return list(map(list, self))

    def toString(self):
        """
        Returns a string representation of this matrix.

        :rtype: str
        """

        return '[{rows}]'.format(rows=',\r'.join(str(tuple(map(lambda number: round(number, self.precision), row))) for row in iter(self)))
    # endregion
