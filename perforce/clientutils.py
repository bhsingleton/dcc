import os
import getpass

from PySide2 import QtWidgets
from six.moves import collections_abc
from collections import namedtuple
from dcc import fnqt
from dcc.perforce import cmds
from dcc.perforce.decorators.relogin import relogin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


Branch = namedtuple('Branch', ['depotPath', 'clientPath'])


class ClientSpec(object):
    """
    Base class used for interfacing with client related data.
    """

    # region Dunderscores
    __slots__ = (
        'user',
        'port',
        'access',
        'name',
        'description',
        'host',
        'lineEnd',
        'options',
        'owner',
        'root',
        'stream',
        'submitOptions',
        'update',
        'view'
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(ClientSpec, self).__init__()

        # Declare public variables
        #
        self.user = args[0]
        self.port = args[1]
        self.access = kwargs.get('Access', '')
        self.name = kwargs.get('Client', '')
        self.description = kwargs.get('Description', '')
        self.host = kwargs.get('Host', '')
        self.lineEnd = kwargs.get('LineEnd', '')
        self.owner = kwargs.get('Owner', '')
        self.root = kwargs.get('Root', '')
        self.stream = kwargs.get('Stream', '')
        self.options = kwargs.get('Options', '').split(' ')
        self.submitOptions = kwargs.get('SubmitOptions', '')
        self.update = kwargs.get('Update', '')
        self.view = [self.parseView(x) for x in kwargs.get('View', [])]
    # endregion

    # region Methods
    @staticmethod
    def parseView(view):
        """
        Extrapolates the branch from the supplied client view.

        :type view: str
        :rtype: Branch
        """

        index = view.rfind('//')
        depotPath = view[:index-1].replace('/...', '')
        clientPath = view[index:].replace('/...', '')

        return Branch(depotPath, clientPath)

    def mapToView(self, depotPath):
        """
        Utilizes the client view to convert the depot path into a local path.
        No error checking is performed to see if this file exists!

        :type depotPath: str
        :rtype: str
        """

        # Get workspace mapping
        #
        found = [x for x in self.view if depotPath.startswith(x.depotPath)]
        numFound = len(found)

        if numFound == 0:

            raise TypeError(
                'The depot path: "{depotPath}", does not exist under the "{client}" client view!'.format(
                    depotPath=depotPath,
                    client=self.name
                )
            )

        # Replace client name with workspace root
        #
        branch = found[-1]

        workspaceMap = branch.clientPath.replace('//{client}'.format(client=self.name), self.root)
        localPath = depotPath.replace(branch.depotPath, workspaceMap)

        return os.path.normpath(localPath)

    def mapToRoot(self, filePath):
        """
        Utilizes the client root to convert the absolute path into a relative path.

        :type filePath: str
        :rtype: str
        """

        # Check if path is mappable
        #
        if not self.hasAbsoluteFile(filePath):

            return filePath

        # Concatenate relative path
        #
        filePath = os.path.normpath(filePath)
        clientPath = os.path.normpath(self.root)

        return os.path.relpath(filePath, clientPath)

    def mapToDepot(self, filePath):
        """
        Utilized the client view to convert the absolute path into a depot path.

        :type filePath: str
        :rtype: str
        """

        return os.path.join(self.view[0].depotPath, self.mapToRoot(filePath))

    def hasStream(self):
        """
        Evaluates whether this client has a stream associated with it.

        :rtype: bool
        """

        return not self.stream

    def hasAbsoluteFile(self, filePath):
        """
        Evaluates if the supplied file is derived from this client.

        :type filePath: str
        :rtype: bool
        """

        # Normalize system paths
        #
        filePath = os.path.normpath(filePath)
        clientPath = os.path.normpath(self.root)

        return filePath.lower().startswith(clientPath.lower())

    def getChangelists(self):
        """
        Returns a list of changelists from this client.

        :rtype: list[dict]
        """

        return cmds.changes(user=self.user, port=self.port, client=self.name, status='pending')
    # endregion


class ClientSpecs(collections_abc.MutableMapping):
    """
    Overload of MutableMapping designed to store clients associated with the current user.
    This class is capable of dynamic lookup in case the requested client couldn't be found.
    """

    # region dunderscores
    __slots__ = ('_user', '_port', '_clients')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(ClientSpecs, self).__init__()

        # Declare private variables
        #
        self._user = kwargs.get('user', os.environ.get('P4USER', getpass.getuser()))
        self._port = kwargs.get('port', os.environ.get('P4PORT', 'localhost:1666'))
        self._clients = {}

        # Populate clients
        #
        clients = cmds.clients(user=self._user, port=self._port)

        if clients is not None:

            self._clients = {x.get('Client', ''): ClientSpec(self._user, self._port, **x) for x in clients}

    def __getitem__(self, key):
        """
        Private method that returns an indexed item.

        :type key: str
        :rtype: ClientSpec
        """

        return self.get(key, default=None)

    def __setitem__(self, key, value):
        """
        Private method that updates an indexed item.

        :type key: str
        :type value: ClientSpec
        :rtype: None
        """

        # Check value type
        #
        if not isinstance(value, ClientSpec):

            raise TypeError('Unable to assign client using "%s" type!' % type(value).__name__)

        self._clients[key] = value

    def __delitem__(self, key):
        """
        Private method that deletes an indexed item.

        :type key: str
        :rtype: None
        """

        del self._clients[key]

    def __len__(self):
        """
        Private method that evaluates the number of clients belonging to this collection.

        :rtype: int
        """

        return len(self._clients)

    def __iter__(self):
        """
        Private method that returns a generator that yields all clients from this collection.

        :rtype: iter
        """

        return iter(self._clients)
    # endregion

    # region Properties
    @property
    def user(self):
        """
        Getter method used to retrieve the username associated with these clients.

        :rtype: str
        """

        return self._user

    @user.setter
    def user(self, username):
        """
        Setter method used to update the global perforce username for this session.

        :type username: str
        :rtype: None
        """

        self._user = username
        self.refresh()

    @property
    def port(self):
        """
        Getter method used to retrieve the port associated with these clients.

        :rtype: str
        """

        return self._port

    @port.setter
    def port(self, port):
        """
        Setter method used to update the global perforce port for this session.

        :type port: str
        :rtype: None
        """

        self._port = port
        self.refresh()
    # endregion

    # region Methods
    def get(self, key, default=None):
        """
        Returns an index item from this collection with any exceptions.
        This method will attempt to fetch the client if there currently is no key-value pair.

        :type key: str
        :type default: object
        :rtype: ClientSpec
        """

        # Check if item exists
        #
        clientSpec = self._clients.get(key, None)

        if clientSpec is None:

            # Get client specs
            #
            specs = cmds.client(key)

            if specs is None:

                log.warning('Unable to fetch "%s" client from perforce!' % key)
                return default

            # Assign new client using specs
            #
            clientSpec = ClientSpec(**specs)
            self._clients[key] = clientSpec

            return clientSpec

        else:

            return clientSpec

    def keys(self):
        """
        Returns a keys view into this collection.

        :rtype: collection_abc.KeysView
        """

        return self._clients.keys()

    def values(self):
        """
        Returns a values view into this collection.

        :rtype: collection_abc.ValuesView
        """

        return self._clients.values()

    def items(self):
        """
        Returns an items view into this collection.

        :rtype: collection_abc.ItemsView
        """

        return self._clients.items()

    def clear(self):
        """
        Removes all of the items from this collection.

        :rtype: None
        """

        self._clients.clear()

    def refresh(self):
        """
        Method used to recollect all of the available clients based on the username and port.
        Refer to the following  environment variables for details: "P4USER" and "P4PORT"

        :rtype: None
        """

        self._clients.clear()
        self._clients = {x['Client']: ClientSpec(**x) for x in cmds.clients(user=self._user, port=self._port)}
    # endregion


def getClientByName(name):
    """
    Returns a client associated with the given name.
    If no client is found then none is returned!

    :type name: str
    :rtype: ClientSpec
    """

    return __clientspecs__.get(name, None)


def getCurrentClient():
    """
    Returns the current client using the P4CLIENT environment variable.

    :rtype: ClientSpec
    """

    return getClientByName(os.environ.get('P4CLIENT', ''))


def getClientNames():
    """
    Returns a list of client names.

    :rtype: list[str]
    """

    return list(__clientspecs__.keys())


def iterClients():
    """
    Returns a generator that yields all client key-value pairs.

    :rtype: iter
    """

    return iter(__clientspecs__.items())


def setClient(client):
    """
    Updates the current client.

    :type client: str
    :rtype: None
    """

    # Check if client requires updating
    #
    if client == os.environ['P4CLIENT']:

        return

    # Update environment variables to reflect change
    #
    clientSpec = __clientspecs__[client]
    log.info('Switching workspace to: "%s"' % clientSpec.name)

    os.environ['P4CLIENT'] = clientSpec.name
    os.environ['P4ROOT'] = clientSpec.root


def changeClient():
    """
    Prompts the user to changes the current client.
    Right now this method is restricted to listing only clients associated with the host.

    :rtype: None
    """

    # Collect all clients
    #
    fnQt = fnqt.FnQt()
    parent = fnQt.getMainWindow()

    clients = [x for (x, y) in __clientspecs__.items() if y.host == os.environ['P4HOST']]
    numClients = len(clients)

    if numClients == 0:

        QtWidgets.QMessageBox.warning(parent, 'Change Client', 'Current host has no perforce workspaces!')
        return

    # Get previous client
    #
    client = os.environ['P4CLIENT']
    current = 0

    if client in clients:

        current = clients.index(client)

    # Prompt user for new client
    #
    newClient, response = QtWidgets.QInputDialog.getItem(
        parent,
        'Change Workspace',
        'Workspaces:',
        clients,
        current=current,
        editable=False
    )

    # Check if user response
    #
    if response and newClient != client:

        setClient(newClient)


def detectClient(filePath):
    """
    Returns the client associated with the given file path.
    This method expects the given path to contain an environment variable!

    :type filePath: str
    :rtype: ClientSpec
    """

    # Check if path contains variable
    #
    if not filePath.startswith('$P4ROOT'):

        raise TypeError('Unable to detect client from unresolved file path!')

    # Iterate through clients
    #
    strings = filePath.split(os.path.sep)

    for (client, clientSpec) in __clientspecs__.items():

        # Concatenate client path
        #
        clientPath = '//{client}/{path}'.format(client=client, path='/'.join(strings[1:]))
        fileSpecs = cmds.files(clientPath, client=client)

        if fileSpecs is not None:

            return client

    # Prompt user
    #
    log.warning('Unable to find client associated with: "%s"' % filePath)
    return None


def initializeClients():
    """
    Initializes the client specs for the current session.
    Any expired tickets will be resolved through the decorator!

    :rtype: ClientSpecs
    """

    return ClientSpecs(
        user=os.environ.get('P4USER', getpass.getuser()),
        port=os.environ.get('P4PORT', 'localhost:1666')
    )


__clientspecs__ = initializeClients()
