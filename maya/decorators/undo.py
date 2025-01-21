import os
import sys

from maya import cmds as mc
from ...python import stringutils
from ...decorators import abstractdecorator

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Undo(abstractdecorator.AbstractDecorator):
    """
    Overload of `AbstractDecorator` that defines Maya undo chunks.
    """

    # region Dunderscores
    __slots__ = ('_state', '_name', '_exception')
    __chunk__ = None  # Prevents nested undo chunks from closing prematurely
    __plugin__ = 'pyundocommand.py'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :type enabled: bool
        :type name: str
        :rtype: None
        """

        # Call parent method
        #
        super(Undo, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._name = kwargs.get('name', '').replace(' ', '_')
        self._state = kwargs.get('state', True)
        self._exception = None

    def __enter__(self, *args, **kwargs):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        # Evaluate undo state
        #
        if self.state:

            # Check if chunk is already open
            #
            if not stringutils.isNullOrEmpty(self.chunk):

                return

            # Ensure API undo is loaded
            #
            self.ensureLoaded()

            # Open undo chunk
            #
            self.__class__.__chunk__ = self.name
            mc.undoInfo(openChunk=True, chunkName=self.name)

        else:

            # Disable undo
            #
            mc.undoInfo(stateWithoutFlush=False)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Private method that is called when this instance is exited using a with statement.

        :type exc_type: Any
        :type exc_val: Any
        :type exc_tb: Any
        :rtype: None
        """

        # Evaluate undo state
        #
        if self.state:

            # Check if active chunk names match
            # If so, go ahead and close the undo chunk!
            #
            log.debug(f'Open undo chunk: {self.chunk}, current undo chunk: {self.name}')

            if self.name == self.chunk:

                self.__class__.__chunk__ = None
                mc.undoInfo(closeChunk=True)

        else:

            # Re-enable undo
            #
            mc.undoInfo(stateWithoutFlush=True)

        # Check if any exceptions were raised
        # If so, go ahead and raise them now that undo has been re-enabled!
        #
        if isinstance(self._exception, Exception):
            
            exception, self._exception = self._exception, None
            raise exception
    # endregion

    # region Properties
    @property
    def chunk(self):
        """
        Getter method that returns the current undo chunk.

        :rtype: Union[str, None]
        """

        return self.__class__.__chunk__

    @property
    def name(self):
        """
        Getter method that returns the name of this undo.

        :rtype: str
        """

        return self._name

    @property
    def state(self):
        """
        Getter method that returns the undo state.

        :rtype: bool
        """

        return self._state

    @property
    def exception(self):
        """
        Getter method that returns any exceptions from this chunk.

        :rtype: Union[Exception, None]
        """

        return self._exception
    # endregion

    # region Methods
    def wrap(self, func):
        """
        Returns a wrapper for the supplied function.

        :type func: FunctionType
        :rtype: FunctionType
        """

        def wrapper(*args, **kwargs):

            results = None

            try:

                self.__enter__(*args, **kwargs)
                results = func(*args, **kwargs)

            except Exception as exception:  # This allows us to re-enable undo for any exception!

                self._exception = exception

            finally:

                self.__exit__(None, None, None)
                return results

        return wrapper

    def exists(self):
        """
        Evaluates if the `pyUndo` command plugin exists.

        :rtype: bool
        """

        paths = os.environ.get('MAYA_PLUG_IN_PATH', '').split(';')
        filePaths = [os.path.join(os.path.abspath(path), self.__plugin__) for path in paths if not stringutils.isNullOrEmpty(path)]
        filteredPaths = list(filter(os.path.exists, filePaths))

        return len(filteredPaths) == 1

    def isLoaded(self):
        """
        Evaluates if the `pyUndo` command plugin has been loaded.

        :rtype: bool
        """

        return mc.pluginInfo(self.__plugin__, query=True, loaded=True)

    def ensureLoaded(self):
        """
        Loads the `pyUndo` command plugin.

        :rtype: None
        """

        # Check if plug-in is already loaded
        #
        isLoaded = self.isLoaded()

        if isLoaded:

            return

        # Check if plug-in exists
        #
        exists = self.exists()

        if exists:

            mc.loadPlugin(self.__plugin__, quiet=True)

        else:

            log.debug(f'Unable to locate "{self.__plugin__}" plugin!')
    # endregion


def commit(doIt, undoIt):
    """
    Passes the supplied functions to the py-undo bridge.

    :type doIt: Callable
    :type undoIt: Callable
    :rtype: None
    """

    pyundobridge = sys.modules.get('pyundobridge')

    if pyundobridge is not None:

        log.debug(f'Sending: {doIt}, {undoIt} to py-undo bridge!')
        pyundobridge.__doit__ = doIt
        pyundobridge.__undoit__ = undoIt

        mc.pyUndo()

    else:

        log.debug('Cannot locate py-undo bridge!')


def commitAndDoIt(doIt, undoIt):
    """
    Passes the supplied functions to the py-undo bridge and executes them.

    :type doIt: Callable
    :type undoIt: Callable
    :rtype: None
    """

    commit(doIt, undoIt)
    doIt()
