import os

from collections import defaultdict
from dcc.perforce import clientutils, cmds

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class SearchEngine(object):
    """
    Search class used for locating files on perforce.
    This classes also records search history for faster lookups.
    History is broken down by client first then search value.
    """

    __slots__ = ('_history',)

    def __init__(self):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(SearchEngine, self).__init__()

        # Declare class variables
        #
        self._history = defaultdict(dict)

    def history(self, client):
        """
        Returns the search history for the given client.

        :type client: str
        :rtype: dict
        """

        return self._history[client]

    def findFile(self, filePath, client=None):
        """
        Finds the given file using the supplied client.
        If no client is provided then the current client is used instead.

        :type filePath: str
        :type client: clientutils.ClientSpec
        :rtype: list
        """

        # Check if a client was supplied
        #
        if client is None:

            client = clientutils.getCurrentClient()

        # Concatenate path and search client for file
        #
        filePath = os.path.normpath(filePath)
        segments = filePath.split(os.path.sep)
        search = '/'.join([client.view[0].clientPath, '...', segments[-1]])

        return self.searchClient(search, client=client)

    def searchClient(self, search, client=None):
        """
        Finds the given file using the supplied client.
        This method expects the following search pattern: '{view}/.../{filename}'
        If no client is provided then the current client is used instead.

        :type search: str
        :type client: clientutils.ClientSpec
        :rtype: list
        """

        # Check if a client was supplied
        #
        if client is None:

            client = clientutils.getCurrentClient()

        # Check if client has history
        #
        history = self.history(client.name)

        if search in history.keys():

            return history[search]

        # Collect files from client view
        #
        log.info('Searching for: %s' % search)
        fileSpecs = cmds.files(search, client=client.name, ignoreDeleted=True)

        if fileSpecs is not None:

            log.info('Found: %s' % fileSpecs)
            history[search] = fileSpecs

            return fileSpecs

        else:

            log.warning('No results found!')
            return []

    def searchClients(self, search):
        """
        Searches all the available clients for the given file.

        :type search: str
        :rtype: dict
        """

        # Iterate through clients
        #
        results = {}

        for (name, client) in clientutils.iterClients():

            # Check if client is associated with host
            #
            if client.host != os.environ['P4HOST']:

                continue

            # Find files
            #
            fileSpecs = self.searchClient(search, client=client)

            if fileSpecs is not None:

                results[client] = fileSpecs

        return results

    def clearHistory(self):
        """
        Clears all the accumulated search history.
        This is useful in case the user has been doing alot of renaming through p4v.

        :rtype: None
        """

        log.info('Clearing search history...')
        self._history.clear()


def findFile(filePath, client=None):
    """
    Locates the supplied file using the search engine.

    :type filePath: str
    :type client: clientutils.ClientSpec
    :rtype: List[dict]
    """

    return __searchengine__.findFile(filePath, client=client)


def clearHistory():
    """
    Clears all the accumulated search history.
    This is useful in case the user has been doing alot of renaming through p4v.

    :rtype: None
    """

    __searchengine__.clearHistory()


__searchengine__ = SearchEngine()
