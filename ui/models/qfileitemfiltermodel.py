from PySide2 import QtCore, QtWidgets, QtGui
from dcc.ui.models import qfileitemmodel

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QFileItemFilterModel(QtCore.QSortFilterProxyModel):
    """
    Overload of QSortFilterProxyModel used to filter files.
    """

    def __init__(self, parent=None):
        """
        Private method called after a new instance has been created.

        :type parent: QtCore.QObject
        :rtype: None
        """

        # Call parent method
        #
        super(QFileItemFilterModel, self).__init__(parent=parent)

        # Declare private variables
        #
        self._ignoreFiles = False
        self._ignoreLinks = False

    def ignoreFiles(self):
        """
        Returns the files flag.

        :rtype: bool
        """

        return self._ignoreFiles

    def setIgnoreFiles(self, ignoreFiles):
        """
        Updates the ignore files flag.

        :type ignoreFiles: bool
        :rtype: None
        """

        self._ignoreFiles = ignoreFiles

    def ignoreLinks(self):
        """
        Returns the symlinks flag.

        :rtype: bool
        """

        return self._ignoreFiles

    def setIgnoreLinks(self, ignoreLinks):
        """
        Updates the ignore symlinks flag.

        :type ignoreLinks: bool
        :rtype: None
        """

        self._ignoreFiles = ignoreLinks

    def setSourceModel(self, sourceModel):
        """
        Updates the source model to be processed by this proxy model.

        :type sourceModel: QFileItemModel
        :rtype: None
        """

        if isinstance(sourceModel, qfileitemmodel.QFileItemModel):

            super(QFileItemFilterModel, self).setSourceModel(sourceModel)

        else:

            raise TypeError('setSourceModel() expects a QFileItemModel (%s given)!' % type(sourceModel).__name__)

    def filterAcceptsRow(self, row, parent):
        """
        Returns true if the item in the row indicated by the given row and parent should be included in the model.

        :type row: int
        :type parent: QtCore.QModelIndex
        :rtype: bool
        """

        # Check if source model exists
        #
        sourceModel = self.sourceModel()  # type: qfileitemmodel.QFileItemModel

        if sourceModel is None:

            return False

        # Get path from index
        #
        index = sourceModel.index(row, 0, parent=parent)
        path = sourceModel.pathFromIndex(index)

        if self._ignoreLinks and path.isLink():

            return False

        elif self._ignoreFiles and path.isFile():

            return False

        else:

            return True
