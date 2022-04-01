import os
import sys


__executable__ = os.path.normpath(sys.executable)
__application__ = os.path.splitext(os.path.split(__executable__)[1])[0]
