from . import __executable__, __application__, DCC


if __application__ == DCC.MAYA:

    from .maya.fnskin import *

elif __application__ == DCC.MAX:

    from .max.fnskin import *

elif __application__ == DCC.BLENDER:

    from .blender.fnskin import *

else:

    raise ModuleNotFoundError(f'Unable to import DCC skin-helpers for: {__executable__}!')
