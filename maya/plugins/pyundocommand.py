import types
import sys

from maya import cmds as mc
from maya.api import OpenMaya as om

pyundobridge = types.ModuleType('pyundobridge')
pyundobridge.__doit__ = None
pyundobridge.__undoit__ = None
sys.modules['pyundobridge'] = pyundobridge  # Required to pass data from python to the MPxCommand!

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__vendor__ = 'Ben Singleton'
__version__ = '1.0'
__command__ = 'pyUndo'


def maya_useNewAPI():
    """
    Maya python API 2.0 plugin boilerplate.

    :rtype: None
    """

    pass


class PyUndoCommand(om.MPxCommand):
    """
    Overload of `MPxCommand` that provides undo support for the latest Maya python API.
    This is done by externally modifying the `pending` dunderscore with an `MDGModifier` to be undone.
    This can be done either with decorators or `with` statements.
    """

    __slots__ = ('modifier',)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(PyUndoCommand, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self.modifier = None  # type: Tuple[Callable, Callable]

    def doIt(self, args):
        """
        This method should perform a command by setting up internal class data and then calling the redoIt method.

        :type args: om.MArgList
        :rtype: None
        """

        if callable(pyundobridge.__doit__) and callable(pyundobridge.__undoit__):

            self.modifier = pyundobridge.__doit__, pyundobridge.__undoit__

    def undoIt(self):
        """
        This method should undo the work done by the redoIt method based on the internal class data only.

        :rtype: None
        """

        doIt, undoIt = self.modifier
        undoIt()

    def redoIt(self):
        """
        This method should do the actual work of the command based on the internal class data only.
        Internal class data should be set in the `doIt` method.

        :rtype: None
        """

        doIt, undoIt = self.modifier
        doIt()

    def isUndoable(self):
        """
        This method is used to specify whether the command is undoable.

        :rtype: bool
        """

        hasModifier = hasattr(self.modifier, '__len__')

        if hasModifier:

            return len(self.modifier) == 2

        else:

            return False


def initializePlugin(plugin):
    """
    Maya plug-in initialize boilerplate.

    :type plugin: om.MObject
    :rtype: None
    """

    fnPlugin = om.MFnPlugin(plugin, __vendor__, str(__version__))
    fnPlugin.registerCommand(__command__, PyUndoCommand)


def uninitializePlugin(plugin):
    """
    Maya plug-in uninitialize boilerplate.

    :type plugin: om.MObject
    :rtype: None
    """

    fnPlugin = om.MFnPlugin(plugin)
    fnPlugin.deregisterCommand(__command__)
