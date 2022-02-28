import os
import inspect
import shiboken2

from PySide2 import QtCore, QtWidgets, QtGui
from dcc.ui import quicloader

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QUicInterface(object):
    """
    Abstract class used with Qt widgets to create layouts at runtime via .ui files.
    This class must come first when declaring your base classes!
    """

    # region Dunderscores
    def __getattribute__(self, item):
        """
        Private method used to lookup an attribute.
        Sadly all pointers are lost from QUicLoader so we have to rebuild them on demand.

        :type item: str
        :rtype: QtCore.QObject
        """

        # Call parent method
        #
        obj = super(QUicInterface, self).__getattribute__(item)

        if isinstance(obj, QtWidgets.QWidget):

            # Check if cpp pointer is still valid
            #

            if not shiboken2.isValid(obj):

                obj = self.findChild(QtWidgets.QWidget, item)
                setattr(self, item, obj)

            return obj

        else:

            return obj

    def __load__(self, *args, **kwargs):
        """
        Private method used to load the user interface from the associated .ui file.
        Be sure to overload the associated class methods to augment the behavior of this method.

        :rtype: QtWidgets.QWidget
        """

        # Initialize qt loader
        #
        customWidgets = kwargs.get('customWidgets', self.customWidgets())
        workingDirectory = kwargs.get('workingDirectory', self.workingDirectory())

        loader = quicloader.QUicLoader(self, customWidgets=customWidgets, workingDirectory=workingDirectory)

        # Load the .ui file
        #
        filePath = os.path.join(self.workingDirectory(), self.filename())

        log.info('Loading UI file: %s' % filePath)
        widget = loader.load(filePath)

        # Automate signal/slot connections
        # Qt expects the following method names: on_{objectName}_{signal} complete with a QtCore.Slot decorator!
        #
        QtCore.QMetaObject.connectSlotsByName(widget)

        return widget
    # endregion

    # region Methods
    @classmethod
    def filename(cls):
        """
        Returns the ui configuration filename for this class.
        This defaults to the name of this python file.

        :rtype: str
        """

        filePath = inspect.getfile(cls)
        directory, filename = os.path.split(filePath)
        name, ext = os.path.splitext(filename)

        return '{name}.ui'.format(name=name)

    @classmethod
    def customWidgets(cls):
        """
        Returns a dictionary of custom widgets used by this class.
        Overload this method to extend this dictionary!

        :rtype: dict[str:type]
        """

        return {}

    @classmethod
    def workingDirectory(cls):
        """
        Returns the working directory for this class.
        This defaults to the directory this python file resides in.

        :rtype: str
        """

        return os.path.dirname(inspect.getfile(cls))

    def preLoad(self):
        """
        Called before the user interface has been loaded.

        :rtype: None
        """

        pass

    def postLoad(self):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        pass
    # endregion
