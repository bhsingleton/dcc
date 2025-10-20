from . import __executable__, __application__, DCC


if __application__ == DCC.MAYA:

    from .maya.fnnotify import *

elif __application__ == DCC.MAX:

    from .max.fnnotify import *

elif __application__ == DCC.BLENDER:

    from .blender.fnnotify import *

else:

    raise ModuleNotFoundError(f'Unable to import DCC notify-helpers for: {__executable__}!')
