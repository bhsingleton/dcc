import pymxs
from ..abstract import afnfbx

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FnFbx(afnfbx.AFnFbx):
    """
    Overload of AFnFbx that defines function set behaviours for fbx in 3DS Max.
    """

    __slots__ = ()

    def setMeshExportParams(self, **kwargs):
        """
        Adopts the export settings from the supplied kwargs.

        :rtype: None
        """

        pymxs.runtime.FBXExporterSetParam('ResetExport', True)
        pymxs.runtime.FBXExporterSetParam('Animation', False)
        pymxs.runtime.FBXExporterSetParam('ExportAnimationOnly', False)
        pymxs.runtime.FBXExporterSetParam('ASCII', False)
        pymxs.runtime.FBXExporterSetParam('AxisConversionMethod', 'None')
        pymxs.runtime.FBXExporterSetParam('Cameras', True)
        pymxs.runtime.FBXExporterSetParam('CAT2HIK', False)
        pymxs.runtime.FBXExporterSetParam('Convert2Tiff', False)
        pymxs.runtime.FBXExporterSetParam('ConvertUnit', 'cm')
        pymxs.runtime.FBXExporterSetParam('EmbedTextures', False)
        pymxs.runtime.FBXExporterSetParam('FileVersion', 'FBX201600')
        pymxs.runtime.FBXExporterSetParam('GeomAsBone', True)
        pymxs.runtime.FBXExporterSetParam('GenerateLog', True)
        pymxs.runtime.FBXExporterSetParam('Lights', False)
        pymxs.runtime.FBXExporterSetParam('LoadExportPresetFile', '')
        pymxs.runtime.FBXExporterSetParam('NormalsPerPoly', False)
        pymxs.runtime.FBXExporterSetParam('PointCache', False)
        pymxs.runtime.FBXExporterSetParam('PopSettings', False)
        pymxs.runtime.FBXExporterSetParam('Preserveinstances', False)
        pymxs.runtime.FBXExporterSetParam('PushSettings', False)
        pymxs.runtime.FBXExporterSetParam('ScaleFactor', kwargs['scale'])
        pymxs.runtime.FBXExporterSetParam('SelectionSet', '')
        pymxs.runtime.FBXExporterSetParam('SelectionSetExport', False)
        pymxs.runtime.FBXExporterSetParam('Shape', kwargs['includeBlendshapes'])
        pymxs.runtime.FBXExporterSetParam('Skin', kwargs['includeSkins'])
        pymxs.runtime.FBXExporterSetParam('ShowWarnings', False)
        pymxs.runtime.FBXExporterSetParam('SmoothingGroups', kwargs['includeSmoothings'])
        pymxs.runtime.FBXExporterSetParam('SmoothMeshExport', False)
        pymxs.runtime.FBXExporterSetParam('TangentSpaceExport', kwargs['includeTangentsAndBinormals'])
        pymxs.runtime.FBXExporterSetParam('Triangulate', True)
        pymxs.runtime.FBXExporterSetParam('PreserveEdgeOrientation', True)
        pymxs.runtime.FBXExporterSetParam('UpAxis', 'Z')
        pymxs.runtime.FBXExporterSetParam('UseSceneName', False)

    def setAnimExportParams(self, **kwargs):
        """
        Adopts the animation settings from the supplied kwargs.

        :rtype: None
        """

        pymxs.runtime.FBXExporterSetParam('ExportAnimationOnly', True)
        pymxs.runtime.FBXExporterSetParam('Animation', True)
        pymxs.runtime.FBXExporterSetParam('BakeAnimation', True)
        pymxs.runtime.FBXExporterSetParam('BakeFrameStart', kwargs['startFrame'])
        pymxs.runtime.FBXExporterSetParam('BakeFrameEnd', kwargs['endFrame'])
        pymxs.runtime.FBXExporterSetParam('BakeFrameStep', kwargs['step'])
        pymxs.runtime.FBXExporterSetParam('BakeResampleAnimation', True)
        pymxs.runtime.FBXExporterSetParam('Removesinglekeys', False)
        pymxs.runtime.FBXExporterSetParam('Resampling', 1.0)
        pymxs.runtime.FBXExporterSetParam('FilterKeyReducer', False)
        pymxs.runtime.FBXExporterSetParam('SplitAnimationIntoTakes', False)

    def exportSelection(self, filePath):
        """
        Exports the active selection to the specified file path.

        :type filePath: str
        :rtype: None
        """

        pymxs.runtime.exportFile(filePath, pymxs.runtime.name('noPrompt'), selectedOnly=True, using='FBXEXP')
