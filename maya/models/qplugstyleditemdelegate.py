from Qt import QtCore, QtWidgets, QtGui
from maya.api import OpenMaya as om
from dcc.maya.libs import plugmutators

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QPlugStyledItemDelegate(QtWidgets.QStyledItemDelegate):
    """
    Overload of QStyledItemDelegate used to edit python data.
    """

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
        'QSpinBox': lambda widget, value: (widget.setRange(-9999, 9999), widget.setValue(value)),
        'QDoubleSpinBox': lambda widget, value: (widget.setRange(-9999, 9999), widget.setValue(value)),
        'QTimeSpinBox': lambda widget, value: (widget.setRange(-9999, 9999), widget.setValue(value)),
        'QCheckBox': lambda widget, value: widget.setChecked(value),
        'QComboBox': lambda widget, value: widget.setCurrentIndex(value)
    }

    __numeric_types__ = {
        om.MFnNumericData.kBoolean: QtWidgets.QCheckBox,
        om.MFnNumericData.kInt: QtWidgets.QSpinBox,
        om.MFnNumericData.kShort: QtWidgets.QSpinBox,
        om.MFnNumericData.kLong: QtWidgets.QSpinBox,
        om.MFnNumericData.kFloat: QtWidgets.QDoubleSpinBox,
        om.MFnNumericData.kDouble: QtWidgets.QDoubleSpinBox,
    }

    __unit_types__ = {
        om.MFnUnitAttribute.kTime: QtWidgets.QDoubleSpinBox,
        om.MFnUnitAttribute.kAngle: QtWidgets.QDoubleSpinBox,
        om.MFnUnitAttribute.kDistance: QtWidgets.QDoubleSpinBox,
    }

    __data_types__ = {
        om.MFnData.kString: QtWidgets.QLineEdit
    }

    def __init__(self, parent=None):
        """
        Private method called after a new instance has been created.

        :type parent: QtWidgets.QWidget
        :rtype: None
        """

        # Call parent method
        #
        super(QPlugStyledItemDelegate, self).__init__(parent=parent)

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

        # Evaluate attribute type
        #
        model = index.model()
        plug = model.plugFromIndex(index)

        attribute = plug.attribute()

        if attribute.hasFn(om.MFn.kNumericAttribute):

            # Check if numeric editor exists
            #
            fnAttribute = om.MFnNumericAttribute(attribute)
            numericType = fnAttribute.numericType()
            cls = self.__numeric_types__.get(numericType, None)

            if not callable(cls):

                return

            # Create editor instance
            # Edit spin-box range
            #
            editor = cls(parent)

            if fnAttribute.hasMin() and isinstance(editor, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):

                editor.setMinimum(fnAttribute.getMin())

            if fnAttribute.hasMax() and isinstance(editor, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):

                editor.setMaximum(fnAttribute.getMax())

            return editor

        elif attribute.hasFn(om.MFn.kUnitAttribute):

            # Check if unit editor exists
            #
            fnAttribute = om.MFnUnitAttribute(attribute)
            unitType = fnAttribute.unitType()
            cls = self.__unit_types__.get(unitType, None)

            if not callable(cls):

                return

            # Create editor instance
            # Edit spin-box range
            #
            editor = cls(parent)

            if fnAttribute.hasMin():

                editor.setMinimum(fnAttribute.getMin())

            if fnAttribute.hasMax():

                editor.setMaximum(fnAttribute.getMax())

            return editor

        elif attribute.hasFn(om.MFn.kTypedAttribute):

            # Check if typed editor exists
            #
            dataType = om.MFnTypedAttribute(attribute).attrType()
            cls = self.__data_types__.get(dataType, None)

            if callable(cls):

                return cls(parent)

            else:

                return None

        elif attribute.hasFn(om.MFn.kEnumAttribute):

            # Get enum fields
            #
            fnAttribute = om.MFnEnumAttribute(attribute)
            minValue, maxValue = fnAttribute.getMin(), fnAttribute.getMax()

            fields = [fnAttribute.fieldName(value) for value in range(minValue, maxValue + 1)]

            # Create new editor instance
            # Populate field items
            #
            editor = QtWidgets.QComboBox(parent)
            editor.addItems(fields)

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
        plug = model.plugFromIndex(index)
        value = plugmutators.getValue(plug, convertUnits=True)

        typeName = type(editor).__name__
        func = self._setters.get(typeName, None)

        if callable(func):

            func(editor, value)

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
