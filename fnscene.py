from dcc.helpers import platform


__application__ = platform.getApplication()


if __application__ == 'maya':

    from dcc.maya.fnscene import *

elif __application__ == '3dsmax':

    from dcc.max.fnscene import *

else:

    raise ImportError('Unable to import dcc scene-helpers for: %s application!' % __application__)