import os

from collections import defaultdict
from . import clientutils, cmds

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

    def searchClient(self, search, client=None):
        """
        Locates the specified file against the supplied client.
        If no client is provided then the current client is used instead.

        :type search: str
        :type client: str
        :rtype: dict
        """

        # Check if a client was supplied
        #
        if client is None:

            client = os.environ['P4CLIENT']

        # Check if client has history
        #
        history = self.history(client)

        if search in history.keys():

            return history[search]

        # Collect files from client view
        #
        fileSpecs = cmds.files(search, client=client, ignoreDeleted=True)

        if fileSpecs is not None:

            history[search] = fileSpecs
            return fileSpecs

        else:

            return []

    def searchClients(self, search):
        """
        Searches all of the available clients for the given file.

        :type search: str
        :rtype: dict
        """

        # Iterate through clients
        #
        results = {}

        for (client, clientSpec) in clientutils.iterClients():

            # Check if client is associated with host
            #
            if clientSpec.host != os.environ['P4HOST']:

                continue

            # Find files
            #
            fileSpecs = self.searchClient(search, client=client)

            if fileSpecs is not None:

                results[client] = fileSpecs

        return results

    def clearHistory(self):
        """
        Clears all of the accumulated search history.
        This is useful in case the user has been doing alot of renaming through p4v.

        :rtype: None
        """

        log.info('Clearing search history...')
        self._history.clear()


def findFile(search):
    """
    Locates the supplied file using the search engine.

    :type search: str
    :rtype: list[dict]
    """

    return __searchengine__.searchClient(search)


def clearHistory():
    """
    Clears all of the accumulated search history.
    This is useful in case the user has been doing alot of renaming through p4v.

    :rtype: None
    """

    __searchengine__.clearHistory()


__searchengine__ = SearchEngine()
