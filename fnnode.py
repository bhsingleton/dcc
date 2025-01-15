from . import __executable__, __application__, DCC


if __application__ == DCC.MAYA:

    from .maya.fnnode import *

elif __application__ == DCC.MAX:

    from .max.fnnode import *

else:

    raise ModuleNotFoundError(f'Unable to import DCC node-helpers for: {__executable__}!')
