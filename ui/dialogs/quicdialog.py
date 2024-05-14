import os
import sys

from Qt import QtCore, QtWidgets, QtGui, QtCompat
from .. import resources
from ..abstract import qabcmeta
from ...decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QUicDialog(QtWidgets.QDialog, metaclass=qabcmeta.QABCMeta):
    """
    Overload of `QUicMixin` and `QDialog` that dynamically creates dialogs at runtime.
    """

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key f: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        parent = kwargs.pop('parent', QtWidgets.QApplication.activeWindow())
        f = kwargs.pop('f', QtCore.Qt.WindowFlags())

        super(QUicDialog, self).__init__(parent=parent, f=f)

    def __post_init__(self, *args, **kwargs):
        """
        Private method called after an instance has initialized.

        :rtype: None
        """

        # Edit dialog properties
        #
        modal = kwargs.get('modal', True)

        self.setObjectName(self.className)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Dialog)
        self.setModal(modal)

        # Execute load operations
        #
        self.preLoad(*args, **kwargs)
        self.__load__(*args, **kwargs)
        self.postLoad(*args, **kwargs)

        # Update dialog state
        #
        self.__setstate__(kwargs)

    def __getattribute__(self, item):
        """
        Private method returns an internal attribute with the associated name.
        Sadly all pointers are lost from QUicLoader, so we have to relocate them on demand.

        :type item: str
        :rtype: Any
        """

        # Call parent method
        #
        obj = super(QUicDialog, self).__getattribute__(item)

        if isinstance(obj, QtCore.QObject):

            # Check if C++ pointer is still valid
            #
            if not QtCompat.isValid(obj):

                obj = self.findChild(QtCore.QObject, item)
                setattr(self, item, obj)

                return obj

            else:

                return obj

        else:

            return obj

    def __setstate__(self, state):
        """
        Private method that inherits the contents of the pickled object.

        :type state: dict
        :rtype: None
        """

        # Iterate through items
        #
        for (key, value) in state.items():

            # Check if class has property
            #
            func = getattr(self.__class__, key, None)

            if not isinstance(func, property):

                continue

            # Check if property is settable
            #
            if callable(func.fset):

                func.fset(self, value)

    def __load__(self, *args, **kwargs):
        """
        Private method used to load the user interface from the associated .ui file.

        :rtype: QtWidgets.QWidget
        """

        # Concatenate ui path
        #
        filename = self.filename()
        workingDirectory = kwargs.get('workingDirectory', self.workingDirectory())

        filePath = os.path.join(workingDirectory, filename)

        # Load ui from file
        #
        if os.path.exists(filePath):

            log.info(f'Loading UI file: {filePath}')
            return QtCompat.loadUi(uifile=filePath, baseinstance=self)

        else:

            log.debug(f'Cannot locate UI file: {filePath}')
            return self
    # endregion

    # region Properties
    @classproperty
    def className(cls):
        """
        Getter method that returns the name of this class.

        :rtype: str
        """

        return cls.__name__
    # endregion

    # region Events
    def showEvent(self, event):
        """
        Event method called after the window has been shown.

        :type event: QtGui.QShowEvent
        :rtype: None
        """

        # Call parent method
        #
        super(QUicDialog, self).showEvent(event)

        # Recenter dialog
        #
        self.centerToParent()
    # endregion

    # region Methods
    @classmethod
    def filename(cls):
        """
        Returns the ui configuration filename for this class.
        This defaults to the name of this python file.

        :rtype: str
        """

        filePath = os.path.abspath(sys.modules[cls.__module__].__file__)
        directory, filename = os.path.split(filePath)
        name, ext = os.path.splitext(filename)

        return '{name}.ui'.format(name=name)

    @classmethod
    def workingDirectory(cls):
        """
        Returns the working directory for this class.
        This defaults to the directory this python file resides in.

        :rtype: str
        """

        return os.path.dirname(os.path.abspath(sys.modules[cls.__module__].__file__))

    def preLoad(self, *args, **kwargs):
        """
        Called before the user interface has been loaded.

        :rtype: None
        """

        pass

    def postLoad(self, *args, **kwargs):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        pass

    def centerToParent(self):
        """
        Centers this dialog to its current parent.

        :rtype: None
        """

        window = self.parentWidget().window()
        offset = window.geometry().center() - self.geometry().center()

        self.move(offset)
    # endregion
