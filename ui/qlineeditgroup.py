from Qt import QtCore, QtWidgets

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QLineEditGroup(QtCore.QObject):
    """
    Overload of `QObject` that groups line edits together into a collection.
    """

    # region Signals
    lineEditTextChanged = QtCore.Signal(QtCore.QObject)
    idTextChanged = QtCore.Signal(int)
    lineEditTextEdited = QtCore.Signal(QtCore.QObject)
    idTextEdited = QtCore.Signal(int)
    # endregion

    # region Dunderscores
    def __init__(self, parent=None):
        """
        Private method called after a new instance has been created.

        :type parent: QtCore.QObject
        :rtype: None
        """

        # Call parent method
        #
        super(QLineEditGroup, self).__init__(parent=parent)

        # Declare private methods
        #
        self._lineEdits = {}

    def __getitem__(self, index):
        """
        Private method that returns an indexed line edit.

        :type index: int
        :rtype: QtWidgets.QLineEdit
        """

        return self.lineEdit(index)

    def __setitem__(self, key, value):
        """
        Private method that updates an indexed line edit.

        :type key: int
        :type value: QtWidgets.QLineEdit
        :rtype: None
        """

        self.addLineEdit(value, id=key)

    def __len__(self):
        """
        Private method that evaluates the number of line edits in this group.

        :rtype: int
        """

        return len(self._lineEdits)

    def __contains__(self, lineEdit):
        """
        Private method that evaluates if this group contains the supplied line edit.

        :type lineEdit: QtWidgets.QLineEdit
        :rtype: bool
        """

        return self.id(lineEdit) != -1
    # endregion

    # region Methods
    def lineEdits(self):
        """
        Returns a list of line edits in this group.

        :rtype: List[QtWidgets.QLineEdit]
        """

        return list(self._lineEdits.values())

    def ids(self):
        """
        Returns a list of IDs that are currently in use.

        :rtype: List[int]
        """

        return list(self._lineEdits.keys())

    def lineEdit(self, index):
        """
        Returns the line edit for the given index.

        :type index: int
        :rtype: QtWidgets.QLineEdit
        """

        return self._lineEdits.get(index, None)

    def id(self, lineEdit):
        """
        Returns the id for the given line edit.
        If there is not line edit in this group then -1 is returned instead.

        :type lineEdit: QtWidgets.QLineEdit
        :rtype: int
        """

        try:

            index = list(self._lineEdits.values()).index(lineEdit)
            key = list(self._lineEdits.keys())[index]

            return key

        except IndexError:

            return -1

    def getNextAvailableId(self):
        """
        Returns the next available id.

        :rtype: int
        """

        ids = self.ids()
        numIDs = len(ids)

        for i in range(numIDs):

            if i != ids[i]:

                return i

        return numIDs

    def addLineEdit(self, lineEdit, id=-1):
        """
        Adds the supplied line edit to this group.

        :type lineEdit: QtWidgets.QLineEdit
        :type id: int
        :rtype: None
        """

        # Inspect line edit argument
        #
        if not isinstance(lineEdit, QtWidgets.QLineEdit):

            raise TypeError('addLineEdit() expects a QLineEdit (%s given)!' % type(lineEdit).__name__)

        # Inspect id argument
        #
        if not isinstance(id, int):

            raise TypeError('addLineEdit() expects an int (%s given)!' % type(id).__name__)

        # Evaluate id value
        # If id is negative then get the next available id
        #
        if id < 0:

            id = self.getNextAvailableId()

        # Check if id is already in use
        #
        if id in self.ids():

            self.removeLineEdit(self._lineEdits[id])

        # Assign line edit to group
        #
        self._lineEdits[id] = lineEdit
        lineEdit.textChanged.connect(self.lineEdit_textChanged)
        lineEdit.textEdited.connect(self.lineEdit_textEdited)

    def removeLineEdit(self, lineEdit):
        """
        Removes the supplied line edit from this group.

        :type lineEdit: QtWidgets.QLineEdit
        :rtype: None
        """

        index = self.id(lineEdit)

        if index != -1:

            lineEdit = self._lineEdits.pop(index)
            lineEdit.textChanged.disconnect(self.lineEdit_textChanged)
            lineEdit.textEdited.disconnect(self.lineEdit_textExited)
    # endregion

    # region Slots
    def lineEdit_textChanged(self, text):
        """
        Text changed slot method responsible for triggering the text changed signals.

        :type text: str
        :rtype: None
        """

        sender = self.sender()
        self.lineEditTextChanged.emit(sender)
        self.idTextChanged.emit(self.id(sender))

    def lineEdit_textEdited(self, text):
        """
        Text changed slot method responsible for triggering the text edited signals.

        :type text: str
        :rtype: None
        """

        sender = self.sender()
        self.lineEditTextEdited.emit(sender)
        self.idTextEdited.emit(self.id(sender))
    # endregion
