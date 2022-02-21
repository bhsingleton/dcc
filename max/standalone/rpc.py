"""
Module used to interface with standalone 3ds Max processes.
In order to use this you would fire up an instance of StandaloneCommandPort:

from dcc.max.standalone import rpc
port = rpc.StandaloneCommandPort()
port.start()

Once the server has been binded to the default port you can fire up a client for local testing.
In production this would be executed inside the main thread.

command = rpc.StandaloneCommand('maya.cmds.ls', type='camera')
command.start()

Now you can send commands from the client which will await a response from the server.

result = command.join(timeout=1.0)
print(result)
"""
import os
import sys
import json
import socket
import threading
import subprocess
import traceback
import atexit

from dcc.max.json import mxsvalueparser

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__executable__ = os.path.join(os.path.dirname(sys.executable), '3dsmaxbatch.exe')
__server__ = None
__process__ = None
__host__ = 'localhost'
__port__ = 8000


def defaultspecs():
    """
    Returns a default specs object that's used to track command outputs.

    :rtype: dict
    """

    return {
        'success': False,
        'command': '',
        'result': None,
        'exception': '',
        'traceback': ''
    }


class StandaloneCommandPort(object):
    """
    Overload of Thread used to listen for commands from an external client.
    """

    __slots__ = ('host', 'port', 'socket', 'running')

    def __init__(self, host='localhost', port=8000):
        """
        Private method called after a new instance has been created.

        :type host: str
        :type port: int
        :rtype: None
        """

        # Call parent method
        #
        super(StandaloneCommandPort, self).__init__()

        # Declare public variables
        #
        self.host = host
        self.port = port
        self.running = True

        # Bind socket to port
        #
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(True)
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)

    def run(self):
        """
        Sends a command to the connected client to be processed.
        The main thread will wait until the results are returned.

        :rtype: None
        """

        # Wrap this thread in a try/catch
        # That way we can shut down this thread in case of an error
        #
        connection = None
        data = '{}'

        try:

            # Await for connection from client
            #
            while self.running:

                # Wait for connection
                #
                log.info('Awaiting command from client...')

                connection, address = self.socket.accept()
                log.info('Command received from client!')

                # Get message from client
                #
                io = connection.makefile('rw', newline='\n')
                data = io.readlines()[-1]

                results = self.execute(data)
                log.info(results)

                # Send results back to client
                #
                io.write(f'{results}\n')
                io.flush()
                io.close()

                # Close connection
                #
                connection.close()

        except Exception as exception:

            log.error(exception)

        finally:

            self.stop()

    def execute(self, data):
        """
        Executes the supplied command data in the main thread.

        :type data: str
        :rtype: str
        """

        # Try and execute command
        #
        specs = defaultspecs()

        try:

            # Load json data
            #
            data = json.loads(data, cls=mxsvalueparser.MXSValueDecoder)
            log.info('Executing command: %s' % data['command'])

            command = data['command']
            args = data['args']
            kwargs = data['kwargs']

            # Execute python command
            #
            specs['command'] = command

            func = eval(command)
            result = func(*args, **kwargs)

            # Record results
            #
            specs['success'] = True
            specs['result'] = result

        except Exception as exception:

            # Capture traceback message
            #
            specs['exception'] = str(exception)
            specs['traceback'] = traceback.format_exc()

        finally:

            pymxs.runtime.windows.processPostedMessages()
            return json.dumps(specs, cls=mxsvalueparser.MXSValueEncoder)

    def stop(self):
        """
        Closes the socket that is listening to the binded port.

        :rtype: None
        """

        self.running = False
        self.socket.close()


class StandaloneCommand(threading.Thread):
    """
    Client class used to interact with remote standalone Maya sessions.
    This class runs in its own thread to avoid blocking the main thread.
    """

    __slots__ = ('host', 'port', 'socket', 'command', 'results')

    def __init__(self, command, *args, host='localhost', port=8000, **kwargs):
        """
        Private method called after a new instance has been created.

        :type command: str
        :type host: str
        :type port: int
        :type buffer: int
        :rtype: None
        """

        # Call parent method
        #
        super(StandaloneCommand, self).__init__()

        # Declare class variables
        #
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.command = json.dumps({'command': command, 'args': args, 'kwargs': kwargs}, cls=mxsvalueparser.MXSValueEncoder)
        self.results = defaultspecs()

        # Set socket to block
        #
        self.socket.setblocking(True)

    def run(self):
        """
        Waits for commands from the server to be executed.
        In order to kill this thread just call shutdown from the server.

        :rtype: None
        """

        # Wrap this thread in a try/catch
        # That way we can shut down this thread in case of an error
        #
        try:

            # Connect to command port
            # This thread will block until a connection is made
            #
            log.info('Connecting to command port...')
            self.socket.connect((self.host, self.port))

            log.info('Connected to command port!')

            # Send message to server
            #
            io = self.socket.makefile('rw', newline='\n')
            io.write(f'{self.command}\n')
            io.flush()

            # Execute message
            #
            self.results = json.loads(io.readlines()[-1], cls=mxsvalueparser.MXSValueDecoder)
            io.close()

        except Exception as exception:

            log.error(exception)

        finally:

            log.info('Closing connection to command port...')
            self.socket.close()

    def join(self, timeout=10.0):
        """
        Waits for this thread to synchronize with the main thread.

        :type timeout: float
        :rtype: dict
        """

        # Call parent method
        #
        super(StandaloneCommand, self).join(timeout=timeout)

        # Return results
        #
        return self.results


def isAlive():
    """
    Checks if the mayapy subprocess is still alive.

    :rtype: bool
    """

    # Create TCP socket and check connection
    #
    sock = socket.socket()

    try:

        sock.connect(('localhost', 8000))
        return True

    except socket.error as exception:

        return False

    finally:

        sock.close()


def start():
    """
    Starts a new 3dsmaxbatch.exe subprocess in the background.

    :rtype: None
    """

    # Check if process is alive
    #
    global __process__

    if not isAlive():

        __process__ = subprocess.Popen([__executable__, __file__], shell=False)

    else:

        log.warning('Socket port is currently in use!')


def stop():
    """
    Kills the 3dsmaxbatch.exe subprocess that is running in the background.

    :rtype: None
    """

    # Check if process is alive
    #
    if isAlive():

        send('quit')


def send(command, *args, **kwargs):
    """
    Sends the supplied command and arguments to the standalone process.

    :type command: str
    :rtype: object
    """

    # Check if process is alive
    #
    if not isAlive():

        raise RuntimeError('Unable to connect to localhost:8000')

    # Run command and wait for results
    #
    cmd = StandaloneCommand(command, *args, **kwargs)
    cmd.start()

    specs = cmd.join()

    # Inspect results
    #
    log.info('Results = %s' % specs)

    if specs['success']:

        return specs['result']

    else:

        raise RuntimeError(specs['exception'])


if __name__ == '__main__':

    # Start command prompt
    #
    log.info('Starting standalone command port...')

    __server__ = StandaloneCommandPort()
    __server__.run()

    # Register exit function
    # This will close the port on quitMAX
    #
    atexit.register(__server__.stop)
