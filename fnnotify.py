from . import platform

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__application__ = platform.getApplication()


if __application__ == 'maya':

    from .maya.fnnotify import *

elif __application__ == '3dsmax':

    from .max.fnnotify import *

else:

    raise ImportError('Unable to import dcc notify-helpers for: %s application!' % __application__)
