from . import fbxobjectset

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxCamera(fbxobjectset.FbxObjectSet):
    """
    Overload of `FbxBase` used to store camera properties.
    """

    # region Dunderscores
    __slots__ = ()
    # endregion
