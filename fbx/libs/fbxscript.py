import os

from enum import IntEnum
from . import fbxbase

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Language(IntEnum):
    """
    Overload of IntEnum that lists all executable languages.
    """

    Python = 0
    Embedded = 1


class FbxScript(fbxbase.FbxBase):
    """
    Overload of FbxBase used for managing custom script data.
    """

    # region Dunderscores
    __slots__ = ('_filePath', '_language', '_script')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Declare private variables
        #
        self._filePath = kwargs.get('filePath', '')
        self._language = kwargs.get('language', Language.Python)
        self._script = kwargs.get('script', '')

        # Call parent method
        #
        super(FbxScript, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def filePath(self):
        """
        Getter method that returns the file path to execute.

        :rtype: str
        """

        return self._filePath

    @filePath.setter
    def filePath(self, filePath):
        """
        Setter method that updates the file path to execute.

        :type filePath: str
        :rtype: None
        """

        self._filePath = filePath

    @property
    def script(self):
        """
        Getter method that returns the script to execute.

        :rtype: str
        """

        return self._script

    @script.setter
    def script(self, script):
        """
        Setter method that updates the script to execute.

        :type script: str
        :rtype: None
        """

        self._script = script

    @property
    def language(self):
        """
        Getter method that returns the script language to use.

        :rtype: Language
        """

        return self._language

    @language.setter
    def language(self, language):
        """
        Setter method that updates the script language to use.

        :type language: Language
        :rtype: None
        """

        self._language = Language(language)
    # endregion

    # region Methods
    def exists(self):
        """
        Evaluates whether this custom script exists.

        :rtype: bool
        """

        return os.path.exists(self.filePath)

    def execute(self):
        """
        Executes the pre-export function from the python file.

        :rtype: None
        """

        # Check if file path exists
        #
        if not stringutils.isNullOrEmpty(self.filePath):

            log.info('Executing file: %s' % self.filePath)
            self.scene.executeFile(self.filePath)

        # Check if script is valid
        #
        if not stringutils.isNullOrEmpty(self.script):

            log.info('Executing custom script.')

            asPython = self.language == Language.Python
            self.scene.execute(self.script, asPython=asPython)

    def postExport(self):
        """
        Executes the post-export function from the python file.

        :rtype: None
        """

        # Check if file path exists
        #
        if not stringutils.isNullOrEmpty(self.filePath):

            log.info('Executing file: %s' % self.filePath)
            self.scene.executeFile(self.filePath)

        # Check if script is valid
        #
        if not stringutils.isNullOrEmpty(self.script):

            log.info('Executing custom script.')

            asPython = self.language == Language.Python
            self.scene.execute(self.script, asPython=asPython)
    # endregion
