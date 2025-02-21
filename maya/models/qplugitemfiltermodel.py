from maya.api import OpenMaya as om
from . import qplugitemmodel
from ...vendor.Qt import QtCore, QtWidgets, QtGui

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
        self._hideStaticAttributes = False
        self._hideDynamicAttributes = False
        self._showHiddenAttributes = False
    # endregion

    # region Mutators
    def hideStaticAttributes(self):
        """
        Returns the `hideStaticAttributes` flag.

        :rtype: bool
        """

        return self._hideStaticAttributes

    @QtCore.Slot(bool)
    def setHideStaticAttributes(self, hideStaticAttributes):
        """
        Updates the `hideStaticAttributes` flag.

        :type hideStaticAttributes: bool
        :rtype: None
        """

        self._hideStaticAttributes = hideStaticAttributes
        self.invalidateFilter()

    def hideDynamicAttributes(self):
        """
        Returns the `hideDynamicAttributes` flag.

        :rtype: bool
        """

        return self._hideDynamicAttributes

    @QtCore.Slot(bool)
    def setHideDynamicAttributes(self, hideDynamicAttributes):
        """
        Updates the `hideDynamicAttributes` flag.

        :type hideDynamicAttributes: bool
        :rtype: None
        """

        self._hideDynamicAttributes = hideDynamicAttributes
        self.invalidateFilter()

    def showHiddenAttributes(self):
        """
        Returns the `showHiddenAttributes` flag.

        :rtype: bool
        """

        return self._showHiddenAttributes

    @QtCore.Slot(bool)
    def setShowHiddenAttributes(self, showHiddenAttributes):
        """
        Returns the `showHiddenAttributes` flag.

        :type showHiddenAttributes: bool
        :rtype: None
        """

        self._showHiddenAttributes = showHiddenAttributes

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

        if plug.isNull:

            return False

        # Check if path meets filtering criteria
        #
        isDynamic = plug.isDynamic
        isStatic = not isDynamic
        isHidden = om.MFnAttribute(plug.attribute()).hidden

        if self.hideStaticAttributes() and isStatic:

            return False

        elif self.hideDynamicAttributes() and isDynamic:

            return False

        elif not self.showHiddenAttributes() and isHidden:

            return False

        else:

            return super(QPlugItemFilterModel, self).filterAcceptsRow(row, parent)
    # endregion
