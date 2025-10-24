import os
import json

from maya import cmds as mc
from ...json import jsonutils
from ...python import stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def iterUserCommands():
    """
    Returns a generator that yields user runtime commands.

    :rtype: Iterator[str]
    """

    commands = mc.runTimeCommand(query=True, userCommandArray=True)

    if not stringutils.isNullOrEmpty(commands):

        return iter(commands)

    else:

        return iter([])


def hasCategory(command, category):
    """
    Evaluates if the supplied command is derived from the specified category.

    :type command: str
    :type category: str
    :rtype: bool
    """

    try:

        return category in mc.runTimeCommand(command, query=True, category=True)

    except RuntimeError:

        return False


def loadRuntimeCommands(filePath):
    """
    Returns the user commands from the supplied file.

    :type filePath: str
    :rtype: Tuple[str, List[str]]
    """

    # Check if file exists
    #
    category = ''
    commands = []

    if not os.path.isfile(filePath) or not filePath.endswith('.json'):

        return category, commands

    # Try and load json file
    #
    try:

        with open(filePath) as jsonFile:

            data = json.load(jsonFile)
            category, commands = data['category'], data['commands']

    except (json.JSONDecodeError, TypeError, KeyError) as exception:

        log.warning(exception)

    finally:

        return category, commands


def installRuntimeCommands(filePath):
    """
    Installs runtime-commands from the supplied JSON file.

    :type commandSpec: str
    :rtype: bool
    """

    # Load user commands
    #
    category, commands = loadRuntimeCommands(filePath)

    if stringutils.isNullOrEmpty(category) or stringutils.isNullOrEmpty(commands):

        return False

    # Remove deprecated commands
    #
    existing = [command for command in iterUserCommands() if hasCategory(command, category)]
    incoming = [command.get('name', '') for command in commands]

    deprecated = [command for command in existing if command not in incoming]

    for command in deprecated:

        log.info(f'Removing {command} runtime command...')
        mc.runTimeCommand(command, edit=True, delete=True)

    # Iterate through new commands
    #
    for command in commands:

        # Get command properties
        #
        name = command.get('name', '')
        annotation = command.get('annotation', '')
        language = command.get('language', None)
        code = ';\n'.join(command.get('code', []))

        if any([stringutils.isNullOrEmpty(x) for x in (name, annotation, language, code)]):

            log.warning(f'Unable to create "{name}" runtime command!')
            continue

        # Check if command already exists
        #
        if mc.runTimeCommand(name, exists=True):

            # Edit command
            #
            log.info(f'Overwriting "{name}" runtime command.')

            mc.runTimeCommand(
                name,
                edit=True,
                commandLanguage=language,
                category=category,
                annotation=annotation,
                command=code,
                showInHotkeyEditor=True
            )

        else:

            # Add command
            #
            log.info(f'Adding "{name}" runtime command.')

            mc.runTimeCommand(
                name,
                commandLanguage=language,
                category=category,
                annotation=annotation,
                command=code,
                showInHotkeyEditor=True
            )

    return True
