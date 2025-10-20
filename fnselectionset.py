from . import __executable__, __application__, DCC


if __application__ == DCC.MAYA:

    from .maya.fnselectionset import *

elif __application__ == DCC.MAX:

    from .max.fnselectionset import *

elif __application__ == DCC.BLENDER:

    from .blender.fnselectionset import *

else:

    raise ModuleNotFoundError(f'Unable to import DCC set-helpers for: {__executable__}!')
