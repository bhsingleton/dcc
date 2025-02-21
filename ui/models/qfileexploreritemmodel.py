from . import qabstractfileitemmodel
from ...vendor.Qt import QtCore

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QFileExplorerItemModel(qabstractfileitemmodel.QAbstractFileItemModel):
    """
    Overload of QAbstractFileItemModel that displays hierarchical file data.
    """

    # region Methods
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

        return False

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

        return False  # TODO: Implement file move operation
    # endregion
