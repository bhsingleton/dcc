from maya import mel
from ..abstract import afnfbx

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnFbx(afnfbx.AFnFbx):
    """
    Overload of AFnFbx that defines function set behaviours for fbx in Maya.
    """

    __slots__ = ()

    def setMeshExportParams(self, **kwargs):
        """
        Adopts the export settings from the supplied kwargs.

        :rtype: None
        """

        commands = [
            'FBXExportAnimationOnly -v false;',
            'FBXExportBakeComplexAnimation -v false;',
            'FBXExportAxisConversionMethod "none";',
            'FBXExportCacheFile -v false;',
            'FBXExportCameras -v true;',
            'FBXExportConstraints -v false;',
            'FBXExportConvertUnitString "cm";',
            'FBXExportDxfTriangulate -v true;',
            'FBXExportDxfDeformation -v true;',
            'FBXExportEmbeddedTextures -v false;',
            'FBXExportFileVersion "FBX201600";',
            'FBXExportGenerateLog -v true;',
            'FBXExportHardEdges -v true;',
            'FBXExportInAscii -v false;',
            'FBXExportInputConnections -v false;',
            'FBXExportInstances -v false;',
            'FBXExportQuickSelectSetAsCache -v false;',
            'FBXExportReferencedAssetsContent -v false;',
            'FBXExportScaleFactor {scale};'.format(scale=kwargs['scale']),
            'FBXExportShapes -v {includeBlendshapes};'.format(includeBlendshapes=kwargs['includeBlendshapes']),
            'FBXExportSkeletonDefinitions -v false;',
            'FBXExportSkins -v {includeSkins};'.format(includeSkins=kwargs['includeSkins']),
            'FBXExportSmoothingGroups -v {includeSmoothings};'.format(includeSmoothings=kwargs['includeSmoothings']),
            'FBXExportSmoothMesh -v false;',
            'FBXExportSplitAnimationIntoTakes -v false;',
            'FBXExportTangents -v {includeTangentsAndBinormals};'.format(includeTangentsAndBinormals=kwargs['includeTangentsAndBinormals']),
            'FBXExportTriangulate -v true;',
            'FBXExportUpAxis "z";',
            'FBXExportUseSceneName -v false;'
        ]

        mel.eval('\n'.join(commands))

    def setAnimExportParams(self, **kwargs):
        """
        Adopts the animation settings from the supplied kwargs.

        :rtype: None
        """

        commands = [
            'FBXExportAnimationOnly -v true;',
            'FBXExportBakeComplexAnimation -v true;',
            'FBXExportBakeComplexStart {startFrame};'.format(startFrame=kwargs['startFrame']),
            'FBXExportBakeComplexEnd {endFrame};'.format(endFrame=kwargs['endFrame']),
            'FBXExportBakeComplexStep {step};'.format(step=kwargs['step']),
            'FBXExportBakeResampleAnimation -v true;',
            'FBXExportApplyConstantKeyReducer -v false;',
            'FBXExportQuaternion -v false;',
        ]

        mel.eval('\n'.join(commands))

    def exportSelection(self, filePath):
        """
        Exports the active selection to the specified file path.

        :type filePath: str
        :rtype: None
        """

        mel.eval(f'FBXExport -f {filePath} -s;')
