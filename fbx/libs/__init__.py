from enum import IntEnum


class FbxFileType(IntEnum):

    Binary = 0
    ASCII = 1


class FbxFileVersion(IntEnum):

    FBX200900 = 0
    FBX201000 = 1
    FBX201100 = 2
    FBX201200 = 3
    FBX201300 = 4
    FBX201400 = 5
    FBX201600 = 6
    FBX201800 = 7
    FBX202000 = 8


class FbxMeshComponent(IntEnum):

    Vertex = 0
    Edge = 1
    Polygon = 3


class FbxExportSetType(IntEnum):

    Skeleton = 0
    StaticMesh = 1
    SkeletalMesh = 2
    Camera = 3
