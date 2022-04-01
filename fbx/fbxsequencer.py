from dcc import fnreference
from dcc.fbx import fbxbase, fbxasset
from dcc.collections import notifylist

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxSequencer(fbxbase.FbxBase):
    """
    Overload of FbxBase that interfaces with fbx sequence data.
    Sequencers rely on a reference GUID in order to retrieve the associated asset.
    """

    # region Dunderscores
    __slots__ = ('_guid', '_asset', '_sequences', '_reference',)

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :rtype: None
        """

        # Call parent method
        #
        super(FbxSequencer, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._guid = kwargs.get('guid', '')
        self._asset = kwargs.get('asset', self.nullWeakReference)
        self._sequences = notifylist.NotifyList()
        self._reference = kwargs.get('reference', fnreference.FnReference())

        # Setup notifies
        #
        self._sequences.addCallback('itemAdded', self.sequenceAdded)
        self._sequences.addCallback('itemRemoved', self.sequenceRemoved)

    def __getattr__(self, name):

        if hasattr(self.asset, name):

            return getattr(self.asset, name)

        else:

            raise AttributeError('__getattr__() "%s" object has no "%s" attribute!' % (type(self).__name__, name))
    # endregion

    # region Properties
    @property
    def guid(self):
        """
        Getter method that returns the GUID for this proxy.

        :rtype: str
        """

        return self._asset

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

        return self._asset

    @property
    def reference(self):
        """
        Getter method that returns the associated reference for this asset.

        :rtype: fnreference.FnReference
        """

        return self._reference

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
    def invalidate(self):

        reference = self._reference.getReferenceByGuid(self.guid)

        if reference is not None:

            self._reference.setObject(reference)
            self._asset = None
    # endregion

    # region Callbacks
    def sequenceAdded(self, index, sequence):
        """
        Adds a reference of this asset to the supplied export set.

        :type index: int
        :type sequence: fbxsequence.FbxSequence
        :rtype: None
        """

        sequence._asset = self.weakReference()

    def sequenceRemoved(self, sequence):
        """
        Removes the reference of this asset from the supplied export set.

        :type sequence: fbxsequence.FbxSequence
        :rtype: None
        """

        sequence._asset = self.nullWeakReference
    # endregion
