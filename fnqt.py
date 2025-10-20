from . import __executable__, __application__, DCC


if __application__ == DCC.MAYA:

    from .maya.fnqt import *

elif __application__ == DCC.MAX:

    from .max.fnqt import *

elif __application__ == DCC.BLENDER:

    from .blender.fnqt import *

else:

    raise ModuleNotFoundError(f'Unable to import DCC Qt-helpers for: {__executable__}!')
