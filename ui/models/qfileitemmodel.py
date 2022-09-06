from Qt import QtCore
from itertools import chain
from dcc.generators.consecutivepairs import consecutivePairs
from . import qabstractfileitemmodel, qfilepath

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QFileItemModel(qabstractfileitemmodel.QAbstractFileItemModel):
    """
    Overload of QAbstractFileItemModel that displays file data.
    """

    # region Methods
    def insertRows(self, row, paths, parent=QtCore.QModelIndex()):
        """
        Inserts multiple rows before the given row in the child items of the parent specified.

        :type row: int
        :type paths: List[Union[str, qfilepath.QFilePath]]
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        # Mark start of row insertion
        #
        rowCount = len(paths)
        firstRow = row if row >= 0 else self.rowCount(parent)
        lastRow = (firstRow + rowCount) - 1

        self.beginInsertRows(parent, firstRow, lastRow)

        # Insert new paths
        #
        currentPaths = self.paths()

        for (physicalIndex, logicalIndex) in enumerate(range(firstRow, lastRow + 1, 1)):

            currentPaths.insert(logicalIndex, qfilepath.QFilePath(paths[physicalIndex]))

        # Mark end of row insertion
        #
        self.endInsertRows()
        return True

    def popRows(self, row, count, parent=QtCore.QModelIndex()):
        """
        Pops the number of rows starting with the given row under parent from the model.
        Returns a list of popped items.

        :type row: int
        :type count: int
        :type parent: QtCore.QModelIndex
        :rtype: List[qfilepath.QFilePath]
        """

        # Signal start of removal
        #
        lastRow = (row + count) - 1
        self.beginRemoveRows(parent, row, lastRow)

        # Verify parent is mutable
        #
        currentPaths = self.paths()
        paths = [currentPaths.pop(i) for i in range(lastRow, row - 1, -1)]

        # Signal end of removal
        #
        self.endRemoveRows()
        return paths

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        """
        Removes number of rows starting with the given row under parent from the model.
        Returns true if the rows were successfully removed; otherwise returns false.

        :type row: int
        :type count: int
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        paths = self.popRows(row, count, parent=parent)
        return len(paths) == count

    def canDropMimeData(self, data, action, row, column, parent):
        """
        Evaluates if mime data can be dropped on the requested row.

        :type data: QtCore.QMimeData
        :type action: int
        :type row: int
        :type column: int
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        return not parent.isValid()

    def dropMimeData(self, data, action, row, column, parent):
        """
        Handles the data supplied by a drag and drop operation that ended with the given action.
        Returns true if the data and action were handled by the model; otherwise returns false.

        :type data: QtCore.QMimeData
        :type action: int
        :type row: int
        :type column: int
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        # Collect paths from mime data
        #
        paths = [qfilepath.QFilePath(url.toLocalFile()) for url in data.urls()]
        log.debug('Receiving URLs: %s' % paths)

        # Diff files against current array
        #
        filePaths = list(chain(*[[path] if path.isFile() else [child for child in path.children if child.isFile()] for path in paths]))
        currentPaths = self.paths()

        existingPaths = [filePath for filePath in filePaths if filePath in currentPaths]
        nonExistingPaths = [filePath for filePath in filePaths if filePath not in currentPaths]

        # Perform move operation
        #
        numExistingPaths = len(existingPaths)

        if numExistingPaths:

            # Remove items and reinsert
            #
            indices = [currentPaths.index(filePath) for filePath in existingPaths]

            for (start, end) in reversed(list(consecutivePairs(indices))):

                self.removeRows(start, (end - start) + 1, parent=parent)

            self.insertRows(row, existingPaths, parent=parent)

        # Perform insert operation
        #
        numNonExistingPaths = len(nonExistingPaths)

        if numNonExistingPaths:

            self.insertRows(row, nonExistingPaths, parent=parent)

        return True
    # endregion
