import pymxs

from .. import fnnode

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class CommandPanelOverride(object):
    """
    Class decorator used to override the command panel task mode at runtime.
    """

    __slots__ = ('func', 'mode', 'autoSelect')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(CommandPanelOverride, self).__init__()

        # Declare public variables
        #
        self.func = None
        self.mode = None
        self.autoSelect = kwargs.get('autoSelect', True)

        # Inspect arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            # Inspect argument type
            #
            arg = args[0]

            if callable(arg):

                self.func = arg
                self.mode = pymxs.runtime.getCommandPanelTaskMode()

            else:

                self.mode = pymxs.runtime.name(arg)

        else:

            raise TypeError('Undo() expects 1 argument (%s given)!' % numArgs)

    def __call__(self, *args, **kwargs):
        """
        Private method that is called whenever this instance is evoked.

        :type func: method
        :rtype: Any
        """

        # Check if function is callable
        #
        if not callable(self.func):

            # Store reference to function
            #
            self.func = args[0]
            return self.__call__

        else:

            # Wrap internal function
            #
            self.__enter__()
            results = self.func(*args, **kwargs)
            self.__exit__(None, None, None)

            return results

    def __enter__(self):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        # Inspect current task mode
        #
        currentMode = pymxs.runtime.getCommandPanelTaskMode()

        if currentMode != self.mode:

            pymxs.runtime.setCommandPanelTaskMode(self.mode)

        # Check if auto select is enabled
        #
        obj = self.func.im_self

        if self.autoSelect and isinstance(obj, fnnode.FnNode):

            obj.select()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Private method that is called when this instance is exited using a with statement.

        :type exc_type: Any
        :type exc_val: Any
        :type exc_tb: Any
        :rtype: None
        """

        pass


def commandpaneloverride(*args, **kwargs):
    """
    Returns an command panel override wrapper for the supplied function.

    :rtype: method
    """

    return CommandPanelOverride(*args, **kwargs).__call__
