import sys
import numpy

from PySide2 import QtCore, QtWidgets, QtGui
from dcc.userinterface import qlineeditgroup

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QMatrixEdit(QtWidgets.QWidget):
    """
    Overload of QWidget used to edit transform matrices.
    """

    cellEdited = QtCore.Signal(int, int)
    cellChanged = QtCore.Signal(int, int)

    # region Dunderscores
    __decimals__ = 3

    def __init__(self, rows, columns, parent=None):
        """
        Private method called after a new instance has been created.

        :type parent: QtWidgets.QWidget
        :rtype: None
        """

        # Call parent method
        #
        super(QMatrixEdit, self).__init__(parent=parent)

        # Declare private variables
        #
        self._rowCount = rows
        self._columnCount = columns
        self._rows = [None] * rows
        self._validator = self.initializeValidator()

        # Initialize matrix rows
        #
        self.setLayout(QtWidgets.QGridLayout())

        for row in range(columns):

            self._rows[row] = self.initializeRow(self.layout(), row, columns=columns)
    # endregion

    # region Methods
    def validator(self):
        """
        Returns the validator used by the matrix line edits.

        :rtype: QtGui.QDoubleValidator
        """

        return self._validator

    def rowCount(self):
        """
        Returns the number of rows in this matrix.

        :rtype: int
        """

        return self._rowCount

    def columnCount(self):
        """
        Returns the number of columns in this matrix.

        :rtype: int
        """

        return self._columnCount

    def rows(self):
        """
        Returns a list of line edit groups.

        :rtype: list[qlineeditgroup.QLineEditGroup]
        """

        return self._rows

    def columns(self, row):
        """
        Returns a group of line edits from the specified row.

        :type row: int
        :rtype: qlineeditgroup.QLineEditGroup
        """

        return self.rows()[row]

    def matrix(self):
        """
        Returns the displayed matrix.

        :rtype: numpy.matrix
        """

        matrix = numpy.matrix(numpy.zeros((4, 4)))

        for row in range(self.rowCount()):

            columns = self.columns(row)

            for column in range(self.columnCount()):

                matrix[row, column] = float(columns.lineEdit(column).text())

        return matrix

    def setMatrix(self, matrix):
        """
        Updates the displayed matrix.

        :type matrix: numpy.matrix
        :rtype: None
        """

        for row in range(self.rowCount()):

            columns = self.columns(row)

            for column in range(self.columnCount()):

                text = str(round(matrix[row, column], self.__decimals__))
                columns.lineEdit(column).setText(text)

    def initializeValidator(self):
        """
        Initializes a line edit validator.

        :rtype: QtGui.QDoubleValidator
        """

        validator = QtGui.QDoubleValidator(-sys.float_info.max, sys.float_info.max, self.__decimals__, self)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)

        return validator

    def initializeRow(self, layout, row, columns=4):
        """
        Initializes a matrix row using the supplied layout.

        :type layout: QtWidgets.QGridLayout
        :type row: int
        :type columns: int
        :rtype: qlineeditgroup.QLineEditGroup
        """

        # Create line edit group
        #
        lineEditGroup = qlineeditgroup.QLineEditGroup(parent=self)
        lineEditGroup.lineEditTextEdited.connect(self.cell_textEdited)
        lineEditGroup.lineEditTextChanged.connect(self.cell_textChanged)

        for column in range(columns):

            lineEdit = QtWidgets.QLineEdit('0.0', parent=self)
            lineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            lineEdit.setFixedHeight(24)
            lineEdit.setAlignment(QtCore.Qt.AlignCenter)
            lineEdit.setValidator(self._validator)
            lineEdit.setReadOnly(True)

            lineEditGroup.addLineEdit(lineEdit, id=column)
            layout.addWidget(lineEdit, row, column)

        return lineEditGroup
    # endregion

    # region Slots
    def cell_textEdited(self, column):
        """
        Text edited slot method responsible for emitting the cell edited signal.
        This does not include calls made to QLineEdit.setText().

        :type row: int
        :type column: int
        :rtype: None
        """

        lineEditGroup = self.sender()
        row = self.rows().index(lineEditGroup)

        self.cellEdited.emit(row, column)

    def cell_textChanged(self, column):
        """
        Text edited slot method responsible for emitting the cell changed signal.
        This includes calls made to QLineEdit.setText().

        :type column: int
        :rtype: None
        """

        lineEditGroup = self.sender()
        row = self.rows().index(lineEditGroup)

        self.cellChanged.emit(row, column)
    # endregion
