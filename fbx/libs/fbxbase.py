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

        # Call parent method
        #
        super(FbxBase, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._name = kwargs.get('name', '')
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
    def iterNodesFromNames(cls, *names, includeChildren=False, namespace=''):
        """
        Returns a generator that yields nodes from the supplied names and namespace.

        :type includeChildren: bool
        :type namespace: str
        :rtype: Iterator[Any]
        """

        # Iterate through names
        #
        node = fnnode.FnNode()

        for name in names:

            # Try and initialize function set
            #
            success = node.trySetObject(cls.absolutify(name, namespace))

            if not success:

                continue

            # Check if children should be included
            #
            if includeChildren:

                yield node.object()
                yield from node.iterDescendants()

            else:

                yield node.object()

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
    def iterNodesFromRegex(cls, *expressions, namespace=''):
        """
        Returns a generator that yields nodes from the supplied regex.

        :type expressions: str
        :type namespace: str
        :rtype: Iterator[Any]
        """

        # Iterate through expressions
        #
        for expression in expressions:

            # Check if expression is valid
            #
            if stringutils.isNullOrEmpty(expression):

                continue

            # Check if namespace was supplied
            #
            if not stringutils.isNullOrEmpty(namespace):

                expression = r'(?:{namespace}\:)?{regex}'.format(namespace=namespace, regex=expression)

            yield from fnnode.FnNode.iterInstancesByRegex(expression)
    # endregion
