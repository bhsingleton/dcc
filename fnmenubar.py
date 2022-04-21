from . import __application__

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


if __application__ == 'maya':

    from .maya.fnmenubar import *

elif __application__ == '3dsmax':

    from .max.fnmenubar import *

else:

    raise ImportError('Unable to import dcc menubar-helpers for: %s application!' % __application__)
