import win32api  # Required for pythoncom to import!
import pythoncom

from win32com import storagecon

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


FMTID_UserDefinedProperties = '{F29F85E0-4FF9-1068-AB91-08002B27B3D9}'
FMTID_CustomDefinedProperties = '{D5CDD505-2E9C-101B-9397-08002B2CF9AE}'


def iterFileProperties(filePath):
    """
    Returns a generator that yields custom properties from the supplied file.

    :type filePath: str
    :rtype: iter
    """

    # Check if path represents a storage file
    #
    if not pythoncom.StgIsStorageFile(filePath):

        log.warning('iterFileProperties() expects a storage file!')
        return

    # Initialize storage container
    #
    flags = storagecon.STGM_READ | storagecon.STGM_SHARE_EXCLUSIVE
    fileStorage = pythoncom.StgOpenStorage(filePath, None, flags)

    # Open custom property storage
    #
    propertySetStorage = fileStorage.QueryInterface(pythoncom.IID_IPropertySetStorage)
    propertyStorage = propertySetStorage.Open(FMTID_CustomDefinedProperties, flags)

    for (name, propertyId, varType) in propertyStorage:

        for value in propertyStorage.ReadMultiple([propertyId]):

            yield name, value


def getFileProperties(filePath):
    """
    Returns a list of custom properties from the supplied file.

    :type filePath: str
    :rtype: Dict[str, str]
    """

    return dict(iterFileProperties(filePath))


def setFileProperties(filePath, properties):
    """
    Updates the custom properties for the specified file.

    :type filePath: str
    :type properties: Dict[str, str]
    :rtype: None
    """

    # Check if path represents a storage file
    #
    if not pythoncom.StgIsStorageFile(filePath):

        log.warning('setFileProperties() expects a storage file!')
        return

    # Get existing custom properties
    # Otherwise a share violation will be raised while the container is open for editing!
    #
    customProperties = getFileProperties(filePath)
    customProperties.update(properties)

    # Initialize storage container
    #
    flags = storagecon.STGM_READWRITE | storagecon.STGM_SHARE_EXCLUSIVE
    fileStorage = pythoncom.StgOpenStorage(filePath, None, flags)

    # Edit custom property storage
    #
    propertySetStorage = fileStorage.QueryInterface(pythoncom.IID_IPropertySetStorage)
    propertyStorage = propertySetStorage.Open(FMTID_CustomDefinedProperties, flags)

    propertyStorage.WriteMultiple(list(customProperties.keys()), list(customProperties.values()))

    # Commit changes to storage container
    #
    log.info('Committing storage changes to: %s' % filePath)
    propertyStorage.Commit(0x8)


def setFileProperty(filePath, key, value):
    """
    Updates a custom property for the specified file.

    :type filePath: str
    :type key: str
    :type value: Any
    :rtype: None
    """

    setFileProperties(filePath, {key: value})
