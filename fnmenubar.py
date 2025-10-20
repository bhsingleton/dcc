from . import __executable__, __application__, DCC


if __application__ == DCC.MAYA:

    from .maya.fnmenubar import *

elif __application__ == DCC.MAX:

    from .max.fnmenubar import *

elif __application__ == DCC.BLENDER:

    from .blender.fnmenubar import *

else:

    raise ModuleNotFoundError(f'Unable to import DCC menubar-helpers for: {__executable__}!')
