from . import __executable__, __application__, DCC


if __application__ == DCC.MAYA:

    from .maya.fnlayer import *

elif __application__ == DCC.MAX:

    from .max.fnlayer import *

elif __application__ == DCC.BLENDER:

    from .blender.fnlayer import *

else:

    raise ModuleNotFoundError(f'Unable to import DCC layer-helpers for: {__executable__}!')
