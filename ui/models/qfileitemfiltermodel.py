from PySide2 import QtCore, QtWidgets, QtGui
from dcc.ui.models import qabstractfileitemmodel

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QFileItemFilterModel(QtCore.QSortFilterProxyModel):
    """
    Overload of QSortFilterProxyModel used to filter files.
    """

    # region Dunderscores
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
        self._directoriesOnly = False
        self._ignoreSymLinks = False
    # endregion

    # region Methods
    def directoriesOnly(self):
        """
        Returns the "directoriesOnly" flag.

        :rtype: bool
        """

        return self._directoriesOnly

    def setDirectoriesOnly(self, directoriesOnly):
        """
        Updates the "directoriesOnly" flag.

        :type directoriesOnly: bool
        :rtype: None
        """

        self._directoriesOnly = directoriesOnly

    def ignoreSymLinks(self):
        """
        Returns the "ignoreSymLinks" flag.

        :rtype: bool
        """

        return self._ignoreSymLinks

    def setIgnoreSymLinks(self, ignoreSymLinks):
        """
        Updates the "ignoreSymLinks" flag.

        :type ignoreSymLinks: bool
        :rtype: None
        """

        self._ignoreSymLinks = ignoreSymLinks

    def setSourceModel(self, sourceModel):
        """
        Updates the source model to be processed by this proxy model.

        :type sourceModel: qabstractfileitemmodel.QAbstractFileItemModel
        :rtype: None
        """

        if isinstance(sourceModel, qabstractfileitemmodel.QAbstractFileItemModel):

            super(QFileItemFilterModel, self).setSourceModel(sourceModel)

        else:

            raise TypeError('setSourceModel() expects a QAbstractFileItemModel subclass (%s given)!' % type(sourceModel).__name__)

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

        if self.ignoreSymLinks() and path.isLink():

            return False

        elif self.directoriesOnly() and not path.isDir():

            return False

        else:

            return super(QFileItemFilterModel, self).filterAcceptsRow(row, parent)
    # endregion
