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

    readOnlyChanged = QtCore.Signal(bool)
    validatorChanged = QtCore.Signal(QtGui.QValidator)
    cellEdited = QtCore.Signal(int, int)
    cellChanged = QtCore.Signal(int, int)
    matrixChanged = QtCore.Signal(numpy.matrix)

    # region Dunderscores
    __decimals__ = 3

    def __init__(self, rowCount, columnCount, parent=None):
        """
        Private method called after a new instance has been created.

        :type rowCount: int
        :type columnCount: int
        :type parent: QtWidgets.QWidget
        :rtype: None
        """

        # Call parent method
        #
        super(QMatrixEdit, self).__init__(parent=parent)

        # Declare private variables
        #
        self._rowCount = rowCount
        self._columnCount = columnCount
        self._readOnly = False
        self._validator = self.defaultValidator()
        self._rows = [None] * self._rowCount

        # Initialize matrix rows
        #
        gridLayout = QtWidgets.QGridLayout()

        for row in range(self._rowCount):

            self._rows[row] = self.createLineEditGroup(self._columnCount)

            for column in range(self._columnCount):

                gridLayout.addWidget(self._rows[row][column], row, column)

        self.setLayout(gridLayout)
    # endregion

    # region Methods
    def readOnly(self):
        """
        Returns the read-only state.

        :rtype: bool
        """

        return self._readOnly

    def setReadOnly(self, readOnly):
        """
        Updates the read-only state.

        :type readOnly: bool
        :rtype: None
        """

        self._readOnly = readOnly
        self.readOnlyChanged.emit(self._readOnly)

    def validator(self):
        """
        Returns the validator used by the matrix line edits.

        :rtype: QtGui.QDoubleValidator
        """

        return self._validator

    def defaultValidator(self):
        """
        Returns the default line edit validator.

        :rtype: QtGui.QDoubleValidator
        """

        validator = QtGui.QDoubleValidator(-sys.float_info.max, sys.float_info.max, self.__decimals__, self)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)

        return validator

    def setValidator(self, validator):
        """
        Updates the validator used by the matrix line edits.

        :rtype: QtGui.QDoubleValidator
        """

        self._validator = validator
        self.validatorChanged.emit(self._validator)

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
        Returns the current matrix.

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
        Updates the current matrix.

        :type matrix: numpy.matrix
        :rtype: None
        """

        for row in range(self.rowCount()):

            columns = self.columns(row)

            for column in range(self.columnCount()):

                text = str(round(matrix[row, column], self.__decimals__))
                columns.lineEdit(column).setText(text)

        self.matrixChanged.emit(self.matrix())

    def createLineEdit(self):
        """
        Returns a line edit with all of the necessary connections.

        :rtype: QtWidgets.QLineEdit
        """

        lineEdit = QtWidgets.QLineEdit('0.0')
        lineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        lineEdit.setFixedHeight(24)
        lineEdit.setAlignment(QtCore.Qt.AlignCenter)
        lineEdit.setValidator(self._validator)
        lineEdit.setReadOnly(self._readOnly)

        self.readOnlyChanged.connect(lineEdit.setReadOnly)
        self.validatorChanged.connect(lineEdit.setValidator)

    def createLineEditGroup(self, columnCount):
        """
        Returns a line edit group based on the number of columns.

        :type columnCount: int
        :rtype: qlineeditgroup.QLineEditGroup
        """

        # Create line edit group
        #
        lineEditGroup = qlineeditgroup.QLineEditGroup(parent=self)
        lineEditGroup.lineEditTextEdited.connect(self.cell_textEdited)
        lineEditGroup.lineEditTextChanged.connect(self.cell_textChanged)

        for column in range(columnCount):

            lineEdit = self.createLineEdit()
            lineEditGroup.addLineEdit(lineEdit, id=column)

        return lineEditGroup
    # endregion

    # region Slots
    def cell_textEdited(self, column):
        """
        Text edited slot method responsible for emitting the cell edited signal.
        This does not include calls made to QLineEdit.setText().

        :type column: int
        :rtype: None
        """

        lineEditGroup = self.sender()
        row = self.rows().index(lineEditGroup)

        self.cellEdited.emit(row, column)
        self.matrixChanged.emit(self.matrix())

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
        self.matrixChanged.emit(self.matrix())
    # endregion
