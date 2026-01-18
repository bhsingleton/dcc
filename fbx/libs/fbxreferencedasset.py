from . import fbxbase, fbxio, fbxasset, fbxexportrange
from ... import fnreference
from ...python import stringutils
from ...collections import notifylist

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FbxReferencedAsset(fbxbase.FbxBase):
    """
    Overload of `FbxBase` that interfaces with referenced assets.
    Fbx export-ranges rely on reference GUIDs in order to associate them with an export-set from a referenced asset.
    """

    # region Dunderscores
    __slots__ = ('_manager', '_guid', '_reference', '_asset', '_exportRanges')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :type guid: str
        :type exportRanges: List[fbxexportranges.FbxExportRanges]
        :rtype: None
        """

        # Call parent method
        #
        super(FbxReferencedAsset, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._manager = fbxio.FbxIO()
        self._guid = ''
        self._reference = fnreference.FnReference()
        self._asset = self.nullWeakReference
        self._exportRanges = notifylist.NotifyList()

        # Setup notifies
        #
        self._exportRanges.addCallback('itemAdded', self.exportRangeAdded)
        self._exportRanges.addCallback('itemRemoved', self.exportRangeRemoved)

    def __post_init__(self, *args, **kwargs):
        """
        Private method called after this instance has been initialized.

        :rtype: None
        """

        # Call parent method
        #
        super(FbxReferencedAsset, self).__post_init__(*args, **kwargs)

        # Invalidate sequencer
        #
        if not stringutils.isNullOrEmpty(self.guid):

            self.invalidate()
    # endregion

    # region Properties
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
    def reference(self):
        """
        Getter method that returns the associated reference for this asset.

        :rtype: fnreference.FnReference
        """

        return self._reference

    @property
    def asset(self):
        """
        Getter method that returns the associated asset.

        :rtype: fbxasset.FbxAsset
        """

        return self._asset()

    @property
    def exportRanges(self):
        """
        Getter method that returns the FBX export-ranges for this asset.

        :rtype: List[fbxexportrange.FbxExportRange]
        """

        return self._exportRanges

    @exportRanges.setter
    def exportRanges(self, exportRanges):
        """
        Setter method that returns the FBX export-ranges for this asset.

        :type exportRanges: List[fbxexportrange.FbxExportRange]
        :rtype: None
        """

        self._exportRanges.clear()
        self._exportRanges.extend(exportRanges)
    # endregion

    # region Callbacks
    def exportRangeAdded(self, index, exportRange):
        """
        Adds a reference of this asset to the supplied export set.

        :type index: int
        :type exportRange: fbxexportrange.FbxExportRange
        :rtype: None
        """

        exportRange._referencedAsset = self.weakReference()
        exportRange.refresh()

    def exportRangeRemoved(self, exportRange):
        """
        Removes the reference of this asset from the supplied export set.

        :type exportRange: fbxexportrange.FbxExportRange
        :rtype: None
        """

        exportRange._referencedAsset = self.nullWeakReference
        exportRange.refresh()
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

            return self.reference.associatedNamespace()

        else:

            return ''

    def invalidate(self):
        """
        Invalidates all the dynamic components that make up this sequencer.

        :rtype: None
        """

        self.invalidateReference()
        self.invalidateAsset()
        self.invalidateExportRanges()

    def invalidateReference(self):
        """
        Invalidates the reference interface against the current GUID.

        :rtype: bool
        """

        # Locate associated reference
        #
        reference = self._reference.getReferenceByGuid(self.guid)

        if reference is None:

            log.warning(f'Cannot locate reference from: {self.guid}')
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
        asset = self.manager.loadAssetFromReference(self.reference)

        if asset is not None:

            self._asset = asset.weakReference()
            return True

        else:

            self._asset = self.nullWeakReference
            return False

    def invalidateExportRanges(self):
        """
        Invalidates the internal export-ranges.
        This will ensure the 'exportSetId' property's return type is up-to-date!

        :rtype: bool
        """

        # Refresh export-ranges
        #
        for exportRange in self.exportRanges:

            exportRange.refresh()

        return True
    # endregion
