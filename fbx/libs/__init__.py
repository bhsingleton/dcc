from enum import IntEnum


class FbxFileType(IntEnum):
    """
    Enum class of all the available FBX file types.
    """

    Binary = 0
    ASCII = 1


class FbxFileVersion(IntEnum):
    """
    Enum class of all the available FBX file versions.
    """

    FBX200900 = 0
    FBX201000 = 1
    FBX201100 = 2
    FBX201200 = 3
    FBX201300 = 4
    FBX201400 = 5
    FBX201600 = 6
    FBX201800 = 7
    FBX202000 = 8


class FbxExportStatus(IntEnum):
    """
    Enum class of all the possible export states.
    """

    Pending = 0
    Pre = 1
    Post = 2
    Complete = 2
