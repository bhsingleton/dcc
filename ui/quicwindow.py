import os
import sys

from . import qsingletonwindow
from ..vendor.Qt import QtCore, QtWidgets, QtGui, QtCompat

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QUicWindow(qsingletonwindow.QSingletonWindow):
    """
    Overload of `QSingletonWindow` that loads windows from .ui files.
    """

    # region Dunderscores
    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Load user interface
        #
        self.preLoad(*args, **kwargs)
        self.__load__(*args, **kwargs)
        self.postLoad(*args, **kwargs)

        # Call parent method
        #
        super(QUicWindow, self).__setup_ui__(*args, **kwargs)

    def __load__(self, *args, **kwargs):
        """
        Private method used to load the user interface from the associated .ui file.
        Be sure to overload the associated class methods to augment the behavior of this method.

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

    def __getattribute__(self, item):
        """
        Private method returns an internal attribute with the associated name.
        Sadly all pointers are lost from QUicLoader, so we have to relocate them on demand.

        :type item: str
        :rtype: Any
        """

        # Call parent method
        #
        obj = super(QUicWindow, self).__getattribute__(item)

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
    # endregion
