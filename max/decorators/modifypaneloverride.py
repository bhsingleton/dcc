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
        '_currentNode',
        '_currentModifier',
        '_objectLevel',
        '_subObjectLevel',
        '_create',
        '_before',
        '_deleteLater'
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :type revert: bool
        :type objectLevel: int
        :type subObjectLevel: int
        :type create: Union[pymxs.runtime.MAXClass, None]
        :type before: Union[int, None]
        :type deleteLater: bool
        :rtype: None
        """

        # Override command panel mode
        #
        kwargs['mode'] = 'modify'

        # Call parent method
        #
        super(ModifyPanelOverride, self).__init__(*args, **kwargs)

        # Declare public variables
        #
        self._currentNode = None
        self._currentModifier = None
        self._objectLevel = kwargs.get('objectLevel', None)
        self._subObjectLevel = kwargs.get('subObjectLevel', None)
        self._create = kwargs.get('create', None)
        self._before = kwargs.get('before', None)
        self._deleteLater = kwargs.get('deleteLater', False)

    def __enter__(self, *args, **kwargs):
        """
        Private method that is called when this instance is entered using a with statement.

        :rtype: None
        """

        # Call parent method
        #
        super(ModifyPanelOverride, self).__enter__(*args, **kwargs)

        # Check if modifier should be selected
        #
        if isinstance(self.objectLevel, integer_types):

            # Evaluate number of arguments
            #
            numArgs = len(args)

            if not (0 <= self.objectLevel < numArgs):

                raise TypeError('__enter__() selection index is out of range!')

            # Evaluate argument type
            #
            arg = args[self.objectLevel]

            isValidNode = nodeutils.isValidNode(arg)
            isValidModifier = modifierutils.isValidModifier(arg)

            if isValidNode:

                self._currentNode = arg
                self._currentModifier = nodeutils.baseObject(self._currentNode)

            elif isValidModifier:

                self._currentModifier = arg
                self._currentNode = wrapperutils.getAssociatedNode(self._currentModifier)

            else:

                raise TypeError('__enter__() expects a valid node or modifier!')

            # Update current modifier
            #
            self.setCurrentObject(self._currentNode, self._currentModifier)

        # Check if the sub-object level should be changed
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

        # Check if a modifier should be created
        #
        if modifierutils.acceptsModifier(self._currentNode, self.create):

            # Check if modifier already exists
            #
            modifiers = modifierutils.getModifierByClass(self._currentNode, self.create)
            hasModifier = len(modifiers) > 0

            if hasModifier:

                modifier = modifiers[0]

            else:

                modifier = self.create()
                kwargs = {'before': self.before} if isinstance(self.before, integer_types) else {}

                pymxs.runtime.addModifier(self._currentNode, modifier, **kwargs)

            # Update current object
            #
            self.setCurrentObject(self._currentNode, modifier)

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
        if wrapperutils.isClass(self.create) and self.deleteLater:

            pymxs.runtime.deleteModifier(self._currentNode, self._currentModifier)

        # Cleanup pymxs references
        #
        self._currentNode = None
        self._currentModifier = None
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
