import os

from maya import mel
from ..fbx.libs import FbxFileVersion
from ..abstract import afnfbx

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnFbx(afnfbx.AFnFbx):
    """
    Overload of AFnFbx that defines the function set behaviours for fbx in Maya.
    See the following for details: https://knowledge.autodesk.com/support/maya/getting-started/caas/CloudHelp/cloudhelp/2023/ENU/Maya-DataExchange/files/GUID-6CCE943A-2ED4-4CEE-96D4-9CB19C28F4E0-htm.html
    """

    __slots__ = ()

    def setMeshExportParams(self, **kwargs):
        """
        Adopts the export settings from the supplied kwargs.

        :key version: FbxFileVersion
        :key asAscii: bool
        :key scale: float
        :key includeSkins: bool
        :key includeBlendshapes: bool
        :key includeSmoothings: bool
        :key includeTangentsAndBinormals: bool
        :rtype: None
        """

        version = kwargs.get('version', FbxFileVersion.FBX202000)
        asAscii = kwargs.get('asAscii', False)
        scale = kwargs.get('scale', 1.0)
        includeSmoothings = kwargs.get('includeSmoothings', True)
        includeTangentsAndBinormals = kwargs.get('includeTangentsAndBinormals', True)
        includeSkins = kwargs.get('includeSkins', True)
        includeBlendshapes = kwargs.get('includeBlendshapes', False)

        commands = [
            'FBXExportAnimationOnly -v false;',
            'FBXExportApplyConstantKeyReducer -v false;',
            'FBXExportAxisConversionMethod "none";',
            'FBXExportBakeComplexAnimation -v false;',
            'FBXExportBakeComplexStart -v 0;',
            'FBXExportBakeComplexEnd -v 1;',
            'FBXExportBakeComplexStep -v 1;',
            'FBXExportBakeResampleAnimation -v false;'
            'FBXExportCacheFile -v false;',
            'FBXExportCameras -v true;',
            'FBXExportConstraints -v false;',
            'FBXExportConvertUnitString "cm";',
            'FBXExportEmbeddedTextures -v false;',
            'FBXExportFileVersion "{version}";'.format(version=version.name),
            'FBXExportGenerateLog -v true;',
            'FBXExportHardEdges -v {includeSmoothings};'.format(includeSmoothings=str(includeSmoothings).lower()),
            'FBXExportInAscii -v {asAscii};'.format(asAscii=str(asAscii).lower()),
            'FBXExportIncludeChildren -v false;',  # Required to skip non-export nodes!
            'FBXExportInputConnections -v false;',  # Required to skip non-export nodes!
            'FBXExportInstances -v false;',
            'FBXExportLights -v false;',
            'FBXExportQuaternion -v "resample";',
            'FBXExportQuickSelectSetAsCache -v false;',
            'FBXExportReferencedAssetsContent -v false;',
            'FBXExportScaleFactor {scale};'.format(scale=scale),
            'FBXExportShapes -v {includeBlendshapes};'.format(includeBlendshapes=str(includeBlendshapes).lower()),
            'FBXExportSkeletonDefinitions -v false;',
            'FBXExportSkins -v {includeSkins};'.format(includeSkins=str(includeSkins).lower()),
            'FBXExportSmoothingGroups -v {includeSmoothings};'.format(includeSmoothings=str(includeSmoothings).lower()),
            'FBXExportSmoothMesh -v false;',
            'FBXExportSplitAnimationIntoTakes -v "Take 001" 0 1;',
            'FBXExportTangents -v {includeTangentsAndBinormals};'.format(includeTangentsAndBinormals=str(includeTangentsAndBinormals).lower()),
            'FBXExportTriangulate -v true;',
            'FBXExportUpAxis "z";',
            'FBXExportUseSceneName -v false;'
        ]

        mel.eval('\r'.join(commands))

    def setAnimExportParams(self, **kwargs):
        """
        Adopts the animation settings from the supplied kwargs.

        :rtype: None
        """

        startFrame = kwargs.get('startFrame', 0)
        endFrame = kwargs.get('endFrame', 1)
        step = kwargs.get('step', 1)

        commands = [
            'FBXExportAnimationOnly -v true;',
            'FBXExportApplyConstantKeyReducer -v false;',
            'FBXExportBakeComplexAnimation -v true;',
            'FBXExportBakeComplexStart {startFrame};'.format(startFrame=startFrame),
            'FBXExportBakeComplexEnd {endFrame};'.format(endFrame=endFrame),
            'FBXExportBakeComplexStep {step};'.format(step=step),
            'FBXExportBakeResampleAnimation -v false;',
            'FBXExportInAscii -v false;',
            'FBXExportIncludeChildren -v false;',  # Required to skip non-export nodes!
            'FBXExportInputConnections -v false;',  # Required to skip non-export nodes!
            'FBXExportInstances -v false;',
            'FBXExportLights -v false;',
            'FBXExportCameras -v true;',
            'FBXExportSplitAnimationIntoTakes -v "Take 001" {startFrame} {endFrame};'.format(startFrame=startFrame, endFrame=endFrame),
            'FBXExportQuaternion -v "resample";',
            'FBXExportUpAxis "z";',
            'FBXExportUseSceneName -v false;'
        ]

        mel.eval('\n'.join(commands))

    def exportSelection(self, filePath):
        """
        Exports the active selection to the specified file path.

        :type filePath: str
        :rtype: bool
        """

        try:

            altPath = filePath.replace(os.sep, os.altsep)
            mel.eval(f'FBXExport -f "{altPath}" -s;')

            return True

        except (RuntimeError, IOError) as exception:

            log.error(exception)
            return False
