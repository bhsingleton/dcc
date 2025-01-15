from . import __executable__, __application__, DCC


if __application__ == DCC.MAYA:

    from .maya.fnscene import *

elif __application__ == DCC.MAX:

    from .max.fnscene import *

else:

    raise ModuleNotFoundError(f'Unable to import DCC scene-helpers for: {__executable__}!')
