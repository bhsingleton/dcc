import os

from collections import defaultdict
from . import clientutils, cmds
from ..python import stringutils, importutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


P4 = importutils.tryImport('P4', __locals__=locals(), __globals__=globals())


class SearchEngine(object):
    """
    Search class used for locating files on perforce.
    This classes also records search history for faster lookups.
    History is broken down by client first then search value.
    """

    __slots__ = ('__history__',)

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
        self.__history__ = defaultdict(dict)

    def history(self, client):
        """
        Returns the search history for the given client.

        :type client: str
        :rtype: dict
        """

        return self.__history__[client]

    def filterBranches(self, client, filePath):
        """
        Returns a list of filtered branches that could be used to find the specified file.

        :type client: clientutils.ClientSpec
        :type filePath: str
        :rtype: List[clientutils.Branch]
        """

        # Check if client has a stream
        #
        if client.hasStream():

            return client.view

        # Iterate through client view
        #
        segments = os.path.normpath(filePath).split(os.path.sep)

        found = [branch for branch in client.view if branch.depotPath.lstrip('/') in segments]
        numFound = len(found)

        if numFound > 0:

            return found

        else:

            return client.view

    def findFile(self, filePath, client=None):
        """
        Finds the given file using the supplied client.
        If no client is provided then the current client is used instead.

        :type filePath: str
        :type client: clientutils.ClientSpec
        :rtype: list[dict]
        """

        # Check if a client was supplied
        #
        if client is None:

            client = clientutils.getCurrentClient()

        # Iterate through client branches
        #
        filePath = os.path.normpath(filePath)
        segments = filePath.split(os.path.sep)

        branches = self.filterBranches(client, filePath)

        for branch in branches:

            # Concatenate client path and search client for file
            # Make sure to leave out the parent directory in case the file has been moved!
            #
            filename = segments[-1]
            search = '/'.join([branch.clientPath, '...', filename])

            results = self.searchClient(search, client=client)

            if stringutils.isNullOrEmpty(results):

                continue

            # Evaluate search results
            #
            resultCount = len(results)

            if resultCount == 1:

                return results

            # Filter results based on parent directory
            #
            directory = segments[-2]

            filteredResults = [result for result in results if result['depotFile'].endswith(f'{directory}/{filename}')]
            filteredCount = len(filteredResults)

            if filteredCount == 1:

                return filteredResults

            # Filter results based on drive letter changes
            #
            localPath = '/'.join(segments)

            filteredResults = [result for result in results if localPath.endswith(result['depotFile'][2:])]
            filteredCount = len(filteredResults)

            if filteredCount == 1:

                return filteredResults

            else:

                return results

        return []

    def searchClient(self, search, client=None):
        """
        Finds the given file using the supplied client.
        This method expects the following search pattern: '{view}/.../{filename}'
        If no client is provided then the current client is used instead.

        :type search: str
        :type client: clientutils.ClientSpec
        :rtype: list[dict]
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
        fileSpecs = None

        try:

            log.info(f'Searching for: {search}')
            fileSpecs = cmds.files(search, client=client.name, ignoreDeleted=True)

        except P4.P4Exception as exception:

            log.error(exception)

        finally:

            log.info(f'Found: {fileSpecs}')
            return fileSpecs if not stringutils.isNullOrEmpty(fileSpecs) else []

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
        self.__history__.clear()


def findFile(filePath, client=None):
    """
    Locates the supplied file using the search engine.

    :type filePath: str
    :type client: clientutils.ClientSpec
    :rtype: List[dict]
    """

    return __search_engine__.findFile(filePath, client=client)


def clearHistory():
    """
    Clears all the accumulated search history.
    This is useful in case the user has been doing alot of renaming through p4v.

    :rtype: None
    """

    __search_engine__.clearHistory()


__search_engine__ = SearchEngine()
