import os
import re
import sys

from maya import cmds as mc
from collections import defaultdict, namedtuple
from . import sceneutils
from ...python import importutils, pathutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__config_regex__ = re.compile(r'^\+\s?(?:MAYAVERSION:([0-9]{4})\s?)?(?:PLATFORM:([a-z0-9]+)\s?)?(?:LOCALE:([a-zA-Z_]+)\s?)?([a-zA-Z_\-]+)\s([0-9\.]+)\s([a-zA-Z0-9_\/\\:\$\-]+)$')
__variable_regex__ = re.compile(r'^([a-zA-Z_\-]+)(?:\s?)([\+\:\=]+)(?:\s?)([a-zA-Z0-9_\-\/\\\.]+)$')


Configuration = namedtuple('Configuration', ('year', 'platform', 'locale', 'title', 'version', 'location'))
AssignmentInfo = namedtuple('AssignmentInfo', ('key', 'operator', 'value'))


def isLoaded(filePath):
    """
    Evaluates if the supplied module file has already been loaded.

    :type filePath: str
    :rtype: bool
    """

    cwd = pathutils.normalizePath(os.path.dirname(filePath))
    paths = os.environ['MAYA_MODULE_PATH'].split(os.pathsep)

    return cwd in paths


def parseModule(filePath):
    """
    Parses the supplied file for module configurations.

    :type filePath: str
    :rtype: List[Tuple[Configuration, List[AssignmentInfo]]]
    """

    # Evaluate path type
    #
    if not isinstance(filePath, str):

        raise TypeError(f'loadModule() expects a str ({type(filePath).__name__} given)!')

    # Check if path exists
    #
    if not (os.path.isfile(filePath) and filePath.endswith('.mod')):

        raise TypeError(f'loadModule() expects a valid module file: {filePath}')

    # Read lines from module file
    #
    lines = []

    with open(filePath, 'r') as file:

        lines = [line.strip() for line in file.readlines()]

    filteredLines = list(filter(lambda line: not (len(line) == 0 or line.startswith('#')), lines))

    # Evaluate line count
    #
    numLines = len(filteredLines)

    if not (numLines >= 1):

        raise TypeError(f'loadModule() expects a non-empty module file: {filePath}')

    # Evaluate configuration count
    #
    occurrences = [i for (i, line) in enumerate(filteredLines) if line.startswith('+')]
    occurrences.append(numLines)

    numOccurrences = len(occurrences)

    if not (numOccurrences >= 2):

        raise TypeError(f'loadModule() expects at least 1 configuration ({numOccurrences} found)!')

    # Group together and iterate through configurations
    #
    groups = [filteredLines[startIndex:nextIndex] for (startIndex, nextIndex) in zip(occurrences[:-1], occurrences[1:])]
    configurations = []

    for group in groups:

        # Check if configuration is valid
        #
        config = group[0]

        results = __config_regex__.findall(config)
        isValid = len(results) == 1

        if not isValid:

            log.warning(f'Skipping invalid configuration: {config}')
            continue

        configuration = Configuration(*results[0])

        # Check if configuration has any variable assignments
        #
        hasVariables = len(group) >= 2

        if not hasVariables:

            configurations.append((configuration, []))
            continue

        # Iterate through variable assignments
        #
        variables = defaultdict(list)
        assignments = []

        for assignment in group[1:]:

            results = __variable_regex__.findall(assignment)
            isValid = len(results) == 1

            if not isValid:

                log.warning(f'Skipping invalid variable assignment: {assignment}')
                continue

            assignmentInfo = AssignmentInfo(*results[0])
            assignments.append(assignmentInfo)

        configurations.append((configuration, assignments))

    return configurations


def tryParseModule(filePath):
    """
    Parses the supplied file for module configurations without raising `TypeError` exceptions.

    :type filePath: str
    :rtype: List[Tuple[Configuration, List[AssignmentInfo]]]
    """

    try:

        return parseModule(filePath)

    except TypeError:

        return []


def loadModule(filePath):
    """
    Attempts to load the supplied module.

    :type filePath: str
    :rtype: bool
    """

    # Check if module file has already been loaded
    #
    if isLoaded(filePath):

        return True

    # Parse module file
    #
    configurations = tryParseModule(filePath)
    numConfigurations = len(configurations)

    if numConfigurations == 0:

        return False

    # Find config compatible with this version of Maya
    #
    year = str(sceneutils.getMayaVersion())

    found = [(config, assignments) for (config, assignments) in configurations if config.year == year or len(config.year) == 0]
    numFound = len(found)

    if numFound == 0:

        return False

    # Collect environment changes
    #
    cwd = pathutils.normalizePath(os.path.dirname(filePath))
    config, assignments = found[0]
    log.info(f'Loading module: {config}')

    environmentMap = {'icons': 'XBMLANGPATH', 'scripts': 'MAYA_SCRIPT_PATH', 'plug-ins': 'MAYA_PLUG_IN_PATH', 'presets': 'MAYA_PRESET_PATH'}
    environmentRecord = {}
    environmentChanges = {}

    for assignment in assignments:

        # Decompose environment variable
        #
        key = environmentMap.get(assignment.key, assignment.key)
        values = environmentChanges.get(key, None)

        if values is None:

            values = set(filter(lambda string: len(string) > 0, os.environ.get(key, '').split(';')))
            environmentChanges[key] = values
            environmentRecord[key] = len(values)

        # Evaluate assignment operator
        #
        operator = assignment.operator
        value = pathutils.normalizePath(assignment.value)

        if operator == ':':  # Override default structure (icons, scripts, plug-ins, etc)

            value = value if os.path.isabs(value) else f'{cwd}/{value}'

        elif operator == '=':  # Set environment value

            values.clear()

        elif operator == '+=':  # Append path

            pass

        elif operator == ':=':  # Set path relative to this module

            values.clear()
            value = f'{cwd}/{value}'

        elif operator == '+:=':  # Append path relative to this module

            value = f'{cwd}/{value}'

        else:

            log.warning(f'Skipping unknown assignment operator: {operator}')
            continue

        log.debug(f'${key}{operator}{value}')
        values.add(value)

    # Push environment changes
    #
    for (key, values) in environmentChanges.items():

        values = tuple(values)

        numValues = len(values)
        numOriginal = environmentRecord.get(key, numValues)

        if numValues != numOriginal:

            value = ';'.join(values) if numValues > 1 else values[0]

            log.debug(f'{key}={value}')
            os.environ[key] = value

        else:

            log.debug(f'No changes made @ ${key}')
            continue

    importutils.synchronizeSystemPaths()

    # Finalize environment change
    #
    os.environ['MAYA_MODULE_PATH'] += f';{cwd}'

    return True
