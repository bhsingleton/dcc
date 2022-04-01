import inspect

from PySide2 import QtCore, QtWidgets, QtGui
from six import string_types, integer_types
from six.moves import collections_abc
from typing import *
from enum import IntEnum

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QPropertyItemDelegate(QtWidgets.QStyledItemDelegate):
    """
    Overload of QStyledItemDelegate used to interface with QPropertyItemModels.
    """

    __builtins__ = (bool, int, float, str)

    __types__ = {
        'str': QtWidgets.QLineEdit,
        'unicode': QtWidgets.QLineEdit,  # Legacy
        'int': QtWidgets.QSpinBox,
        'float': QtWidgets.QDoubleSpinBox,
        'bool': QtWidgets.QCheckBox,
        'IntEnum': QtWidgets.QComboBox
    }

    def createEditor(self, parent, option, index):
        """
        Returns the widget used to edit the item specified by index for editing.
        The parent widget and style option are used to control how the editor widget appears.

        :type parent: QtWidgets.QWidget
        :type option: QtWidgets.QStyleOptionViewItem
        :type index: QtCore.QModelIndex
        :rtype: QtWidget.QWidget
        """

        # Get internal id from index
        #
        model = index.model()
        internalId = model.decodeInternalId(index.internalId())

        # Create widget associated with return type
        #
        getter, setter = model.propertyFromInternalId(internalId)
        returnType = model.getPropertyTypeHint(getter)

        return self.createEditorByType(returnType, parent=parent, index=internalId[-1])

    def createEditorByType(self, T, parent=None, index=None):
        """
        Returns the widget used to edit the type specified for editing.

        :type T: type
        :type parent: QtWidgets.QWidget
        :type index: Union[str, int]
        :rtype: QtWidget.QWidget
        """

        # Evaluate type hint
        #
        if hasattr(T, '__args__'):  # Reserved for typing objects

            # Check if this is an indexed item
            #
            if isinstance(index, integer_types):

                return self.createEditorByType(T.__args__[0], parent=parent)

            else:

                return QtWidgets.QSpinBox(parent=parent)

        elif inspect.isclass(T):

            # Get widget associated with type name
            #
            typeName = T.__name__
            cls = self.__types__.get(typeName, None)

            if callable(cls):

                return cls(parent=parent)

            else:

                return None

        else:

            return self.createEditorByType(type(T))

    def getEditorData(self, editor):
        """
        Returns the data from the supplied editor.

        :type editor: QtWidgets.QWidget
        :rtype: Any
        """

        if isinstance(editor, QtWidgets.QLineEdit):

            return editor.text()

        elif isinstance(editor, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):

            return editor.value()

        elif isinstance(editor, QtWidgets.QCheckBox):

            return editor.isChecked()

        elif isinstance(editor, QtWidgets.QComboBox):

            return editor.currentIndex()

        else:

            raise TypeError('getEditorData() expects a supported widget (%s given)!' % type(editor).__name__)

    def setEditorData(self, editor, index):
        """
        Sets the data to be displayed and edited by the editor from the data model item specified by the model index.

        :type editor: QtWidgets.QWidget
        :type index: QtCore.QModelIndex
        :rtype: None
        """

        model = index.model()
        value = model.itemFromIndex(index)

        if isinstance(editor, QtWidgets.QSpinBox) and isinstance(value, collections_abc.MutableSequence):

            editor.setValue(len(value))

        elif isinstance(editor, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):

            editor.setValue(value)

        elif isinstance(editor, QtWidgets.QLineEdit):

            editor.setText(value)

        elif isinstance(editor, QtWidgets.QCheckBox):

            editor.setChecked(value)

        elif isinstance(editor, QtWidgets.QComboBox):

            editor.addItems(list(value.__members__.keys()))
            editor.setCurrentIndex(value)

        else:

            raise TypeError('setEditorData() expects a supported widget (%s given)!' % type(editor).__name__)

    def updateEditorGeometry(self, editor, option, index):
        """
        Updates the editor for the item specified by index according to the style option given.

        :type editor: QtWidgets.QWidget
        :type option: QtWidgets.QStyleOptionViewItem
        :type index: QtCore.QModelIndex
        :rtype: None
        """

        editor.setAutoFillBackground(True)
        editor.setGeometry(option.rect)

    def setModelData(self, editor, model, index):
        """
        Gets data from the editor widget and stores it in the specified model at the item index.

        :type editor: QtWidgets.QWidget
        :type model: QtCore.QAbstractItemModel
        :type index: QtCore.QModelIndex
        :rtype: None
        """

        value = self.getEditorData(editor)
        model.setData(index, value, role=QtCore.Qt.EditRole)
