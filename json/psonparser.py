import json
import sys

from six.moves import collections_abc
from ..python import importutils, stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PSONEncoder(json.JSONEncoder):
    """
    Overload of JSONEncoder used to translate python types into JSON objects.
    """

    # region Dunderscores
    __slots__ = ()
    __builtin_types__ = (bool, int, float, str, collections_abc.MutableSequence, collections_abc.MutableMapping)
    # endregion

    # region Methods
    def acceptsType(self, T):
        """
        Evaluates whether this serializer accepts the supplied type.

        :type T: Callable
        :rtype: bool
        """

        return hasattr(T, '__getstate__') or issubclass(T, self.__builtin_types__)

    def default(self, obj):
        """
        Object hook used to resolve any non-builtin python types.

        :type obj: Any
        :rtype: Any
        """

        # Check if object is mapped
        #
        cls = type(obj)

        if hasattr(cls, '__getstate__'):

            return obj.__getstate__()

        elif issubclass(cls, collections_abc.MutableSequence):

            return list(iter(obj))

        elif issubclass(cls, collections_abc.MutableMapping):

            return dict(obj.items())

        else:

            return super(PSONEncoder, self).default(obj)
    # endregion


class PSONDecoder(json.JSONDecoder):
    """
    Overload of JSONDecoder used to translate JSON objects back into python objects.
    """

    # region Dunderscores
    __slots__ = ()

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        object_hook = kwargs.pop('object_hook', self.default)
        object_pairs_hook = kwargs.pop('object_pairs_hook', None)
        parse_float = kwargs.pop('parse_float', None)
        parse_int = kwargs.pop('parse_int', None)
        parse_constant = kwargs.pop('parse_constant', None)
        strict = kwargs.pop('strict', True)

        super(PSONDecoder, self).__init__(
            object_hook=object_hook,
            object_pairs_hook=object_pairs_hook,
            parse_float=parse_float,
            parse_int=parse_int,
            parse_constant=parse_constant,
            strict=strict,
        )

        # Store the remaining keyword arguments
        #
        self.__kwdefaults__ = kwargs
    # endregion

    # region Methods
    def acceptsObject(self, obj):
        """
        Evaluates whether this deserializer accepts the supplied object.

        :type obj: dict
        :rtype: bool
        """

        return True

    def default(self, obj):
        """
        Object hook used to find an appropriate class for the supplied object.
        Rest assured json parses leaf objects first before top level objects!

        :type obj: dict
        :rtype: Any
        """

        # Find associated class
        #
        className = obj.pop('__class__', obj.pop('__name__', ''))  # This is here for legacy purposes!
        moduleName = obj.pop('__module__', '')

        cls = self.findClass(className, moduleName)

        if callable(cls):

            instance = cls(**self.__kwdefaults__)
            instance.__setstate__(obj)

            return instance

        else:

            return obj

    @classmethod
    def findClass(cls, className, moduleName):
        """
        Returns the class associated with the given name.

        :type className: str
        :type moduleName: str
        :rtype: Callable
        """

        # Redundancy check
        #
        if any(map(stringutils.isNullOrEmpty, (className, moduleName))):

            return None

        # Check if module already exists inside `sys` modules
        # If not, then import associated module
        #
        module = sys.modules.get(moduleName, None)

        if module is not None:

            return module.__dict__.get(className, None)

        else:

            return importutils.findClass(className, moduleName)
    # endregion
