import json

from maya import cmds as mc
from maya.api import OpenMaya as om
from six.moves import collections_abc
from dcc.python import stringutils
from dcc.maya.libs import dagutils
from dcc.maya.json import mdataparser

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class UserProperties(collections_abc.MutableMapping):
    """
    Overload of `MutableMapping` that interfaces with user properties.
    """

    # region Dunderscores
    __slots__ = ('__handle__', '__buffer__', '__properties__')

    def __init__(self, obj, **kwargs):
        """
        Private method called after a new instance has been created.

        :type obj: Union[str, om.MObject, om.MDagPath]
        :rtype: None
        """

        # Call parent method
        #
        super(UserProperties, self).__init__()

        # Declare private variables
        #
        self.__handle__ = dagutils.getMObjectHandle(obj)
        self.__buffer__ = ''
        self.__properties__ = {}

    def __getitem__(self, key):
        """
        Private method that returns an indexed item.

        :type key: Union[int, str]
        :rtype: Any
        """

        self.pullBuffer()
        return self.__properties__[key]

    def __setitem__(self, key, value):
        """
        Private method that updates an indexed item.

        :type key: Union[int, str]
        :type value: Any
        :rtype: None
        """

        self.pullBuffer()
        self.__properties__[key] = value
        self.pushBuffer()

    def __delitem__(self, key):
        """
        Private method that removes an indexed item.

        :type key: Union[int, str]
        :rtype: None
        """

        self.pullBuffer()
        del self.__properties__[key]
        self.pushBuffer()

    def __len__(self):
        """
        Private method that returns the number of properties.

        :rtype: int
        """

        self.pullBuffer()
        return len(self.__properties__)

    def __iter__(self):
        """
        Private method that returns a generator that yields property keys.

        :rtype: iter
        """

        self.pullBuffer()
        return iter(self.__properties__)
    # endregion

    # region Methods
    def object(self):
        """
        Returns the associated dependency node.

        :rtype: om.MObject
        """

        return self.__handle__.object()

    def name(self):
        """
        Returns the name of the associated dependency node.

        :rtype: str
        """

        return om.MFnDependencyNode(self.object()).name()

    def fullPathName(self):
        """
        Returns the full name of the associated dependency node.

        :rtype: str
        """

        obj = self.object()

        if obj.hasFn(om.MFn.kDagNode):

            return om.MDagPath.getAPathTo(obj).fullPathName()

        else:

            return self.name()

    def keys(self):
        """
        Returns a generator that yields property keys.

        :rtype: iter
        """

        self.pullBuffer()
        return self.__properties__.keys()

    def values(self):
        """
        Returns a generator that yields property values.

        :rtype: iter
        """

        self.pullBuffer()
        return self.__properties__.values()

    def items(self):
        """
        Returns a generator that yields property key-value pairs.

        :rtype: iter
        """

        self.pullBuffer()
        return self.__properties__.items()

    def update(self, obj):
        """
        Copies the supplied items to the internal properties.

        :type obj: dict
        :rtype: None
        """

        self.pullBuffer()
        self.__properties__.update(obj)
        self.pushBuffer()

    def clear(self):
        """
        Removes all items from the internal properties.

        :rtype: None
        """

        self.__properties__.clear()
        self.pushBuffer()

    def buffer(self):
        """
        Returns the user property buffer from the notes plug.
        If the plug does not exist then a runtime error is raised!

        :rtype: str
        """

        # Check if attribute exists
        #
        fullPathName = self.fullPathName()
        hasAttribute = mc.attributeQuery('notes', node=fullPathName, exists=True)

        if not hasAttribute:

            raise AttributeError(f'buffer() cannot find notes attribute!')

        # Check if node is referenced
        # If so, then be sure to remove any reference edits from the notes plug!
        #
        isReferenced = mc.referenceQuery(fullPathName, isNodeReferenced=True)

        if isReferenced:

            mc.referenceEdit(
                f'{fullPathName}.notes',
                failedEdits=True,
                successfulEdits=True,
                editCommand='setAttr',
                removeEdits=True
            )

        # Get notes from node
        #
        return mc.getAttr(f'{fullPathName}.notes')

    def tryGetBuffer(self):
        """
        Returns the user property buffer from the notes plug.
        If the plug does not exist then an empty string is returned instead.

        :rtype: str
        """

        try:

            return self.buffer()

        except AttributeError:

            return ''

    def ensureNotes(self):
        """
        Ensures that the supplied node has a notes attribute.

        :rtype: None
        """

        # Check if notes exist
        #
        fullPathName = self.fullPathName()

        hasAttribute = mc.attributeQuery('notes', node=fullPathName, exists=True)
        isLocked = mc.lockNode(fullPathName, query=True, lock=True)[0]

        if not hasAttribute and not isLocked:

            mc.addAttr(fullPathName, longName='notes', shortName='nts', dataType='string', cachedInternally=True)

    def pullBuffer(self):
        """
        Loads the user properties from the `notes` attribute.

        :rtype: None
        """

        # Redundancy check
        #
        buffer = self.tryGetBuffer()

        if buffer == self.__buffer__ or stringutils.isNullOrEmpty(buffer):

            return

        # Ensure `notes` attribute exists
        #
        self.ensureNotes()

        # Load properties from buffer
        #
        self.__buffer__ = buffer

        try:

            self.__properties__ = json.loads(buffer, cls=mdataparser.MDataDecoder)

        except json.JSONDecodeError as error:

            log.debug(error)
            self.__properties__ = {}

    def pushBuffer(self):
        """
        Dumps the user properties into the `notes` attribute.

        :rtype: None
        """

        # Redundancy check
        #
        if len(self.__properties__) == 0:

            return

        # Ensure notes attribute exists
        #
        self.ensureNotes()

        # Dump properties to buffer
        #
        try:

            self.__buffer__ = json.dumps(self.__properties__, indent=4, cls=mdataparser.MDataEncoder)

        except TypeError as exception:

            log.error(exception)
            return

        finally:

            fullPathName = self.fullPathName()
            mc.setAttr(f'{fullPathName}.notes', self.__buffer__, type='string')
    # endregion
