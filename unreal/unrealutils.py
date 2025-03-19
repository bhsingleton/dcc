import clipman

from .. import fnscene, fntransform

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def copyRelativeLocationToClipboard():
    """
    Copies the relative location, from the active selection, to the clipboard.
    This method will inverse the Y-axis to compensate for the right to left handed matrix conversion!

    :rtype: str
    """

    scene = fnscene.FnScene()

    selection = scene.getActiveSelection()
    selectionCount = len(selection)

    if selectionCount == 0:

        log.warning('No nodes selected to copy translation from!')
        return

    node = fntransform.FnTransform()
    success = node.trySetObject(selection[0])

    if success:

        translation = node.translation()
        text = f'(X={translation[0]},Y={-translation[1]},Z={translation[2]})'

        clipman.init()
        clipman.copy(text)

        return text

    else:

        log.warning(f'Failed to copy translation from active sleection!')
        return


def copyRelativeRotationToClipboard():
    """
    Copies the relative rotation, from the active selection, to the clipboard.
    This method will inverse the Y and Z axes to compensate for the right to left handed matrix conversion!

    :rtype: Union[str, None]
    """

    scene = fnscene.FnScene()

    selection = scene.getActiveSelection()
    selectionCount = len(selection)

    if selectionCount == 0:

        log.warning('No nodes selected to copy rotation from!')
        return

    node = fntransform.FnTransform()
    success = node.trySetObject(selection[0])

    if success:

        rotation = node.eulerRotation()
        text = f'(Pitch={-rotation[1]},Yaw={-rotation[2]},Roll={rotation[0]})'

        clipman.init()
        clipman.copy(text)

        return text

    else:

        log.warning(f'Failed to copy rotation from active sleection!')
        return
