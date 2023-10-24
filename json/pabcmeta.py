from abc import ABCMeta

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PABCMeta(ABCMeta):
    """
    Python abstract base class that supports post-initialization.
    """

    # region Dunderscores
    def __call__(cls, *args, **kwargs):
        """
        Private method that's called whenever this class is called.

        :rtype: QABCMeta
        """

        instance = super(PABCMeta, cls).__call__(*args, **kwargs)
        instance.__post_init__(*args, **kwargs)

        return instance
    # endregion
