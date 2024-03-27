from Qt import QtCore, QtWidgets, QtGui
from dcc.python import stringutils
from . import qplugitemmodel

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QPlugItemFilterModel(QtCore.QSortFilterProxyModel):
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
        super(QPlugItemFilterModel, self).__init__(parent=parent)

        # Declare private variables
        #
        self._ignoreStaticAttributes = False
        self._ignoreDynamicAttributes = False
    # endregion

    # region Methods
    def plugFromIndex(self, index):
        """
        Returns the plug associated with the given index.

        :type index: QtCore.QModelIndex
        :rtype: om.MPlug
        """

        sourceIndex = self.mapToSource(index)
        sourceModel = self.sourceModel()

        return sourceModel.plugFromIndex(sourceIndex)

    def ignoreStaticAttributes(self):
        """
        Returns the `ignoreStaticAttributes` flag.

        :rtype: bool
        """

        return self._ignoreStaticAttributes

    @QtCore.Slot(bool)
    def setIgnoreStaticAttributes(self, ignoreStaticAttributes):
        """
        Updates the `ignoreStaticAttributes` flag.

        :type ignoreStaticAttributes: bool
        :rtype: None
        """

        self._ignoreStaticAttributes = ignoreStaticAttributes
        self.invalidateFilter()

    def ignoreDynamicAttributes(self):
        """
        Returns the `ignoreDynamicAttributes` flag.

        :rtype: bool
        """

        return self._ignoreDynamicAttributes

    @QtCore.Slot(bool)
    def setIgnoreDynamicAttributes(self, ignoreDynamicAttributes):
        """
        Updates the `ignoreDynamicAttributes` flag.

        :type ignoreDynamicAttributes: bool
        :rtype: None
        """

        self._ignoreDynamicAttributes = ignoreDynamicAttributes
        self.invalidateFilter()

    def setSourceModel(self, sourceModel):
        """
        Updates the source model to be processed by this proxy model.

        :type sourceModel: qabstractfileitemmodel.QAbstractFileItemModel
        :rtype: None
        """

        if isinstance(sourceModel, qplugitemmodel.QPlugItemModel):

            super(QPlugItemFilterModel, self).setSourceModel(sourceModel)

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
        sourceModel = self.sourceModel()  # type: qplugitemmodel.QPlugItemModel

        if sourceModel is None:

            return False

        # Get plug from index
        #
        index = sourceModel.index(row, 0, parent=parent)
        plug = sourceModel.plugFromIndex(index)

        # Check if path meets filtering criteria
        #
        if self.ignoreStaticAttributes() and not plug.isDynamic:

            return False

        elif self.ignoreDynamicAttributes() and plug.isDynamic:

            return False

        else:

            return super(QPlugItemFilterModel, self).filterAcceptsRow(row, parent)
    # endregion
