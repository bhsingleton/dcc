import json
import sys

from six.moves.collections_abc import MutableSequence, MutableMapping
from dcc.python import pythonutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class PSONEncoder(json.JSONEncoder):
    """
    Overload of JSONEncoder used to translate python types into JSON objects.
    """

    __slots__ = ()

    def default(self, obj):
        """
        Object hook used to resolve any non-builtin python types.

        :type obj: Any
        :rtype: Any
        """

        # Check if object is mapped
        #
        objType = type(obj)

        if hasattr(objType, '__getstate__'):

            return obj.__getstate__()

        elif issubclass(objType, MutableSequence):

            return [x for x in obj]

        elif issubclass(objType, MutableMapping):

            return {key: value for (key, value) in obj.items()}

        else:

            return super(PSONEncoder, self).default(obj)


class PSONDecoder(json.JSONDecoder):
    """
    Overload of JSONDecoder used to translate JSON objects back into python objects.
    """

    __slots__ = ()
    __kwdefaults__ = {}

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        kwargs['object_hook'] = self.default
        super(PSONDecoder, self).__init__(*args, **kwargs)

    def default(self, obj):
        """
        Object hook used to find an appropriate class for the supplied object.
        Rest assured json parses leaf objects first before top level objects!

        :type obj: dict
        :rtype: Any
        """

        try:

            className = obj.pop('__name__')
            moduleName = obj.pop('__module__')

            cls = self.findClass(className, moduleName)

            if cls is not None:

                instance = cls(**self.__kwdefaults__)
                instance.__setstate__(obj)

                return instance

            else:

                return obj

        except KeyError as exception:

            log.error(exception)
            return obj

    @classmethod
    def findClass(cls, className, moduleName):
        """
        Returns the class associated with the given name.

        :type className: str
        :type moduleName: str
        :rtype: class
        """

        module = sys.modules.get(moduleName, None)

        if module is not None:

            return module.__dict__.get(className, None)

        else:

            return pythonutils.findClass(className, moduleName)
