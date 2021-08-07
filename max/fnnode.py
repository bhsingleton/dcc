import pymxs

from six import string_types, integer_types

from ..abstract import afnnode
from ..decorators.validator import validator

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnNode(afnnode.AFnNode):
    """
    Overload of AFnNode that outlines function set behaviour for interfacing with 3ds Max nodes.
    """

    __slots__ = ()

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.
        """

        # Call parent method
        #
        super(FnNode, self).__init__(*args, **kwargs)

    def object(self):
        """
        Returns the object assigned to this function set.

        :rtype: pymxs.MXSWrapperBase
        """

        # Call parent method
        #
        handle = super(FnNode, self).object()

        # Inspect object type
        #
        if isinstance(handle, integer_types):

            return self.getNodeByHandle(handle)

        else:

            return None

    def setObject(self, obj):
        """
        Assigns an object to this function set for manipulation.

        :type obj: Union[str, int, pymxs.MXSWrapperBase]
        :rtype: None
        """

        try:

            obj = self.getMXSWrapper(obj)
            handle = pymxs.runtime.getHandleByAnim(obj)

            super(FnNode, self).setObject(handle)

        except TypeError as exception:

            log.error(exception)
            return

    @validator
    def handle(self):
        """
        Returns the handle for this node.

        :rtype: int
        """

        return int(pymxs.runtime.getHandleByAnim(self.object()))

    @validator
    def name(self):
        """
        Returns the name of this node.

        :rtype: str
        """

        return self.object().name

    @validator
    def setName(self, name):
        """
        Updates the name of this node.

        :type name: str
        :rtype: None
        """

        self.object().name = name

    @validator
    def parent(self):
        """
        Returns the parent of this node.

        :rtype: om.MObject
        """

        # Check if object has property
        #
        obj = self.object()

        if pymxs.runtime.isProperty(obj, 'parent'):

            return obj.parent

        else:

            return None

    @validator
    def setParent(self, parent):
        """
        Updates the parent of this node.

        :type parent: om.MObject
        :rtype: None
        """

        # Check if object has property
        #
        obj = self.object()

        if pymxs.runtime.isProperty(obj, 'parent'):

            obj.parent = parent

    @validator
    def iterChildren(self):
        """
        Returns a generator that yields all of the children for this node.

        :rtype: iter
        """

        # Check if object has property
        #
        obj = self.object()

        if not pymxs.runtime.isProperty(obj, 'children'):

            return

        # Iterate through children
        #
        children = obj.children

        for i in range(children.count):

            yield children[i]

    @validator
    def getModifiersByType(self, T):
        """
        Returns a list of modifiers from the specified type.

        :type T: class
        :rtype: list
        """

        return [x for x in self.object().modifiers if pymxs.runtime.classOf(x) == T]

    @classmethod
    def getMXSWrapper(cls, value):
        """
        Returns an MXSWrapper from any given value.

        :type value: Union[str, int, pymxs.MXSWrapperBase]
        :rtype: pymxs.MXSWrapperBase
        """

        # Check object type
        #
        if isinstance(value, pymxs.MXSWrapperBase):

            return value

        elif isinstance(value, integer_types):

            return cls.getNodeByHandle(value)

        elif isinstance(value, string_types):

            return cls.getNodeByName(value)

        else:

            raise TypeError('setObject() expects a str or int (%s given)!' % type(value).__name__)

    @classmethod
    def doesNodeExist(cls, name):
        """
        Evaluates whether a node exists with the given name.

        :type name: str
        :rtype: bool
        """

        return cls.getNodeByName(name) is not None

    @classmethod
    def getNodeByName(cls, name):
        """
        Returns a node with the given name.
        If no node associated with this name then none is returned.

        :type name: str
        :rtype: pymxs.MXSWrapperBase
        """

        return pymxs.runtime.getNodeByName(name, exact=True, ignoreCase=True, all=False)

    @classmethod
    def getNodeByHandle(cls, handle):
        """
        Returns a node with the given handle.
        If no node is associated with this handle then none is returned.

        :type handle: int
        :rtype: pymxs.MXSWrapperBase
        """

        return pymxs.runtime.getAnimByHandle(handle)

    @classmethod
    def getActiveSelection(cls):
        """
        Returns the active selection.

        :rtype: list[pymxs.MXSWrapperBase]
        """

        selection = pymxs.runtime.selection
        return [selection[x] for x in range(selection.count)]

    @classmethod
    def setActiveSelection(cls, selection):
        """
        Updates the active selection.

        :type selection: list
        :rtype: None
        """

        pymxs.runtime.selection = selection

    @classmethod
    def clearActiveSelection(cls):
        """
        Clears the active selection.

        :rtype: None
        """

        pymxs.runtime.clearSelection()
