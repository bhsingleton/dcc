from . import __executable__, __application__, DCC


if __application__ == DCC.MAYA:

    from .maya.fntexture import *

elif __application__ == DCC.MAX:

    from .max.fntexture import *

elif __application__ == DCC.BLENDER:

    from .blender.fntexture import *

else:

    raise ModuleNotFoundError(f'Unable to import DCC texture-helpers for: {__executable__}!')
