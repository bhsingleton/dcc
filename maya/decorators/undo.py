import maya.cmds as mc

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Undo(object):
    """
    Base class used to manage undo chunks either as a decorator or with statement.
    """

    __slots__ = ('func', 'wrapper', 'name')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :type enabled: bool
        :type name: str
        :rtype: None
        """

        # Call parent method
        #
        super(Undo, self).__init__()

        # Declare public variables
        #
        self.func = None
        self.name = ''

        # Inspect arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            # Inspect argument type
            #
            arg = args[0]

            if callable(arg):

                self.func = arg
                self.name = self.func.__name__

            else:

                self.name = arg

        else:

            raise TypeError('Undo() expects 1 argument (%s given)!' % numArgs)

    def __call__(self, *args, **kwargs):
        """
        Private method that is called whenever this instance is evoked.

        :rtype: Any
        """

        # Check if function is callable
        #
        if not callable(self.func):

            # Store reference to unbound method
            #
            self.func = args[0]

            def wrapper(*args, **kwargs):

                self.__enter__()
                results = self.func(*args, **kwargs)
                self.__exit__(None, None, None)

                return results

            return wrapper

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

        mc.undoInfo(openChunk=True, chunkName=self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Private method that is called when this instance is exited using a with statement.

        :type exc_type: Any
        :type exc_val: Any
        :type exc_tb: Any
        :rtype: None
        """

        mc.undoInfo(closeChunk=True)


def undo(*args, **kwargs):
    """
    Returns an undo wrapper for the supplied function.

    :rtype: method
    """

    return Undo(*args, **kwargs).__call__
