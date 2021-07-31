from . import platform

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__application__ = platform.getApplication()


if __application__ == 'maya':

    from .maya.fnqt import *

elif __application__ == '3dsmax':

    from .max.fnqt import *

else:

    raise ImportError('Unable to import dcc qt-helpers for: %s application!' % __application__)
