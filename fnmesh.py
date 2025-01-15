from . import __executable__, __application__, DCC


if __application__ == DCC.MAYA:

    from .maya.fnmesh import *

elif __application__ == DCC.MAX:

    from .max.fnmesh import *

else:

    raise ModuleNotFoundError(f'Unable to import DCC mesh-helpers for: {__executable__}!')
