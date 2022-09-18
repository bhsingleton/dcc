import inspect

from PySide2 import QtCore, QtWidgets, QtGui
from six.moves import collections_abc
from enum import Enum, IntEnum
from collections import defaultdict
from . import qpsonpath
from ...python import annotationutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QPSONStyledItemDelegate(QtWidgets.QStyledItemDelegate):
    """
    Overload of QStyledItemDelegate used to edit python data.
    """

    __builtins__ = (bool, int, float, str)

    __getters__ = {
        'QLineEdit': lambda widget: widget.text(),
        'QFileEdit': lambda widget: widget.text(),
        'QDirectoryEdit': lambda widget: widget.text(),
        'QSpinBox': lambda widget: widget.value(),
        'QDoubleSpinBox': lambda widget: widget.value(),
        'QTimeSpinBox': lambda widget: widget.value(),
        'QCheckBox': lambda widget: widget.isChecked(),
        'QComboBox': lambda widget: widget.currentIndex()
    }

    __setters__ = {
        'QLineEdit': lambda widget, value: widget.setText(value),
        'QFileEdit': lambda widget, value: widget.setText(value),
        'QDirectoryEdit': lambda widget, value: widget.setText(value),
        'QSpinBox': lambda widget, value: widget.setValue(value),
        'QDoubleSpinBox': lambda widget, value: widget.setValue(value),
        'QTimeSpinBox': lambda widget, value: widget.setValue(value),
        'QCheckBox': lambda widget, value: widget.setChecked(value),
        'QComboBox': lambda widget, value: widget.setCurrentIndex(value)
    }

    __types__ = {
        'str': QtWidgets.QLineEdit,
        'unicode': QtWidgets.QLineEdit,  # Legacy
        'int': QtWidgets.QSpinBox,
        'float': QtWidgets.QDoubleSpinBox,
        'bool': QtWidgets.QCheckBox,
        'list': QtWidgets.QSpinBox
    }

    def __init__(self, parent=None):
        """
        Private method called after a new instance has been created.

        :type parent: QtWidgets.QWidget
        :rtype: None
        """

        # Call parent method
        #
        super(QPSONStyledItemDelegate, self).__init__(parent=parent)

        # Declare private variables
        #
        self._getters = dict(self.__getters__)
        self._setters = dict(self.__setters__)

    def createEditor(self, parent, option, index):
        """
        Returns the widget used to edit the item specified by index for editing.
        The parent widget and style option are used to control how the editor widget appears.

        :type parent: QtWidgets.QWidget
        :type option: QtWidgets.QStyleOptionViewItem
        :type index: QtCore.QModelIndex
        :rtype: QtWidget.QWidget
        """

        model = index.model()
        internalId = model.decodeInternalId(index.internalId())

        return self.createEditorByInternalId(internalId, parent)

    def createEditorByInternalId(self, internalId, parent=None):
        """
        Returns a widget from the supplied model internal ID.

        :type internalId: qpsonpath.QPSONPath
        :type parent: QtWidget.QWidget
        :rtype: QtWidget.QWidget
        """

        # Get parent ID
        #
        parentId = None
        isElement = internalId.isElement()

        if isElement:

            parentId = internalId[:-2]  # Skips the array

        else:

            parentId = internalId[:-1]

        # Get associated object and accessor
        #
        obj = parentId.value()
        getter, setter = internalId.accessors()

        return self.createEditorByProperty(obj, getter, isElement, parent=parent)

    def createEditorByProperty(self, obj, func, isElement=False, parent=None):
        """
        Returns a widget from the supplied object and property.

        :type obj: object
        :type func: function
        :type isElement: bool
        :type parent: QtWidgets.QWidget
        :rtype: QtWidgets.QWidget
        """

        # Evaluate return type
        #
        returnType = annotationutils.getReturnType(func)

        if annotationutils.isParameterizedAlias(returnType):

            # Decompose alias
            #
            alias, parameters = annotationutils.decomposeAlias(returnType)
            numParameters = len(parameters)

            if numParameters == 1 and isElement:

                return self.createEditorByType(parameters[0], parent=parent)

            else:

                return self.createEditorByType(alias, parent=parent)

        else:

            return self.createEditorByType(returnType, parent=parent)

    def createEditorByType(self, cls, parent=None):
        """
        Returns the widget used to edit the type specified for editing.

        :type cls: type
        :type parent: QtWidgets.QWidget
        :rtype: QtWidget.QWidget
        """

        # Verify this is a class
        #
        if not inspect.isclass(cls):

            return self.createEditorByType(type(cls), parent=parent)

        # Get widget associated with type name
        #
        typeName = cls.__name__
        editor = self.__types__.get(typeName, None)

        if callable(editor):

            return editor(parent=parent)

        elif issubclass(cls, (Enum, IntEnum)):

            editor = QtWidgets.QComboBox(parent=parent)
            editor.addItems(list(cls.__members__.keys()))

            return editor

        else:

            return None

    def getEditorData(self, editor):
        """
        Returns the data from the supplied editor.

        :type editor: QtWidgets.QWidget
        :rtype: Any
        """

        typeName = type(editor).__name__
        func = self._getters.get(typeName, None)

        if callable(func):

            return func(editor)

        else:

            raise TypeError('getEditorData() expects a supported widget (%s given)!' % typeName)

    def setEditorData(self, editor, index):
        """
        Sets the data to be displayed and edited by the editor from the data model item specified by the model index.

        :type editor: QtWidgets.QWidget
        :type index: QtCore.QModelIndex
        :rtype: None
        """

        # Evaluate widget type
        #
        model = index.model()
        value = model.itemFromIndex(index)

        if isinstance(editor, QtWidgets.QSpinBox):

            # Inspect value type
            #
            editor.setRange(-9999, 9999)  # Default range is -99:99

            if isinstance(value, collections_abc.MutableSequence):

                editor.setValue(len(value))

            else:

                editor.setValue(value)

        elif isinstance(editor, QtWidgets.QDoubleSpinBox):

            editor.setValue(value)

        elif isinstance(editor, QtWidgets.QLineEdit):

            editor.setText(value)

        elif isinstance(editor, QtWidgets.QCheckBox):

            editor.setChecked(value)

        elif isinstance(editor, QtWidgets.QComboBox):

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

    def registerEditor(self, editor, getter, setter):
        """
        Registers a custom editor for data entry.
        The getter should return the value from the editor.
        Whereas the setter should update the editor with the passed value.

        :type editor: class
        :type getter: lambda
        :type setter: lambda
        :rtype: None
        """

        typeName = editor.__name__
        self._getters[typeName] = getter
        self._setters[typeName] = setter
