from . import __application__

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


if __application__ == 'maya':

    from .maya.fnscene import *

elif __application__ == '3dsmax':

    from .max.fnscene import *

else:

    raise ImportError('Unable to import dcc scene-helpers for: %s application!' % __application__)
