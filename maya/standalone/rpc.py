import os
import sys
import subprocess

from maya import cmds as mc, standalone
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from xmlrpc.client import ServerProxy, Transport
from http.client import HTTPConnection
from collections.abc import Sequence

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__process__ = None
__client__ = None


class MRPCServer(SimpleXMLRPCServer):
    """
    Overload of `SimpleXMLRPCServer` that allows you to send XML-RPC requests to a standalone Maya instance.
    """

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :type requestHandler: SimpleXMLRPCRequestHandler
        :type logRequests: bool
        :type allow_none: bool
        :type encoding: Union[str, None]
        :type bind_and_activate: bool
        :type use_builtin_types: bool
        :rtype: None
        """

        # Call parent method
        #
        super(MRPCServer, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._currentFilePath = ''
        self._currentFilename = ''
        self._currentName = ''
        self._currentExtension = ''
        self._currentDirectory = ''
        self._currentType = ''
        self._standalone = self.isBatchMode()

        # Register functions
        #
        self.register_function(self.quit, 'quit')
        self.register_function(self.open, 'open')
        self.register_function(self.save, 'save')
        self.register_function(self.ls, 'ls')
        self.register_function(self.createNode, 'createNode')
        self.register_function(self.parent, 'parent')
        self.register_function(self.addAttr, 'addAttr')
        self.register_function(self.setAttr, 'setAttr')
        self.register_function(self.deleteAttr, 'deleteAttr')
        self.register_function(self.connectAttr, 'connectAttr')
        self.register_function(self.deleteNode, 'deleteNode')

        # Initialize standalone mode
        #
        if self.standalone:

            standalone.initialize()
    # endregion

    # region Properties
    @property
    def currentFilePath(self):
        """
        Getter method that returns the current file path.

        :rtype: str
        """

        return self._currentFilePath

    @property
    def currentFilename(self):
        """
        Getter method that returns the current filename.

        :rtype: str
        """

        return self._currentFilename

    @property
    def currentDirectory(self):
        """
        Getter method that returns the current directory.

        :rtype: str
        """

        return self._currentDirectory

    @property
    def isNewScene(self):
        """
        Getter method that returns the new scene flag.

        :rtype: bool
        """

        return self.isNullOrEmpty(self.currentFilePath)

    @property
    def standalone(self):
        """
        Getter method that returns the standalone flag.

        :rtype: bool
        """

        return self._standalone
    # endregion

    # region Methods
    @staticmethod
    def isNullOrEmpty(value):
        """
        Evaluates if the supplied value is a null or empty.

        :type value: Any
        :rtype: bool
        """

        if isinstance(value, Sequence):

            return len(value) == 0

        else:

            return value is None

    @staticmethod
    def isBatchMode():
        """
        Evaluates if Maya is running in batch mode.

        :rtype: bool
        """

        return sys.executable.lower().endswith('mayapy.exe')

    def register_function(self, function, name=None):
        """
        Register a function that can respond to XML-RPC requests.
        See the following for details: https://stackoverflow.com/questions/119802/using-kwargs-with-simplexmlrpcserver-in-python

        :type function: Callable
        :type name: Union[str, None]
        :rtype: Callable
        """

        # Define function wrapper
        #
        def wrapper(args, kwargs):

            return function(*args, **kwargs)

        # Check if a name was supplied
        #
        if not self.isNullOrEmpty(name):

            wrapper.__name__ = name

        # Call parent method
        #
        return super(MRPCServer, self).register_function(wrapper, name)

    def open(self, filePath, force=True):

        filePath = os.path.abspath(filePath)
        success = True

        try:

            mc.file(filePath, open=True, prompt=False, force=force)

        except RuntimeError as exception:

            log.error(exception)
            success = False

        finally:

            self._currentFilePath = filePath
            self._currentDirectory, self._currentFilename = os.path.split(self._currentFilePath)
            self._currentName, self._currentExtension = os.path.splitext(self._currentFilename)
            self._currentType = 'mayaAscii' if self._currentExtension.lower() == '.ma' else 'mayaBinary'

            return success

    def save(self):

        if self.isNewScene:

            return False

        success = True

        try:

            mc.file(save=True, prompt=False, type=self._currentType)

        except RuntimeError as exception:

            log.error(exception)
            success = False

        finally:

            return success

    def ls(self, *args, **kwargs):

        results = []

        try:

            results = mc.ls(*args, **kwargs)

        except RuntimeError as exception:

            log.error(exception)

        finally:

            return results

    def createNode(self, typeName, name='', parent=None, shared=False, skipSelect=True):
        """
        Returns a new scene node of the specified type.

        :type typeName: str
        :type name: str
        :type parent: Union[str, None]
        :type shared: bool
        :type skipSelect: bool
        :rtype: str
        """

        absoluteName = None

        try:

            absoluteName = mc.createNode(
                typeName,
                name=name,
                parent=parent,
                shared=shared,
                skipSelect=skipSelect
            )

        except RuntimeError as exception:

            log.error(exception)

        finally:

            return absoluteName

    def parent(self, *nodes, **kwargs):
        """
        Parents the first supplied nodes to the last node.

        :type nodes: List[str]
        :key absolute: bool
        :key relative: bool
        :key shape: bool
        :key world: bool
        :rtype: str
        """

        return mc.parent(*nodes, **kwargs)

    def addAttr(self, node, **kwargs):
        """
        Adds an attribute to the supplied node.

        :type node: str
        :key longName: str
        :key attributeType: str
        :rtype: bool
        """

        success = True

        try:

            mc.addAttr(node, **kwargs)

        except RuntimeError as exception:

            log.error(exception)
            success = False

        finally:

            return success

    def setAttr(self, attribute, value, **kwargs):

        success = True

        try:

            mc.setAttr(attribute, value, **kwargs)

        except RuntimeError as exception:

            log.error(exception)
            success = False

        finally:

            return success

    def deleteAttr(self, attribute, **kwargs):
        """
        Deletes the attribute on the supplied node.

        :type attribute: str
        :key attribute: str
        :rtype: bool
        """

        success = True

        try:

            mc.deleteAttr(attribute, **kwargs)

        except RuntimeError as exception:

            log.error(exception)
            success = False

        finally:

            return success

    def connectAttr(self, attribute, otherAttribute, **kwargs):
        """
        Connects the first attribute to the second attribute.

        :type attribute: str
        :type otherAttribute: str
        :key force: bool
        :rtype: bool
        """

        success = True

        try:

            mc.connectAttr(attribute, otherAttribute, **kwargs)

        except RuntimeError as exception:

            log.error(exception)
            success = False

        finally:

            return success

    def deleteNode(self, nodes, **kwargs):
        """
        Deletes the supplied nodes.

        :type nodes: List[str]
        :rtype: bool
        """

        success = True

        try:

            mc.delete(*nodes, **kwargs)

        except RuntimeError as exception:

            log.error(exception)
            success = False

        finally:

            return success

    def quit(self):

        self._BaseServer__shutdown_request = True

        if self.standalone:

            standalone.uninitialize()

        return 0


class MRPCClient(ServerProxy):
    """
    Overload of `ServerProxy` that interacts with `MRPCServer` instances.
    TODO: Look into a failsafe that forces the server to quit when the client is sent to garbage collection!
    """

    def __getattr__(self, name):
        """
        Private method that looks up a class member by name.

        :type name: str
        :rtype: Any
        """

        # Call parent method
        #
        function = super(MRPCClient, self).__getattr__(name)

        # Define function wrapper
        #
        def wrapper(*args, **kwargs):

            return function(args, kwargs)

        return wrapper


class TimeoutTransport(Transport):
    """
    Overload of `Transport` that adds timeout support.
    """

    def __init__(self, timeout):

        # Call parent method
        #
        super(TimeoutTransport, self).__init__()

        # Declare public variables
        #
        self.timeout = timeout

    def make_connection(self, host):
        """
        Returns a new connection to the specified host.

        :type host: str
        :rtype: HTTPConnection
        """

        return HTTPConnection(host, timeout=self.timeout)


def initializeRemoteStandalone(port=8000, timeout=5):
    """
    Opens a headerless Maya process in the background to send commands to.

    :type port: int
    :type timeout: int
    :rtype: Union[Tuple[subprocess.Popen, MRPCClient], Tuple[None, None]]
    """

    global __process__, __client__

    # Check if process has already been initialized
    #
    if isinstance(__process__, subprocess.Popen) and isinstance(__client__, MRPCClient):

        return __process__, __client__

    # Check if required executable exists
    #
    cwd, filename = os.path.split(sys.executable)
    executable = os.path.join(cwd, 'mayapy.exe')

    if not os.path.isfile(executable):

        return None, None

    # Create new process and client
    #
    __process__ = subprocess.Popen([executable, __file__, str(port)])
    __client__ = MRPCClient(
        f'http://localhost:{port}',
        allow_none=True,
        use_builtin_types=True,
        transport=TimeoutTransport(timeout=timeout)
    )

    return __process__, __client__


def main(port=8000):
    """
    Main entry point for remote servers.
    This function is only intended for use only by the `initializeRemoteStandalone` function!

    :type port: int
    :rtype: None
    """

    with MRPCServer(('localhost', port), requestHandler=SimpleXMLRPCRequestHandler) as server:

        log.info('Starting remote server...')
        server.serve_forever()

    quit(0)


if __name__ == '__main__':

    numArgs = len(sys.argv)
    filePath, port = (sys.argv[0], int(sys.argv[1])) if (numArgs == 2) else (sys.argv[0], 8000)

    main(port=port)
