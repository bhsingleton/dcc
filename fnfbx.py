from . import __executable__, __application__, DCC


if __application__ == DCC.MAYA:

    from .maya.fnfbx import *

elif __application__ == DCC.MAX:

    from .max.fnfbx import *

elif __application__ == DCC.BLENDER:

    from .blender.fnfbx import *

else:

    raise ModuleNotFoundError(f'Unable to import DCC FBX-helpers for: {__executable__}!')
