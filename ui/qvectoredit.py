import sys

from Qt import QtCore, QtWidgets, QtGui
from dcc.ui import qlineeditgroup
from dcc.dataclasses import vector

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QVectorEdit(QtWidgets.QWidget):
    """
    Overload of QWidget used to edit transform matrices.
    """

    # region Signals
    readOnlyChanged = QtCore.Signal(bool)
    validatorChanged = QtCore.Signal(QtGui.QValidator)
    vectorChanged = QtCore.Signal(object)
    # endregion

    # region Dunderscores
    __decimals__ = 3

    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags):
        """
        Private method called after a new instance has been created.

        :type parent: QtWidgets.QWidget
        :type f: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        super(QVectorEdit, self).__init__(parent=parent)

        # Declare private variables
        #
        self._vector = vector.Vector()
        self._readOnly = False
        self._validator = self.defaultValidator()

        # Initialize line edits
        #
        self.vectorXLineEdit = self.createLineEdit()
        self.vectorYLineEdit = self.createLineEdit()
        self.vectorZLineEdit = self.createLineEdit()

        self.vectorLineEditGroup = qlineeditgroup.QLineEditGroup(parent=self)
        self.vectorLineEditGroup.addLineEdit(self.vectorXLineEdit, id=0)
        self.vectorLineEditGroup.addLineEdit(self.vectorYLineEdit, id=1)
        self.vectorLineEditGroup.addLineEdit(self.vectorZLineEdit, id=2)
        self.vectorLineEditGroup.idTextEdited.connect(self.vectorLineEditGroup_idTextEdited)

        # Add widgets to layout
        #
        boxLayout = QtWidgets.QHBoxLayout()
        boxLayout.addWidget(self.vectorXLineEdit)
        boxLayout.addWidget(self.vectorYLineEdit)
        boxLayout.addWidget(self.vectorZLineEdit)
        boxLayout.setSpacing(8)
        boxLayout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(boxLayout)
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
        Returns the validator used by this widget.

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
        Updates the validator used by this widget.

        :rtype: QtGui.QDoubleValidator
        """

        self._validator = validator
        self.validatorChanged.emit(self._validator)

    def vector(self):
        """
        Returns the current vector.

        :rtype: vector.Vector
        """

        return self._vector

    def setVector(self, v):
        """
        Updates the current vector.

        :type v: Union[Tuple[float, float, float], vector.Vector]
        :rtype: None
        """

        self._vector = vector.Vector(*v)
        self.synchronize()
        self.vectorChanged.emit(self._vector)

    def synchronize(self):
        """
        Ensures that the line edits match the internal vector value.

        :rtype: None
        """

        for (i, lineEdit) in enumerate(self.vectorLineEditGroup.lineEdits()):

            lineEdit.setText(str(round(self._vector[i], self.__decimals__)))

    def createLineEdit(self):
        """
        Returns a line edit with all the required settings and connections.

        :rtype: QtWidgets.QLineEdit
        """

        # Initialize line edit
        #
        lineEdit = QtWidgets.QLineEdit('0.0')
        lineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        lineEdit.setFixedHeight(24)
        lineEdit.setAlignment(QtCore.Qt.AlignCenter)
        lineEdit.setValidator(self._validator)
        lineEdit.setReadOnly(self._readOnly)

        # Connect signals to slots
        #
        self.readOnlyChanged.connect(lineEdit.setReadOnly)
        self.validatorChanged.connect(lineEdit.setValidator)

        return lineEdit
    # endregion

    # region Slots
    def vectorLineEditGroup_idTextEdited(self, index):
        """
        Slot method for the vectorLineEditGroup's `idTextEdited` signal.
        This method updates the associated internal vector element.

        :type index: int
        :rtype: None
        """

        self._vector[index] = float(self[index].text())
        self.vectorChanged.emit(self._vector)
    # endregion
