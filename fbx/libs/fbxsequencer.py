from . import fbxbase, fbxio, fbxasset, fbxsequence
from ...collections import notifylist

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxSequencer(fbxbase.FbxBase):
    """
    Overload of FbxBase that interfaces with fbx sequence data.
    Sequencers rely on a reference GUIDs in order to associate the sequencer with an asset.
    """

    # region Dunderscores
    __slots__ = ('_manager', '_reference', '_guid', '_asset', '_sequences')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Declare private variables
        #
        self._manager = fbxio.FbxIO()
        self._reference = kwargs.get('reference', self.__reference__())
        self._guid = kwargs.get('guid', '')
        self._asset = kwargs.get('asset', self.nullWeakReference)
        self._sequences = notifylist.NotifyList()

        # Setup notifies
        #
        self._sequences.addCallback('itemAdded', self.sequenceAdded)
        self._sequences.addCallback('itemRemoved', self.sequenceRemoved)
        self._sequences.extend(kwargs.get('sequences', []))

        # Call parent method
        #
        super(FbxSequencer, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def reference(self):
        """
        Getter method that returns the associated reference for this asset.

        :rtype: fnreference.FnReference
        """

        if not self._reference.isValid() and not self.scene.isNullOrEmpty(self.guid):

            self.invalidateReference()  # This ensures the reference interface is always up-to-date!

        return self._reference

    @property
    def manager(self):
        """
        Getter method that returns the fbx sequencer manager.

        :rtype: fbxio.FbxIO
        """

        return self._manager

    @property
    def guid(self):
        """
        Getter method that returns the GUID for this proxy.

        :rtype: str
        """

        return self._guid

    @guid.setter
    def guid(self, guid):
        """
        Setter method that updates the GUID for this proxy.

        :rtype: str
        """

        self._guid = guid
        self.invalidate()

    @property
    def asset(self):
        """
        Getter method that returns the associated asset.

        :rtype: fbxasset.FbxAsset
        """

        return self._asset()

    @property
    def sequences(self):
        """
        Getter method that returns the fbx sequences for this asset.

        :rtype: List[fbxsequence.FbxSequence]
        """

        return self._sequences

    @sequences.setter
    def sequences(self, sequences):
        """
        Setter method that returns the fbx sequences for this asset.

        :type sequences: List[fbxsequence.FbxSequence]
        :rtype: None
        """

        self._sequences.clear()
        self._sequences.extend(sequences)
    # endregion

    # region Methods
    def isValid(self):
        """
        Evaluates if this sequencer is valid.
        Without a valid asset the sequencer cannot export any data.

        :rtype: bool
        """

        return self.asset is not None

    def namespace(self):
        """
        Returns the namespace associated with this sequencer.

        :rtype: str
        """

        if self.isValid():

            return self.reference.namespace()

        else:

            return ''

    def invalidate(self):
        """
        Invalidates all the dynamic components that make up this sequencer.

        :rtype: None
        """

        self.invalidateReference()
        self.invalidateAsset()
        self.invalidateSequences()

    def invalidateReference(self):
        """
        Invalidates the reference interface against the current GUID.

        :rtype: bool
        """

        # Locate associated reference
        #
        reference = self._reference.getReferenceByGuid(self.guid)

        if reference is None:

            log.warning('Cannot locate reference from: %s' % self.guid)
            return False

        # Update function set object
        #
        return self._reference.trySetObject(reference)

    def invalidateAsset(self):
        """
        Invalidates the associated asset against the current reference interface.

        :rtype: bool
        """

        # Check if reference is valid
        #
        if not self.reference.isValid():

            self._asset = self.nullWeakReference
            return False

        # Update associated asset
        #
        asset = self.manager.loadReferencedAsset(self.reference)

        if asset is not None:

            self._asset = asset.weakReference()
            return True

        else:

            self._asset = self.nullWeakReference
            return False

    def invalidateSequences(self):
        """
        Invalidates the sequences against the current asset.
        This will ensure the 'exportSetId' property's return type is up-to-date!

        :rtype: bool
        """

        # Refresh sequences
        #
        for sequence in self.sequences:

            sequence.refresh()

        return True
    # endregion

    # region Callbacks
    def sequenceAdded(self, index, sequence):
        """
        Adds a reference of this asset to the supplied export set.

        :type index: int
        :type sequence: fbxsequence.FbxSequence
        :rtype: None
        """

        sequence._sequencer = self.weakReference()
        sequence.refresh()

    def sequenceRemoved(self, sequence):
        """
        Removes the reference of this asset from the supplied export set.

        :type sequence: fbxsequence.FbxSequence
        :rtype: None
        """

        sequence._asset = self.nullWeakReference
    # endregion
