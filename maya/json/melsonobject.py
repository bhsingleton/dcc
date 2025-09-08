from ...json import psonobject
from . import mdataparser

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MELSONObject(psonobject.PSONObject):
    """
    Overload of `PSONObject` that extends support for Maya dataclasses.
    """

    # region Dunderscores
    __slots__ = ()
    # endregion

    # region Methods
    @classmethod
    def isJsonCompatible(cls, T):
        """
        Evaluates whether the given type is json compatible.

        :type T: Union[Callable, Tuple[Callable]]
        :rtype: bool
        """

        module = getattr(T, '__module__', '')

        if module == 'OpenMaya':

            return mdataparser.MDataEncoder.acceptsType(T)

        else:

            return super(MELSONObject, cls).isJsonCompatible(T)
    # endregion
