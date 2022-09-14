from PySide2 import QtCore, QtWidgets, QtGui
from . import quicdialog
from six import string_types

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QListDialog(quicdialog.QUicDialog):
    """
    Overload of QDialog used to edit string list data.
    """

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :type title: str
        :type parent: QtWidgets.QWidget
        :type f: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        super(QListDialog, self).__init__(**kwargs)

        # Declare private variables
        #
        self._items = []
        self._textFilter = kwargs.get('textFilter', None)
        self._allowDuplicates = kwargs.get('allowDuplicates', False)

        # Build user interface
        #
        self.__build__(*args, **kwargs)

        # Check if any arguments were supplied
        #
        numArgs = len(args)

        if numArgs == 1:

            self.setWindowTitle(args[0])
    # endregion

    # region Methods
    def iterItems(self):
        """
        Returns a generator that yields the current items.

        :rtype: iter
        """

        for i in range(self.listWidget.count()):

            yield self.listWidget.item(i).text()

    def items(self):
        """
        Returns the current items.

        :rtype: List[str]
        """

        return list(self.iterItems())

    def setItems(self, items):
        """
        Updates the current items.

        :type items: List[str]
        :rtype: None
        """

        # Iterate through items
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
        if self.listWidget.count() > 0:

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

    def filterText(self, text):
        """
        Filters the supplied text based on the current filter method.

        :type text: str
        :rtype: str
        """

        func = self.textFilter()

        if callable(func):

            return func(text)

        else:

            return text

    def allowDuplicates(self):
        """
        Returns the supports duplicates flag.

        :rtype: bool
        """

        return self._allowDuplicates

    def setAllowDuplicates(self, allowDuplicates):
        """
        Updates the supports duplicates flag.

        :type allowDuplicates: bool
        :rtype: None
        """

        self._allowDuplicates = allowDuplicates

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

        return QtWidgets.QListWidgetItem(text)
    # endregion

    # region Slots
    @QtCore.Slot(bool)
    def on_addPushButton_clicked(self, checked=False):
        """
        Clicked slot method that adds a new item to the list.

        :type checked: bool
        :rtype: None
        """

        # Prompt user
        #
        text, response = QtWidgets.QInputDialog.getText(self, 'Add New Item', 'Enter Text:')

        if not response:

            log.info('Operation aborted...')
            return

        # Check if text is unique
        #
        text = self.filterText(text)
        allowDuplicates = self.allowDuplicates()

        if (not allowDuplicates and not self.isTextUnique(text)) or len(text) == 0:

            # Prompt user
            #
            response = QtWidgets.QMessageBox.warning(
                self,
                'Add New Item',
                'The entered text is not unique!',
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
            )

            if response == QtWidgets.QMessageBox.Ok:

                return self.sender().click()

        else:

            # Add item to list widget
            #
            listWidgetItem = self.createListWidgetItem(text)
            self.listWidget.addItem(listWidgetItem)

    @QtCore.Slot(bool)
    def on_removePushButton_clicked(self, checked=False):
        """
        Clicked slot method that removes the selected item from the list.

        :type checked: bool
        :rtype: None
        """

        # Check number of items
        #
        numRows = self.listWidget.count()

        if numRows == 0:

            return

        # Get selected row
        #
        currentRow = self.listWidget.currentRow()

        if 0 <= currentRow < numRows:

            self.listWidget.takeItem(currentRow)

    @QtCore.Slot(bool)
    def on_upPushButton_clicked(self, checked=False):
        """
        Clicked slot method that moves the selected item up in the list.

        :type checked: bool
        :rtype: None
        """

        # Check number of items
        #
        numRows = self.listWidget.count()

        if numRows == 0:

            return

        # Get selected row
        #
        currentRow = self.listWidget.currentRow()
        newRow = currentRow - 1

        if 0 <= newRow < numRows:

            item = self.listWidget.takeItem(currentRow)
            self.listWidget.insertItem(newRow, item)
            self.listWidget.setCurrentRow(newRow)

    @QtCore.Slot(bool)
    def on_downPushButton_clicked(self, checked=False):
        """
        Clicked slot method that moves the selected item down in the list.

        :type checked: bool
        :rtype: None
        """

        # Check number of items
        #
        numRows = self.listWidget.count()

        if numRows == 0:

            return

        # Get selected row
        #
        currentRow = self.listWidget.currentRow()
        newRow = currentRow + 1

        if 0 <= newRow < numRows:

            item = self.listWidget.takeItem(currentRow)
            self.listWidget.insertItem(newRow, item)
            self.listWidget.setCurrentRow(newRow)
    # endregion
