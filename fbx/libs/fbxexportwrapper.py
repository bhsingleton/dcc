from abc import ABCMeta, abstractmethod
from . import fbxexportset, fbxexportrange

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxExportWrapper(object, metaclass=ABCMeta):
    """
    Abstract base class used to wrap pre/post export methods.
    """

    # region Dunderscores

    __slots__ = ('_exporter',)

    def __init__(self, exporter):
        """
        Private method called after a new instance has been created.

        :type exporter: Union[fbxexportset.FbxExportSet, fbxexportrange.FbxExportRange]
        :rtype: None
        """

        # Call parent method
        #
        super(FbxExportWrapper, self).__init__()

        # Declare private variables
        #
        self._exporter = exporter.weakReference()
    # endregion

    # region Properties
    @property
    def exporter(self):
        """
        Getter method that returns the exporter that's being wrapped.

        :rtype: Union[fbxexportset.FbxExportSet, fbxexportrange.FbxExportRange]
        """

        return self._exporter()
    # endregion

    # region Methods
    def isExportSet(self):
        """
        Evaluates if an export-set is being wrapped.

        :rtype: bool
        """

        return isinstance(self.exporter, fbxexportset.FbxExportSet)

    def isExportRange(self):
        """
        Evaluates if an export-range is being wrapped.

        :rtype: bool
        """

        return isinstance(self.exporter, fbxexportrange.FbxExportRange)

    @abstractmethod
    def preExport(self):
        """
        Pre-export wrapper.

        :rtype: None
        """

        pass

    @abstractmethod
    def postExport(self):
        """
        Post-export wrapper.

        :rtype: None
        """

        pass
    # endregion
