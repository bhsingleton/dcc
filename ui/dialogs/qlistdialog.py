import json

from . import quicdialog
from ...python import importutils
from ...vendor.Qt import QtCore, QtWidgets, QtGui
from ...vendor.six import string_types

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


clipman = importutils.tryImport('clipman', __locals__=locals(), __globals__=globals())


class QListDialog(quicdialog.QUicDialog):
    """
    Overload of `QUicDialog` used to edit string lists.
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

        # Declare public variables
        #
        self.listWidget = None

        self.buttonsWidget = None
        self.interopWidget = None
        self.addPushButton = None
        self.removePushButton = None
        self.upPushButton = None
        self.downPushButton = None
        self.okayPushButton = None
        self.cancelPushButton = None

        self.editMenu = None
        self.copyItemsAction = None
        self.pasteItemsAction = None
        self.clearItemsAction = None
    # endregion

    # region Methods
    def postLoad(self, *args, **kwargs):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        # Call parent method
        #
        super(QListDialog, self).postLoad(*args, **kwargs)

        # Initialize context menu
        #
        self.copyItemsAction = QtWidgets.QAction('Copy')
        self.copyItemsAction.setObjectName('copyItemsAction')
        self.copyItemsAction.triggered.connect(self.on_copyItemsAction_triggered)

        self.pasteItemsAction = QtWidgets.QAction('Paste')
        self.pasteItemsAction.setObjectName('pasteItemsAction')
        self.pasteItemsAction.triggered.connect(self.on_pasteItemsAction_triggered)

        self.clearItemsAction = QtWidgets.QAction('Clear')
        self.clearItemsAction.setObjectName('clearItemsAction')
        self.clearItemsAction.triggered.connect(self.on_clearItemsAction_triggered)

        self.editMenu = QtWidgets.QMenu(parent=self.listWidget)
        self.editMenu.setObjectName('editMenu')
        self.editMenu.addActions([self.copyItemsAction, self.pasteItemsAction])
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.clearItemsAction)

        # Check if any arguments were supplied
        #
        numArgs = len(args)

        if numArgs == 1:

            self.setWindowTitle(args[0])

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
            listWidgetItem = QtWidgets.QListWidgetItem(item)
            self.listWidget.addItem(listWidgetItem)

        # Select first row
        #
        if self.listWidget.count() > 0:

            self.listWidget.setCurrentRow(0)

    def selectedItems(self):
        """
        Returns the selected items.

        :rtype: List[str]
        """

        return [item.text() for item in self.listWidget.selectedItems()]

    def selectionMode(self):
        """
        Returns the selection mode.

        :rtype: QtWidgets.QAbstractItemView.SelectionMode
        """

        return self.listWidget.selectionMode()

    def setSelectionMode(self, selectionMode):
        """
        Updates the selection mode.

        :type selectionMode: QtWidgets.QAbstractItemView.SelectionMode
        :rtype: None
        """

        self.listWidget.setSelectionMode(selectionMode)

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

        return not any(item == text for item in self.iterItems())

    @classmethod
    def editItems(cls, items, title='Edit Items', textFilter=None, parent=None):
        """
        Prompts the user to edit the supplied list of items.

        :type items: List[str]
        :type title: str
        :type textFilter: Callable
        :type parent: QtWidgets.QMainWindow
        :rtype: Tuple[bool, List[str]]
        """

        # Initialize dialog
        #
        dialog = cls(title, parent=parent)
        dialog.interopWidget.setVisible(True)
        dialog.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        dialog.setItems(items)

        if callable(textFilter):

            dialog.setTextFilter(textFilter)

        # Execute dialog
        #
        response = dialog.exec_()

        if response:

            return True, dialog.items()

        else:

            return False, items

    @classmethod
    def getItems(cls, items, title='Get Items', parent=None):
        """
        Prompts the user to select from a list of items.

        :type items: List[str]
        :type title: str
        :type parent: QtWidgets.QMainWindow
        :rtype: Tuple[bool, List[str]]
        """

        dialog = cls(title, parent=parent)
        dialog.interopWidget.setHidden(True)
        dialog.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        dialog.setItems(items)

        # Execute dialog
        #
        response = dialog.exec_()

        if response:

            return True, dialog.selectedItems()

        else:

            return False, items
    # endregion

    # region Slots
    @QtCore.Slot(QtCore.QPoint)
    def on_listWidget_customContextMenuRequested(self, point):
        """
        Slot method for the `listWidget` widget's `customContextMenuRequested` signal.

        :type point: QtCore.QPoint
        :rtype: None
        """

        globalPoint = self.sender().mapToGlobal(point)
        self.editMenu.exec_(globalPoint)

    @QtCore.Slot()
    def on_copyItemsAction_triggered(self):
        """
        Slot method for the `copyItemsAction` widget's `triggered` signal.

        :rtype: None
        """

        try:

            clipman.set(json.dumps(self.items()))

        except AttributeError:

            pass

    @QtCore.Slot()
    def on_pasteItemsAction_triggered(self):
        """
        Slot method for the `pasteItemsAction` widget's `triggered` signal.

        :rtype: None
        """

        try:

            items = json.loads(clipman.get())
            self.setItems(items)

        except (json.JSONDecodeError, AttributeError):

            pass

    @QtCore.Slot()
    def on_clearItemsAction_triggered(self):
        """
        Slot method for the `clearItemsAction` widget's `triggered` signal.

        :rtype: None
        """

        self.setItems([])

    @QtCore.Slot()
    def on_addPushButton_clicked(self):
        """
        Slot method for the `addPushButton` widget's `clicked` signal.

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
            listWidgetItem = QtWidgets.QListWidgetItem(text)
            self.listWidget.addItem(listWidgetItem)

    @QtCore.Slot()
    def on_removePushButton_clicked(self):
        """
        Slot method for the `removePushButton` widget's `clicked` signal.

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

    @QtCore.Slot()
    def on_upPushButton_clicked(self):
        """
        Slot method for the `upPushButton` widget's `clicked` signal.

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

    @QtCore.Slot()
    def on_downPushButton_clicked(self):
        """
        Slot method for the `downPushButton` widget's `clicked` signal.

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
