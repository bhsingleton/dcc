from PySide2 import QtCore, QtWidgets, QtGui
from six import string_types

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QListDialog(QtWidgets.QDialog):
    """
    Overload of QDialog used to edit string list data.
    """

    def __init__(self, title, parent=None, f=QtCore.Qt.WindowFlags()):
        """
        Private method called after a new instance has been created.

        :type title: str
        :type parent: QtWidgets.QWidget
        :type f: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        super(QListDialog, self).__init__(parent=parent, f=f)

        # Declare class variables
        #
        self._textFilter = None

        # Set dialog properties
        #
        self.setWindowTitle(title)
        self.setLayout(QtWidgets.QHBoxLayout())

        # Create list view
        #
        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setUniformItemSizes(True)

        self.layout().addWidget(self.listWidget)

        # Create manipulate buttons
        #
        self.addButton = QtWidgets.QPushButton('Add')
        self.addButton.clicked.connect(self.addItem)

        self.removeButton = QtWidgets.QPushButton('Remove')
        self.removeButton.clicked.connect(self.removeItem)

        self.upButton = QtWidgets.QPushButton('Up')
        self.upButton.clicked.connect(self.moveItemUp)

        self.downButton = QtWidgets.QPushButton('Down')
        self.downButton.clicked.connect(self.moveItemDown)

        self.okButton = QtWidgets.QPushButton('OK')
        self.okButton.clicked.connect(self.accept)

        self.cancelButton = QtWidgets.QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.reject)

        self.buttonLayout = QtWidgets.QGridLayout()
        self.buttonLayout.addWidget(self.addButton, 0, 0)
        self.buttonLayout.addWidget(self.removeButton, 1, 0)
        self.buttonLayout.addWidget(self.upButton, 2, 0)
        self.buttonLayout.addWidget(self.downButton, 3, 0)
        self.buttonLayout.setRowStretch(4, 100)
        self.buttonLayout.addWidget(self.okButton, 5, 0)
        self.buttonLayout.addWidget(self.cancelButton, 6, 0)

        self.layout().addLayout(self.buttonLayout)

    def items(self):
        """
        Returns the current string items being edited.

        :rtype: List[str]
        """

        return [self.listWidget.item(x).text() for x in range(self.listWidget.count())]

    def setItems(self, items):
        """
        Updates the current string items being edited.

        :type items: List[str]
        :rtype: None
        """

        # Iterate through items
        #
        #
        self.listWidget.clear()

        for item in items:

            # Check item type
            #
            if not isinstance(item, string_types):

                continue

            # Add item to list widget
            #
            listWidgetItem = self.createListWidgetItem(item)
            self.listWidget.addItem(listWidgetItem)

        # Select first row
        #
        if self.listWidget.count() != 0:

            self.listWidget.setCurrentRow(0)

    def textFilter(self):
        """
        Returns the text filter object.

        :rtype: method
        """

        return self._textFilter

    def setTextFilter(self, textFilter):
        """
        Updates the text filter object.
        This filter must accept a single value and return a filtered string.

        :type textFilter: method
        :rtype: None
        """

        # Check if object is callable
        #
        if callable(textFilter):

            self._textFilter = textFilter

        else:

            raise TypeError('setTextFilter() expects a callable object (%s given)!' % type(textFilter).__name__)

    def isTextUnique(self, text):
        """
        Evaluates if the supplied text is currently unique.

        :type text: str
        :rtype: bool
        """

        return not any(x.text() == text for x in self.items())

    @staticmethod
    def createListWidgetItem(text):
        """
        Returns a new QListWidgetItem using the supplied text.

        :type text: str
        :rtype: QtWidgets.QListWidgetItem
        """

        listWidgetItem = QtWidgets.QListWidgetItem(text)
        listWidgetItem.setSizeHint(QtCore.QSize(listWidgetItem.sizeHint().width(), 20))

        return listWidgetItem

    def addItem(self, text=''):
        """
        Prompts the user for a new item to be added to the list.
        The optional text field is provided for any reattempts to rectify invalid entries.

        :type text: str
        :rtype: None
        """

        # Prompt user
        #
        text, response = QtWidgets.QInputDialog.getText(
            self,
            'Add New Item',
            'Enter Text:',
            text=text
        )

        if response:

            # Slugify text if enabled
            #
            if self._textFilter is not None:

                text = self._textFilter(text)

            # Check if text is unique
            #
            if not self.isTextUnique(text) or len(text) == 0:

                # Prompt user
                #
                response = QtWidgets.QMessageBox.warning(
                    self,
                    'Add New Item',
                    'The entered text is not unique!',
                    QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
                )

                if response == QtWidgets.QMessageBox.Ok:

                    return self.addItem(text=text)

                else:

                    return

            # Add item to list widget
            #
            listWidgetItem = self.createListWidgetItem(text)
            self.listWidget.addItem(listWidgetItem)

        else:

            log.info('Operation aborted...')

    def removeItem(self):
        """
        Removes the selected item from the list widget.
        The removed item will be returned before being destroyed by garbage collection.

        :rtype: QtWidgets.QListWidgetItem
        """

        # Check number of items
        #
        if self.listWidget.count() == 0:

            return

        # Get selected row
        #
        currentRow = self.listWidget.currentRow()

        if currentRow == -1:

            return

        # Remove item
        #
        return self.listWidget.takeItem(currentRow)

    def moveItemUp(self):
        """
        Moves the selected item up in the list widget.

        :rtype: None
        """

        # Check number of items
        #
        if self.listWidget.count() == 0:

            return

        # Get selected row
        #
        currentRow = self.listWidget.currentRow()

        if currentRow == -1:

            return

        # Take item and reinsert it
        #
        newRow = currentRow - 1
        item = self.listWidget.takeItem(currentRow)

        self.listWidget.insertItem(newRow, item)
        self.listWidget.setCurrentRow(newRow)

    def moveItemDown(self):
        """
        Moves the selected item down in the list widget.

        :rtype: None
        """

        # Check number of items
        #
        if self.listWidget.count() == 0:

            return

        # Get selected row
        #
        currentRow = self.listWidget.currentRow()

        if currentRow == (self.listWidget.count() - 1):

            return

        # Take item and reinsert it
        #
        newRow = currentRow + 1
        item = self.listWidget.takeItem(currentRow)

        self.listWidget.insertItem(newRow, item)
        self.listWidget.setCurrentRow(newRow)
