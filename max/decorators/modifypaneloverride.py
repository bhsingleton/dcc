import pymxs

from six import integer_types
from . import commandpaneloverride

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ModifyPanelOverride(commandpaneloverride.CommandPanelOverride):
    """
    Overload of `CommandPanelOverride` that overrides the modify panel at runtime.
    """

    # region Dunderscores
    __slots__ = ('_currentObject', '_subObjectLevel')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key revert: bool
        :key currentObject: int
        :key subObjectLevel: int
        :rtype: None
        """

        # Call parent method
        #
        kwargs['mode'] = 'modify'
        super(ModifyPanelOverride, self).__init__(*args, **kwargs)

        # Declare public variables
        #
        self._currentObject = kwargs.get('currentObject', None)
        self._subObjectLevel = kwargs.get('subObjectLevel', None)

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
        if isinstance(self.currentObject, integer_types):

            # Evaluate number of arguments
            #
            numArgs = len(args)

            if not (0 <= self.currentObject < numArgs):

                raise TypeError('__enter__() selection index is out of range!')

            # Evaluate argument type
            #
            modifier = args[self.currentObject]

            if not pymxs.runtime.isKindOf(modifier, pymxs.runtime.Modifier):

                raise TypeError('__enter__() expects a valid modifier!')

            # Update current modifier
            # Check for redundancy since calling `setCurrentObject` will evoke a selection changed callback!
            #
            currentModifier = pymxs.runtime.modPanel.getCurrentObject()

            if modifier != currentModifier:

                node = pymxs.runtime.refs.dependentNodes(modifier, firstOnly=True)

                log.debug(f'Overriding current object: ${node.name}.modifiers[#{pymxs.runtime.classOf(modifier)}]')
                pymxs.runtime.modPanel.setCurrentObject(modifier, node=node)

        # Check if the sub-object level should be changed
        #
        subObjectEnabled = pymxs.runtime.isSubSelEnabled()

        if isinstance(self.subObjectLevel, integer_types) and subObjectEnabled:

            # Evaluate available sub-object levels
            #
            if not (1 <= self.subObjectLevel <= pymxs.runtime.numSubObjectLevels):

                raise TypeError('__enter__() sub-object level is out of range!')

            # Update sub-object level
            #
            log.debug(f'Overriding sub-object level: {self.subObjectLevel}')
            pymxs.runtime.subObjectLevel = self.subObjectLevel
    # endregion

    # region Properties
    @property
    def currentObject(self):
        """
        Getter method that returns the argument index to make current.

        :rtype: int
        """

        return self._currentObject

    @property
    def subObjectLevel(self):
        """
        Getter method that returns the sub-object level override.

        :rtype: int
        """

        return self._subObjectLevel
    # endregion
