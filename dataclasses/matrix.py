import math
import operator

from functools import reduce
from dataclasses import dataclass
from six import integer_types
from six.moves import collections_abc
from collections import deque
from copy import deepcopy
from ..generators.flatten import flatten

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@dataclass
class Shape:
    """
    Data class for matrix shapes.
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


class Matrix(collections_abc.MutableSequence):
    """
    Data class for transformation matrices.
    """

    # region Dunderscores
    __slots__ = ('_shape', '_rows', '_precision')

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
        self._shape = Shape()
        self._rows = []
        self._precision = kwargs.get('precision', 3)

        # Inspect supplied arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            # Check argument type
            #
            arg = args[0]

            if isinstance(arg, integer_types):

                self.reshape(arg, arg)

            elif isinstance(arg, Shape):

                self.reshape(arg.rows, arg.columns)

            else:

                self.assume(arg)

        elif numArgs == 2:

            self.reshape(args[0], args[1])

        else:

            raise TypeError(f'__init__() expects at least 1 argument ({numArgs} given)!')

    def __str__(self):
        """
        Private method that stringifies this matrix.

        :rtype: str
        """

        return '[{rows}]'.format(rows=',\r'.join(str(tuple(map(lambda number: round(number, self.precision), row))) for row in iter(self)))

    def __getitem__(self, key):
        """
        Private method that returns an indexed item.

        :type key: Union[int, Tuple[int, int]]
        :rtype: Union[float, deque]
        """

        if isinstance(key, integer_types):

            # Check if index is in range
            #
            if 0 <= key < self.shape.rows:

                return self._rows[key]

            else:

                raise IndexError('__getitem__() index is out of range!')

        elif isinstance(key, tuple):

            # Check if co-ordinates are valid
            #
            count = len(key)

            if count != 2:

                raise IndexError(f'__getitem__() expects 2 co-ordinates ({count} given)!')

            # Check if co-ordinates are in range
            #
            row, column = key

            if (0 <= row < self.shape.rows) and (0 <= column < self.shape.columns):

                return self[row][column]

            else:

                raise IndexError('__getitem__() index is out of range!')

        else:

            raise TypeError(f'__getitem__() expects either an int or tuple[int, int] ({type(key).__name__} given)!')

    def __setitem__(self, key, value):
        """
        Private method that updates an indexed item.

        :type key: Union[int, Tuple[int, int]]
        :type value: Union[float, deque]
        :rtype: None
        """

        if isinstance(key, integer_types) and isinstance(value, collections_abc.Sequence):

            # Check if index is in range
            #
            if not (0 <= key < self.shape.rows):

                self._rows[key] = deque(value, maxlen=self.shape.columns)

            else:

                raise IndexError('__setitem__() index is out of range!')

        elif isinstance(key, tuple) and isinstance(value, (int, float)):

            # Check if co-ordinates are valid
            #
            count = len(key)

            if count != 2:

                raise IndexError(f'__setitem__() expects 2 co-ordinates ({count} given)!')

            # Check if co-ordinates are in range
            #
            row, column = key

            if (0 <= row < self.shape.rows) and (0 <= column < self.shape.columns):

                self[row][column] = value

            else:

                raise IndexError('__setitem__() index is out of range!')

        else:

            raise TypeError(f'__setitem__() expects either a str or int ({type(key).__name__} given)!')

    def __delitem__(self, key):
        """
        Private method that deletes an indexed item.

        :type key: Union[int, Tuple[int, int]]
        :rtype: None
        """

        pass

    def __mul__(self, other):
        """
        Private method that implements the multiplication operator.

        :type other: Union[float, Matrix]
        :rtype: Matrix
        """

        copy = deepcopy(self)
        copy *= other

        return copy

    def __imul__(self, other):
        """
        Private method that implements the in-place multiplication operator.

        :type other: Union[float, Matrix]
        :rtype: Matrix
        """

        # Evaluate other value type
        #
        if isinstance(other, Matrix):

            # Check if matrices are compatible
            #
            if self.shape != other.shape:

                raise TypeError('__imul__() expects a valid matrix shape!')

            # Perform matrix multiplication
            #
            matrix = deepcopy(self)

            for row in range(self.shape.rows):

                for column in range(self.shape.columns):

                    self[row, column] = sum(matrix[row, i] * other[i, column] for i in range(self.shape.columns))

        elif isinstance(other, (int, float)):

            # Multiple all items
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

        return iter(self._rows)

    def __len__(self):
        """
        Private method that returns the number of fields belonging to this class.

        :rtype: int
        """

        return self.shape.rows
    # endregion

    # region Properties
    @property
    def shape(self):
        """
        Getter method that returns the shape configuration for this matrix.

        :rtype: Shape
        """

        return self._shape

    @property
    def precision(self):
        """
        Getter method that returns the number of digits this matrix rounds to.

        :rtype: int
        """

        return self._precision
    # endregion

    # region Methods
    def insert(self, index, value):
        """
        Inserts a row into this matrix.

        :type index: int
        :type value: List[float]
        :rtype: Matrix
        """

        return self

    def reshape(self, rowCount, columnCount):
        """
        Reshapes this matrix to the specified size.

        :type rowCount: int
        :type columnCount: int
        :rtype: Matrix
        """

        self._shape = Shape(rowCount, columnCount)
        self._rows = deque(map(lambda i: deque([0.0] * columnCount, maxlen=columnCount), range(rowCount)), maxlen=rowCount)

        return self

    def assume(self, array):
        """
        Copies the shape and values to this matrix.

        :type array: List[float]
        :rtype: Matrix
        """

        # Check if there are enough rows
        #
        numRows = len(array)

        if numRows == 0:

            raise TypeError(f'assume() expects at least 1 row ({numRows} given)!')

        # Check if all items are valid
        #
        numColumns = len(array[0])
        isValid = all([len(row) == numColumns and all([isinstance(number, (int, float)) for number in row]) for row in array])

        if not isValid:

            raise TypeError('assume() expects identical length columns!')

        # Reshape matrix and fill
        #
        self.reshape(numRows, numColumns)
        self.fill(array)

        return self

    def fill(self, array):
        """
        Fills this matrix with the supplied array.

        :type array: List[float]
        :rtype: Matrix
        """

        # Check if there are enough values
        #
        numItems = len(array)
        size = self.shape.rows * self.shape.columns

        if numItems > size:

            raise TypeError(f'fill() expects at most {size} values ({numItems} given)!')

        # Populate arrays
        #
        for (i, value) in enumerate(flatten(array)):

            row, column = divmod(i, self.shape.columns)
            self[row, column] = value

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

        for row in range(self.shape.rows):

            for column in range(self.shape.columns):

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

        for row in range(self.shape.rows):

            for column in range(self.shape.columns):

                minor = self.minor(row, column)
                adjugate[row, column] = minor.cofactor()

        return adjugate.transpose()

    def inverse(self):
        """
        Returns the inverse of this matrix.

        :rtype: Matrix
        """

        determinant = 1.0 / abs(self.determinant())
        inverse = self.adjugate() * determinant

        return inverse

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
    # endregion
