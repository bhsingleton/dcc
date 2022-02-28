import os
import getpass

from six.moves import collections_abc
from dcc.perforce import cmds
from dcc.perforce.decorators.relogin import relogin

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class DepotSpec(object):
    """
    Base class used for interfacing with depot related data.
    """

    # region Dunderscores
    __slots__ = (
        'date',
        'name',
        'description',
        'map',
        'owner',
        'streamDepth',
        'type'
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(DepotSpec, self).__init__()

        # Declare public variables
        #
        self.date = kwargs.get('Date', '')
        self.name = kwargs.get('Depot', '')
        self.description = kwargs.get('Description', '')
        self.map = kwargs.get('Map', '')
        self.owner = kwargs.get('Owner', '')
        self.streamDepth = kwargs.get('StreamDepth', '')
        self.type = kwargs.get('Type', '')
    # endregion


class DepotSpecs(collections_abc.MutableMapping):
    """
    Overload of MutableMapping designed to store depot specs associated with the current user.
    """

    # region Dunderscores
    __slots__ = ('_user', '_port', '_depots')

    def __init__(self, *args, **kwargs):
        """
        Private method that is called after a new instance is created.
        """

        # Call parent method
        #
        super(DepotSpecs, self).__init__()

        # Declare private variables
        #
        self._user = kwargs.get('user', os.environ.get('P4USER', getpass.getuser()))
        self._port = kwargs.get('port', os.environ.get('P4PORT', 'localhost:1666'))

        self._depots = {x['Depot']: DepotSpec(**x) for x in cmds.depots(user=self._user, port=self._port)}

    def __getitem__(self, key):
        """
        Private method that returns an indexed item.

        :type key: str
        :rtype: DepotSpec
        """

        return self.get(key, default=None)

    def __setitem__(self, key, value):
        """
        Private method that updates an indexed item.

        :type key: str
        :type value: DepotSpec
        :rtype: None
        """

        # Check value type
        #
        if not isinstance(value, DepotSpec):

            raise TypeError('Unable to assign depot using "%s" type!' % type(value).__name__)

        self._depots[key] = value

    def __delitem__(self, key):
        """
        Private method that deletes an indexed item.

        :type key: str
        :rtype: None
        """

        del self._depots[key]

    def __len__(self):
        """
        Private method that evaluates the number of depots belonging to this collection.

        :rtype: int
        """

        return len(self._depots)

    def __iter__(self):
        """
        Private method that returns a generator that yields all depot from this collection.

        :rtype: iter
        """

        return iter(self._depots)
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
        Inherited method used to safely retrieve a value from this instance with a default option.
        This method will attempt to fetch the client if un-successful.

        :type key: str
        :type default: object
        :rtype: ClientSpec
        """

        # Check if item exists
        #
        depotSpec = self._depots.get(key, None)

        if depotSpec is None:

            # Get client specs
            #
            specs = cmds.depot(key)

            if specs is None:

                log.warning('Unable to fetch "%s" depot from perforce!' % key)
                return default

            # Assign new client using specs
            #
            depotSpec = DepotSpec(**specs)
            self._depots[key] = depotSpec

            return depotSpec

        else:

            return depotSpec

    def keys(self):
        """
        Inherited method used to retrieve all keys belonging to this instance.

        :rtype: list
        """

        return self._depots.keys()

    def values(self):
        """
        Inherited method used to retrieve all values belonging to this instance.

        :rtype: list
        """

        return self._depots.values()

    def clear(self):
        """
        Inherited method used to clear all the items belonging to this instance.

        :rtype: None
        """

        self._depots.clear()

    def refresh(self):
        """
        Method used to recollect all of the available depots based on the username and port.
        Refer to the following  environment variables for details: "P4USER" and "P4PORT"

        :rtype: None
        """

        self.clear()
        self.update({x['Depot']: x for x in cmds.depots(user=self.user, port=self.port)})
    # endregion


def getDepot(depot):
    """
    Method used to retrieve the specs associated with the supplied depot name.

    :type depot: str
    :rtype: DepotSpec
    """

    return __depotspecs__.get(depot, None)


def getDepotNames():
    """
    Method used to retrieve all of the available depots belonging to the current user.

    :rtype: list[str]
    """

    return list(__depotspecs__.keys())


def iterDepots():
    """
    Method used to retrieve a generator that can iterate through all depots available to the user.

    :rtype: iter
    """

    return iter(__depotspecs__.items())


@relogin
def initializeDepots():
    """
    Initializes the depot specs for the current session.
    Any expired tickets will be resolved through the decorator!

    :rtype: DepotSpecs
    """

    return DepotSpecs(
        user=os.environ.get('P4USER', getpass.getuser()),
        port=os.environ.get('P4PORT', 'localhost:1666')
    )


__depotspecs__ = initializeDepots()
