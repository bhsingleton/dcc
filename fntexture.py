from . import __application__

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


if __application__ == 'maya':

    from .maya.fntexture import *

elif __application__ == '3dsmax':

    from .max.fntexture import *

else:

    raise ImportError('Unable to import dcc texture-helpers for: %s application!' % __application__)
