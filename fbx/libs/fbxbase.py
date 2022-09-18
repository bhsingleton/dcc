from abc import ABCMeta
from six import with_metaclass
from ... import fnnode, fnlayer, fnselectionset
from ...json import psonobject
from ...python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxBase(with_metaclass(ABCMeta, psonobject.PSONObject)):
    """
    Overload of PSONObject that acts as a base class for all fbx data objects.
    The dunderscore function set constructors are exposed for DCCs that require custom bindings.
    Especially, for instance, 3ds Max where XRef hasn't worked for over 20 years.
    """

    # region Dunderscores
    __slots__ = ('_name', '__weakref__')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Declare private variables
        #
        self._name = kwargs.get('name', '')

        # Call parent method
        #
        super(FbxBase, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def name(self):
        """
        Getter method that returns the name of this object.

        :rtype: str
        """

        return self._name

    @name.setter
    def name(self, newName):
        """
        Setter method that updates the name of this object

        :type newName: str
        :rtype: None
        """

        self._name = newName
    # endregion

    # region Methods
    @staticmethod
    def absolutify(name, namespace):
        """
        Returns an absolute name using the supplied namespace.

        :type name: str
        :type namespace: str
        :rtype: str
        """

        if stringutils.isNullOrEmpty(namespace):

            return name

        else:

            return '{namespace}:{name}'.format(namespace=namespace, name=name)

    @classmethod
    def iterNodesFromNames(cls, *names, namespace=''):
        """
        Returns a generator that yields nodes from the supplied names and namespace.

        :type namespace: str
        :rtype: Iterator[Any]
        """

        node = fnnode.FnNode()

        for name in names:

            success = node.trySetObject(cls.absolutify(name, namespace))

            if success:

                yield node.object()

            else:

                continue

    @classmethod
    def iterDescendantsFromName(cls, name, namespace=''):
        """
        Returns a generator that yields descendants from the specified names and namespace.

        :type name: str
        :type namespace: str
        :rtype: Iterator[Any]
        """

        # Check if name is valid
        #
        if stringutils.isNullOrEmpty(name):

            return iter([])

        # Try and initialize function set
        #
        node = fnnode.FnNode()
        success = node.trySetObject(cls.absolutify(name, namespace))

        if success:

            yield from node.iterDescendants()

        else:

            return iter([])

    @classmethod
    def iterNodesFromLayers(cls, *names, namespace=''):
        """
        Returns a generator that yields nodes from the supplied names and namespace.

        :type namespace: str
        :rtype: Iterator[Any]
        """

        layer = fnlayer.FnLayer()

        for name in names:

            success = layer.trySetObject(cls.absolutify(name, namespace))

            if success:

                yield from layer.iterNodes()

            else:

                continue

    @classmethod
    def iterNodesFromSelectionSets(cls, *names, namespace=''):
        """
        Returns a generator that yields nodes from the supplied names and namespace.

        :type namespace: str
        :rtype: Iterator[Any]
        """

        selectionSet = fnselectionset.FnSelectionSet()

        for name in names:

            success = selectionSet.trySetObject(cls.absolutify(name, namespace))

            if success:

                yield from selectionSet.iterNodes()

            else:

                continue

    @classmethod
    def iterNodesFromRegex(cls, regex, namespace=''):
        """
        Returns a generator that yields nodes from the supplied regex.

        :type regex: str
        :type namespace: str
        :rtype: Iterator[Any]
        """

        # Check if regex is valid
        #
        if stringutils.isNullOrEmpty(regex):

            return iter([])

        # Check if namespace was supplied
        #
        if not stringutils.isNullOrEmpty(namespace):

            regex = r'(?:{namespace}\:)?{regex}'.format(namespace=namespace, regex=regex)

        return fnnode.FnNode.iterInstancesByRegex(regex)
    # endregion
