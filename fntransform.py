from . import __executable__, __application__, DCC


if __application__ == DCC.MAYA:

    from .maya.fntransform import *

elif __application__ == DCC.MAX:

    from .max.fntransform import *

elif __application__ == DCC.BLENDER:

    from .blender.fntransform import *

else:

    raise ModuleNotFoundError(f'Unable to import DCC transform-helpers for: {__executable__}!')
