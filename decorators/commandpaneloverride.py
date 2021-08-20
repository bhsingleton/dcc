import pymxs

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class CommandPanelOverride(object):
    """
    Class decorator used to override the command panel task mode at runtime.
    """

    __slots__ = ('function', 'mode')

    def __init__(self, mode):
        """
        Private method called after a new instance has been created.

        :type mode: str
        :rtype: None
        """

        self.mode = pymxs.runtime.name(mode)

    def __call__(self, func):
        """
        Private method that is called whenever this instance is evoked.

        :type func: method
        :rtype: Any
        """

        # Define function wrapper
        #
        def wrapper(*args, **kwargs):

            # Inspect current task mode
            #
            currentMode = pymxs.runtime.getCommandPanelTaskMode()

            if currentMode != self.mode:

                pymxs.runtime.setCommandPanelTaskMode(self.mode)

            # Inspect selected node
            #
            shape = args[0].shape()

            if not shape.isSelected:

                pymxs.runtime.select(shape)

            return func(*args, **kwargs)

        return wrapper
