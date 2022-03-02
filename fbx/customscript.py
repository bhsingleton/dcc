import os

from dcc.fbx import fbxbase

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class CustomScript(fbxbase.FbxBase):
    """
    Overload of FbxBase used for managing custom script data.
    """

    # region Dunderscores
    __slots__ = ('_filePath', '_args', '_kwargs')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Declare private variables
        #
        self._filePath = kwargs.get('filePath', '')
        self._args = []
        self._kwargs = {}

        # Call parent method
        #
        super(CustomScript, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def filePath(self):
        """
        Getter method that returns the file path for this export set.

        :rtype: str
        """

        return self._filePath

    @filePath.setter
    def filePath(self, filePath):
        """
        Setter method that updates the file path for this export set.

        :type filePath: str
        :rtype: None
        """

        self._filePath = filePath

    @property
    def args(self):
        """
        Getter method that returns the arguments for this custom script.

        :rtype: List[Any]
        """

        return self._args

    @args.setter
    def args(self, args):
        """
        Setter method that updates the arguments for this custom script.

        :type args: List[Any]
        :rtype: None
        """

        self._args = args

    @property
    def kwargs(self):
        """
        Getter method that returns the keyword arguments for this custom script.

        :rtype: Dict[str, Any]
        """

        return self._kwargs

    @kwargs.setter
    def kwargs(self, kwargs):
        """
        Setter method that updates the keyword arguments for this custom script.

        :type kwargs: Dict[str, Any]
        :rtype: None
        """

        self._kwargs = kwargs
    # endregion

    # region Methods
    def exists(self):
        """
        Evaluates whether this custom script exists.

        :rtype: bool
        """

        return os.path.exists(self.filePath)

    def preExport(self):
        """
        Executes the pre-export function from the python file.

        :rtype: None
        """

        pass

    def postExport(self):
        """
        Executes the post-export function from the python file.

        :rtype: None
        """

        pass
    # endregion
