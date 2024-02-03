import inspect

from Qt import QtCore, QtWidgets, QtGui
from six.moves import collections_abc
from enum import Enum, IntEnum
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

    # region Dunderscores
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
        'QSpinBox': lambda widget, value: (widget.setRange(-9999, 9999), widget.setValue(len(value)) if isinstance(value, collections_abc.MutableSequence) else widget.setValue(value)),
        'QDoubleSpinBox': lambda widget, value: (widget.setRange(-9999, 9999), widget.setValue(value)),
        'QTimeSpinBox': lambda widget, value: (widget.setRange(-9999, 9999), widget.setValue(value)),
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
    # endregion

    # region Methods
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
        Returns the widget used to edit the specified object property.

        :type obj: object
        :type func: function
        :type isElement: bool
        :type parent: QtWidgets.QWidget
        :rtype: QtWidgets.QWidget
        """

        # Check if object delegate exists
        #
        editor = self.createEditorByDelegate(obj, func, parent=parent)

        if isinstance(editor, QtWidgets.QWidget):

            return editor

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

    def createEditorByDelegate(self, obj, func, parent=None):
        """
        Returns the widget used to edit the specified object property via delegate.

        :type obj: object
        :type func: function
        :type parent: QtWidgets.QWidget
        :rtype: Union[QtWidgets.QWidget, None]
        """

        # Check if object has editor delegate
        #
        delegate = getattr(obj, 'createEditor')

        if callable(delegate):

            return delegate(func.__name__, parent=parent)

        else:

            return None

    def createEditorByType(self, cls, parent=None):
        """
        Returns the widget used to edit the specified type.

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

        # Evaluate widget type
        #
        typeName = type(editor).__name__
        func = self.__getters__.get(typeName, None)

        if callable(func):

            return func(editor)

        else:

            raise TypeError(f'getEditorData() expects a supported widget ({typeName} given)!')

    def setEditorData(self, editor, index):
        """
        Sets the data to be displayed and edited by the editor from the data model item specified by the model index.

        :type editor: QtWidgets.QWidget
        :type index: QtCore.QModelIndex
        :rtype: None
        """

        # Evaluate widget type
        #
        typeName = type(editor).__name__
        func = self.__setters__.get(typeName, None)

        model = index.model()
        value = model.itemFromIndex(index)

        if callable(func):

            return func(editor, value)

        else:

            raise TypeError(f'setEditorData() expects a supported widget ({typeName} given)!')

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
    # endregion
