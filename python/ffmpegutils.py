import os

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def findFFmpeg():
    """
    Locates the FFmpeg installation from the user's machine.
    If FFmpeg cannot be found then an empty string is returned!

    :rtype: str
    """

    paths = os.environ.get('PATH', '').split(';')

    found = [os.path.join(path, 'ffmpeg.exe') for path in paths if os.path.exists(os.path.join(path, 'ffmpeg.exe'))]
    numFound = len(found)

    if numFound == 0:

        return ''

    elif numFound == 1:

        return os.path.abspath(found[0])

    else:

        log.warning(f'Multiple FFmpeg installations found @ {found}')
        log.info(f'Using first FFmpeg install: {found[0]}')
        return os.path.abspath(found[0])


def hasFFmpeg():
    """
    Evaluates if the user has FFmpeg installed.

    :rtype: bool
    """

    return os.path.exists(findFFmpeg())


def registerFFmpeg(executable):
    """
    Appends the supplied executable to system paths.

    :type executable: str
    :rtype: bool
    """

    # Check if FFmpeg already exists
    #
    if hasFFmpeg():

        return False

    # Check if executable exists
    #
    directory, filename = os.path.split(executable)

    if not (os.path.isfile(executable) and filename.endswith('ffmpeg.exe')):

        return False

    # Append FFmpeg to system path
    #
    log.info(f'$PATH += {directory}')
    os.environ['PATH'] += f';{directory}'

    return True