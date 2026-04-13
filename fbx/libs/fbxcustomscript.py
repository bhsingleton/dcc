import os

from enum import IntEnum
from collections.abc import Sequence, Mapping
from . import fbxbase, FbxExportStatus
from ... import fnscene
from ...ui import qfileedit
from ...json import jsonutils
from ...python import importutils, stringutils

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Language(IntEnum):
    """
    Enum class of all executable languages.
    """

    PYTHON = 0
    EMBEDDED = 1


class FbxCustomScript(fbxbase.FbxBase):
    """
    Overload of `FbxBase` used for calling export wrappers.
    """

    # region Dunderscores
    __slots__ = (
        '_parent',
        '_scene',
        '_filePath',
        '_script',
        '_language',
        '_args',
        '_kwargs'
    )

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.
        """

        # Call parent method
        #
        super(FbxCustomScript, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._parent = self.nullWeakReference()
        self._scene = fnscene.FnScene()
        self._filePath = ''
        self._script = ''
        self._language = Language.PYTHON
        self._args = ''
        self._kwargs = ''
    # endregion

    # region Properties
    @property
    def parent(self):
        """
        Getter method that returns the parent of this custom script.

        :rtype: Union[fbxexportset.FbxExportSet, fbxexportrange.FbxExportRange]
        """

        return self._parent()

    @property
    def scene(self):
        """
        Getter method that returns the scene interface.

        :rtype: fnscene.FnScene
        """

        return self._scene

    @property
    def filePath(self):
        """
        Getter method that returns the file path to execute.

        :rtype: str
        """

        return self._filePath

    @filePath.setter
    def filePath(self, filePath):
        """
        Setter method that updates the file path to execute.

        :type filePath: str
        :rtype: None
        """

        self._filePath = filePath

    @property
    def script(self):
        """
        Getter method that returns the script to execute.

        :rtype: str
        """

        return self._script

    @script.setter
    def script(self, script):
        """
        Setter method that updates the script to execute.

        :type script: str
        :rtype: None
        """

        self._script = script

    @property
    def language(self):
        """
        Getter method that returns the script language to use.

        :rtype: Language
        """

        return self._language

    @language.setter
    def language(self, language):
        """
        Setter method that updates the script language to use.

        :type language: Language
        :rtype: None
        """

        self._language = Language(language)

    @property
    def args(self):
        """
        Getter method that returns the arguments.

        :rtype: str
        """

        return self._args

    @args.setter
    def args(self, args):
        """
        Setter method that updates the arguments.

        :type args: str
        :rtype: None
        """

        self._args = args

    @property
    def kwargs(self):
        """
        Getter method that returns the keyword arguments.

        :rtype: str
        """

        return self._kwargs

    @kwargs.setter
    def kwargs(self, kwargs):
        """
        Setter method that updates the keyword arguments.

        :type kwargs: str
        :rtype: None
        """

        self._kwargs = kwargs
    # endregion

    # region Methods
    @classmethod
    def createEditor(cls, name, parent=None):
        """
        Returns a Qt editor for the specified property.

        :type name: str
        :type parent: Union[QtWidgets.QWidget, None]
        :rtype: Union[QtWidgets.QWidget, None]
        """

        if name == 'filePath':

            return qfileedit.QFileEdit(filter='Script Files (*.ms *.mel *.py)', parent=parent)

        else:

            return super(FbxCustomScript, cls).createEditor(name, parent=parent)

    def exists(self):
        """
        Evaluates whether this custom script exists.

        :rtype: bool
        """

        return os.path.exists(self.filePath)

    def parseArguments(self):
        """
        Parses the arguments and keyword argument strings.

        :rtype: Tuple[tuple, dict]
        """

        # Evaluate arguments
        #
        args = ()

        if not stringutils.isNullOrEmpty(self.args):

            args = jsonutils.loads(self.args, default=())

        # Evaluate keyword arguments
        #
        kwargs = {}

        if not stringutils.isNullOrEmpty(self.kwargs):

            kwargs = jsonutils.loads(self.kwargs, default={})

        # Evaluate argument types
        #
        if isinstance(args, Sequence) and isinstance(kwargs, Mapping):

            return args, kwargs

        else:

            return (), {}

    def executeModule(self, name, status):
        """
        Executes the export wrapper with the associated name.

        :type name: str
        :type status: FbxExportStatus
        :rtype: bool
        """

        # Check if wrapper file exists
        #
        cwd = os.path.dirname(os.path.abspath(__file__))
        moduleName = name.lower()

        filePath = os.path.abspath(os.path.join(cwd, '..', 'wrappers', f'{moduleName}.py'))

        if not os.path.isfile(filePath):

            log.warning(f'Unable to locate export wrapper: {filePath}')
            return False

        # Try and import module
        #
        importPath = f'dcc.fbx.wrappers.{moduleName}'
        module = importutils.tryImport(importPath, default=None)

        if module is None:

            log.warning(f'Unable to import export wrapper: {importPath}')
            return False

        # Check if wrapper class exists
        #
        cls = getattr(module, name, None)

        if not callable(cls):

            log.warning(f'Unable to locate wrapper class: {name}')
            return False

        # Evaluate export status
        #
        wrapper = cls(self.parent)
        args, kwargs = self.parseArguments()

        if status == FbxExportStatus.PRE_EXPORT:

            wrapper.preExport(*args, **kwargs)
            return True

        elif status == FbxExportStatus.POST_EXPORT:

            wrapper.postExport(*args, **kwargs)
            return True

        else:

            return False

    def executeFile(self, filePath):
        """
        Executes the supplied file path.

        :type filePath: str
        :rtype: bool
        """

        return self.scene.executeFile(filePath)

    def executeScript(self, script, language):
        """
        Executes the supplied script in the specified language.

        :type script: str
        :type language: Language
        :rtype: bool
        """

        asPython = (self.language == Language.PYTHON)

        if asPython:

            return self.scene.executePython(script)

        else:

            return self.scene.execute(script)

    def preExport(self, exporter):
        """
        Executes the pre-export override.

        :type exporter: Union[fbxexportset.FbxExportSet, fbxexportrange.FbxExportRange]
        :rtype: None
        """

        # Check if name is valid
        #
        if not self.scene.isNullOrEmpty(self.name):

            self.executeModule(self.name, FbxExportStatus.PRE_EXPORT)

        # Check if file path is valid
        #
        if not self.scene.isNullOrEmpty(self.filePath):

            self.executeFile(self.filePath)

        # Check if script is valid
        #
        if not self.scene.isNullOrEmpty(self.script):

            self.executeScript(self.script, self.language)

    def postExport(self, exporter):
        """
        Executes the post-export override.

        :type exporter: Union[fbxexportset.FbxExportSet, fbxexportrange.FbxExportRange]
        :rtype: None
        """

        # Check if name is valid
        #
        if not self.scene.isNullOrEmpty(self.name):

            self.executeModule(self.name, FbxExportStatus.POST_EXPORT)

        # Check if file path is valid
        #
        if not self.scene.isNullOrEmpty(self.filePath):

            self.executeFile(self.filePath)

        # Check if script is valid
        #
        if not self.scene.isNullOrEmpty(self.script):

            self.executeScript(self.script, self.language)
    # endregion
