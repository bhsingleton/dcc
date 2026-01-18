import pymxs

from . import commandpaneloverride
from ..libs import wrapperutils, modifierutils, nodeutils
from ...vendor.six import integer_types

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ModifyPanelOverride(commandpaneloverride.CommandPanelOverride):
    """
    Overload of `CommandPanelOverride` that overrides the modify panel at runtime.
    """

    # region Dunderscores
    __slots__ = (
        '_node',
        '_modifier',
        '_objectLevel',
        '_subObjectLevel',
        '_create',
        '_before',
        '_deleteLater'
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :param objectLevel: Indicates the argument index for the object to make current.
        :type objectLevel: int
        :param subObjectLevel: Indicates the sub-object level to make current.
        :type subObjectLevel: int
        :param create: Indicates if a new modifier should be created and made current.
        :type create: Union[pymxs.runtime.MAXClass, None]
        :param before: The position in the stack where the modifier will be inserted.
        :type before: Union[int, None]
        :param deleteLater: Indicates if the modifier should be deleted upon exit.
        :type deleteLater: bool
        :rtype: None
        """

        # Override command-panel mode
        #
        kwargs['mode'] = 'modify'

        # Call parent method
        #
        super(ModifyPanelOverride, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._node = None
        self._modifier = None
        self._objectLevel = kwargs.get('objectLevel', None)
        self._subObjectLevel = kwargs.get('subObjectLevel', None)
        self._create = kwargs.get('create', None)
        self._before = kwargs.get('before', None)
        self._deleteLater = kwargs.get('deleteLater', False)

        # Evaluate supplied arguments
        #
        numArgs = len(args)

        if numArgs == 1:

            # Evaluate argument
            #
            obj = args[0]
            isValidNode = nodeutils.isValidNode(obj)
            isValidModifier = nodeutils.isValidBaseObject(obj) or modifierutils.isValidModifier(obj)

            if isValidNode:

                self._node = obj
                self._modifier = modifierutils.getLastModifier(self._node)

            elif isValidModifier:

                self._modifier = obj
                self._node = modifierutils.getNodeFromModifier(self._modifier)

            else:

                pass

        elif numArgs == 2:

            # Evaluate arguments
            #
            node, name = args
            isValidNode = nodeutils.isValidNode(node)
            isValidName = pymxs.runtime.isKindOf(name, pymxs.runtime.Name)

            if isValidNode and isValidName:

                self._node = node

        else:

            pass

    def __enter__(self, *args, **kwargs):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        # Call parent method
        #
        super(ModifyPanelOverride, self).__enter__(*args, **kwargs)

        # Check if an object-level was specified
        #
        if isinstance(self.objectLevel, integer_types):

            # Evaluate number of arguments
            #
            numArgs = len(args)

            if not (0 <= self.objectLevel < numArgs):

                raise TypeError('__enter__() object level is out of range!')

            # Evaluate argument type
            #
            obj = args[self.objectLevel]

            isValidNode = nodeutils.isValidNode(obj)
            isValidModifier = nodeutils.isValidBaseObject(obj) or modifierutils.isValidModifier(obj)

            if isValidNode:

                self._node = obj
                self._modifier = nodeutils.baseObject(self._node)

            elif isValidModifier:

                self._modifier = obj
                self._node = wrapperutils.getAssociatedNode(self._modifier)

            else:

                pass

        # Check if a modifier should be created
        #
        if modifierutils.acceptsModifier(self._node, self.create):

            # Check if modifier already exists
            #
            modifiers = modifierutils.getModifierByClass(self._node, self.create, all=True)
            hasModifier = len(modifiers) > 0

            if hasModifier:

                self._modifier = modifiers[0]

            else:

                self._modifier = self.create()
                kwargs = {'before': self.before} if isinstance(self.before, integer_types) else {}

                pymxs.runtime.addModifier(self._node, self._modifier, **kwargs)

        # Update current object
        #
        isValidNode = nodeutils.isValidNode(self._node)
        isValidModifier = nodeutils.isValidBaseObject(self._modifier) or modifierutils.isValidModifier(self._modifier)

        if isValidNode and isValidModifier:

            self.setCurrentObject(self._node, self._modifier)

        else:

            raise TypeError('__enter__() expects a valid node or modifier!')

        # Check if the sub-object level requires changing
        #
        subObjectEnabled = pymxs.runtime.isSubSelEnabled()

        if isinstance(self.subObjectLevel, integer_types) and subObjectEnabled:

            # Evaluate if sub-object level is within range
            #
            if not (1 <= self.subObjectLevel <= pymxs.runtime.numSubObjectLevels):

                raise TypeError('__enter__() sub-object level is out of range!')

            # Update sub-object level
            #
            log.debug(f'Overriding sub-object level: {self.subObjectLevel}')
            pymxs.runtime.subObjectLevel = self.subObjectLevel

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Private method that is called when this instance is exited using a with statement.

        :type exc_type: Any
        :type exc_val: Any
        :type exc_tb: Any
        :rtype: None
        """

        # Call parent method
        #
        super(ModifyPanelOverride, self).__exit__(exc_type, exc_val, exc_tb)

        # Check if any modifiers require deleting
        #
        if (wrapperutils.isClass(self.create) and self.deleteLater) and self.depth == 0:

            pymxs.runtime.deleteModifier(self._node, self._modifier)

        # Cleanup pymxs references
        #
        self._node = None
        self._modifier = None
    # endregion

    # region Properties
    @property
    def objectLevel(self):
        """
        Getter method that returns the argument index to make current.

        :rtype: int
        """

        return self._objectLevel

    @property
    def subObjectLevel(self):
        """
        Getter method that returns the sub-object level override.

        :rtype: int
        """

        return self._subObjectLevel

    @property
    def create(self):
        """
        Getter method that returns the MAX class to dynamically create.

        :rtype: Union[pymxs.runtime.MAXClass, None]
        """

        return self._create

    @property
    def before(self):
        """
        Getter method that returns the insertion index for newly created modifiers.

        :rtype: Union[int, None]
        """

        return self._before

    @property
    def deleteLater(self):
        """
        Getter method that returns the delete-later flag.

        :rtype: bool
        """

        return self._deleteLater
    # endregion

    # region Methods
    def setCurrentObject(self, node, modifier):
        """
        Updates the current object inside the modify panel.
        It's important to know that updating current object triggers a selection changed callback!

        :type node: pymxs.MXSWrapperBase
        :type modifier: pymxs.MXSWrapperBase
        :rtype: None
        """

        currentModifier = pymxs.runtime.modPanel.getCurrentObject()

        if modifier != currentModifier:

            log.debug(f'Overriding current object: ${node.name}.modifiers[#{pymxs.runtime.classOf(modifier)}]')
            pymxs.runtime.modPanel.setCurrentObject(modifier, node=node)

        else:

            log.debug(f'Skipping current object: ${node.name}.modifiers[#{pymxs.runtime.classOf(modifier)}]')
    # endregion
