import json
import sys

from . import psonremap
from ..python import importutils, stringutils
from ..decorators.staticinitializer import staticInitializer
from ..vendor.six.moves import collections_abc

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
    __builtin_types__ = (bool, int, float, str, collections_abc.Sequence, collections_abc.Mapping)
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
        isPickleable = hasattr(cls, '__getstate__')

        if issubclass(cls, collections_abc.Sequence):

            return list(iter(obj))

        elif issubclass(cls, collections_abc.Mapping):

            return obj.__getstate__() if isPickleable else dict(obj.items())

        else:

            return super(PSONEncoder, self).default(obj)
    # endregion


@staticInitializer
class PSONDecoder(json.JSONDecoder):
    """
    Overload of JSONDecoder used to translate JSON objects back into python objects.
    """

    # region Dunderscores
    __slots__ = ()
    __remaps__ = {}

    @classmethod
    def __static_init__(cls, *args, **kwargs):
        """
        Private method called after this class has been initialized.

        :rtype: None
        """

        cls.__remaps__.update({remap.name: remap for remap in psonremap.iterRemaps()})

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

    def remap(self, obj):
        """
        Remaps the class and module on the supplied JSON object.

        :type obj: Dict[str, Any]
        :rtype Dict[str, Any]
        """

        # Evaluate dictionary for any numerical keys
        # Next, check if remap object exists
        #
        obj = {stringutils.eval(key): value for (key, value) in obj.items()}
        className = obj.get('__class__', obj.get('__name__', ''))  # This is here for legacy purposes!
        moduleName = obj.get('__module__', '')

        remap = self.__remaps__.get(className, None)  # type: psonremap.PSONRemap

        if remap is None:

            return obj

        # Check if class requires updating
        #
        if not stringutils.isNullOrEmpty(remap.nameChange):

            log.debug(f'Remapping class: "{className}" > "{remap.nameChange}"')
            obj['__class__'] = remap.nameChange

        # Check if module requires updating
        #
        if not stringutils.isNullOrEmpty(remap.pathChange):

            log.debug(f'Remapping module: "{moduleName}" > "{remap.pathChange}"')
            obj['__module__'] = remap.pathChange

        # Check if properties require updating
        #
        if not stringutils.isNullOrEmpty(remap.properties):

            log.debug(f'Remapping properties: {remap.properties}')
            obj = {remap.properties.get(key, key): value for (key, value) in obj.items()}

        return obj

    def default(self, obj):
        """
        Object hook used to find an appropriate class for the supplied object.
        Rest assured json parses leaf objects first before top level objects!

        :type obj: dict
        :rtype: Any
        """

        # Remap any internal dataclass changes
        #
        obj = self.remap(obj)

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
