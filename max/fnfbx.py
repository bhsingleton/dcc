import pymxs

from .libs import modifierutils, wrapperutils
from .decorators.commandpaneloverride import commandPanelOverride
from ..fbx.libs import FbxFileVersion
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

        version = kwargs.get('version', FbxFileVersion.FBX202000)
        asAscii = kwargs.get('asAscii', False)
        scale = kwargs.get('scale', 1.0)
        includeSmoothings = kwargs.get('includeSmoothings', True)
        includeTangentsAndBinormals = kwargs.get('includeTangentsAndBinormals', True)
        includeSkins = kwargs.get('includeSkins', True)
        includeBlendshapes = kwargs.get('includeBlendshapes', False)

        pymxs.runtime.FBXExporterSetParam('Animation', False)
        pymxs.runtime.FBXExporterSetParam('ExportAnimationOnly', False)
        pymxs.runtime.FBXExporterSetParam('ASCII', asAscii)
        pymxs.runtime.FBXExporterSetParam('AxisConversionMethod', 'None')
        pymxs.runtime.FBXExporterSetParam('Cameras', True)
        pymxs.runtime.FBXExporterSetParam('CAT2HIK', False)
        pymxs.runtime.FBXExporterSetParam('Convert2Tiff', False)
        pymxs.runtime.FBXExporterSetParam('ConvertUnit', 'cm')
        pymxs.runtime.FBXExporterSetParam('EmbedTextures', False)
        pymxs.runtime.FBXExporterSetParam('FileVersion', version.name)
        pymxs.runtime.FBXExporterSetParam('GeomAsBone', True)
        pymxs.runtime.FBXExporterSetParam('GenerateLog', True)
        pymxs.runtime.FBXExporterSetParam('Lights', False)
        pymxs.runtime.FBXExporterSetParam('NormalsPerPoly', False)
        pymxs.runtime.FBXExporterSetParam('PointCache', False)
        pymxs.runtime.FBXExporterSetParam('PopSettings', False)
        pymxs.runtime.FBXExporterSetParam('Preserveinstances', False)
        pymxs.runtime.FBXExporterSetParam('PushSettings', False)
        pymxs.runtime.FBXExporterSetParam('ScaleFactor', scale)
        pymxs.runtime.FBXExporterSetParam('SelectionSet', '')
        pymxs.runtime.FBXExporterSetParam('SelectionSetExport', False)
        pymxs.runtime.FBXExporterSetParam('Shape', includeBlendshapes)
        pymxs.runtime.FBXExporterSetParam('Skin', includeSkins)
        pymxs.runtime.FBXExporterSetParam('ShowWarnings', False)
        pymxs.runtime.FBXExporterSetParam('SmoothingGroups', includeSmoothings)
        pymxs.runtime.FBXExporterSetParam('SmoothMeshExport', False)
        pymxs.runtime.FBXExporterSetParam('TangentSpaceExport', includeTangentsAndBinormals)
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

    @commandPanelOverride(mode='modify')
    def enforceMeshTriangulation(self, nodes):
        """
        Ensures that the supplied meshes are triangulated correctly.

        :type nodes: List[pymxs.MXSWrapperBase]
        :rtype: None
        """

        # Iterate through nodes
        #
        for node in nodes:

            # Check if this is a mesh
            #
            if not wrapperutils.isKindOf(node, (pymxs.runtime.Editable_Mesh, pymxs.runtime.Editable_Poly, pymxs.runtime.PolyMeshObject)):

                continue

            # Redundancy check
            #
            if modifierutils.hasModifier(node, pymxs.runtime.Turn_to_Poly):

                continue

            # Insert turn-to-poly modifier
            #
            modifier = pymxs.runtime.Turn_To_Poly()
            modifier.limitPolySize = True
            modifier.maxPolySize = 3

            pymxs.runtime.addModifier(node, modifier, before=1)

    def exportSelection(self, filePath):
        """
        Exports the active selection to the specified file path.

        :type filePath: str
        :rtype: bool
        """

        try:

            self.enforceMeshTriangulation(pymxs.runtime.Selection)
            pymxs.runtime.exportFile(filePath, pymxs.runtime.name('noPrompt'), selectedOnly=True, using='FBXEXP')

            return True

        except (RuntimeError, IOError) as exception:

            log.error(exception)
            return False
