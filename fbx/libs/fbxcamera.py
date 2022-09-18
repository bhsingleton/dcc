from . import fbxbase
from ... import fnnode

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxCamera(fbxbase.FbxBase):
    """
    Overload of FbxBase used to store camera properties.
    """

    # region Dunderscores
    __slots__ = ()
    # endregion

    # region Methods
    def select(self, namespace=''):
        """
        Selects the associated camera node from the scene file.

        :type namespace: str
        :rtype: None
        """

        # Check if root node is valid
        #
        node = fnnode.FnNode()
        success = node.trySetObject(self.absolutify(self.name, namespace))

        if not success:

            return

        # Select root and descendants
        #
        node.select(replace=False)
    # endregion
