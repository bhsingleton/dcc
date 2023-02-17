import os
import sys

from Qt import QtCore, QtWidgets, QtCompat
from . import qmetaclass

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QUicMixin(object, metaclass=qmetaclass.QMetaclass):
    """
    Mixin class used to dynamically create layouts at runtime via .ui files.
    This class must come first when declaring your derived classes to avoid MRO clashes!
    For connections Qt expects the following slot syntax: on_{objectName}_{signalName} complete with a slot decorator!
    """

    # region Dunderscores
    def __post_init__(self, *args, **kwargs):
        """
        Private method called after an instance has initialized.

        :rtype: None
        """

        self.preLoad(*args, **kwargs)
        self.__load__(*args, **kwargs)
        self.postLoad(*args, **kwargs)

    def __getattribute__(self, item):
        """
        Private method returns an internal attribute with the associated name.
        Sadly all pointers are lost from QUicLoader, so we have to relocate them on demand.

        :type item: str
        :rtype: Any
        """

        # Call parent method
        #
        obj = super(QUicMixin, self).__getattribute__(item)

        if isinstance(obj, QtWidgets.QWidget):

            # Check if cpp pointer is still valid
            #
            if not QtCompat.isValid(obj):

                obj = self.findChild(QtWidgets.QWidget, item)
                setattr(self, item, obj)

                return obj

            else:

                return obj

        else:

            return obj

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
        log.info('Loading UI file: %s' % filePath)
        return QtCompat.loadUi(uifile=filePath, baseinstance=self)
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
