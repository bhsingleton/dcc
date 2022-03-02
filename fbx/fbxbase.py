from dcc.json import psonobject

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxBase(psonobject.PSONObject):
    """
    Overload of PSONObject used as a base class for all fbx data objects.
    """

    # region Dunderscores
    __slots__ = ('_name',)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
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

        oldName = self._name

        if oldName != newName:

            self._name = newName
            self.nameChanged(oldName, newName)
    # endregion

    # region Callbacks
    def nameChanged(self, oldName, newName):
        """
        Callback to whenever the name of this object changes.

        :type oldName: str
        :type newName: str
        :rtype: None
        """

        pass
    # endregion
