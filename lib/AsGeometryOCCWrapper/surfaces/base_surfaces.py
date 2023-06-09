import abc
from typing import Union

from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Pnt2d
from OCC.Core.GeomAdaptor import GeomAdaptor_Surface
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.GeomAPI import GeomAPI_ProjectPointOnSurf
from OCC.Core.GeomLib import geomlib_NormEstim
from OCC.Core.Geom import Geom_Surface

import numpy as np
import open3d as o3d

from ..geometry.base_geometry import BaseGeometry, angleDeviation, distanceDeviation
from ..curves import CurveFactory

class BaseSurface(BaseGeometry, metaclass=abc.ABCMeta):

    MESH_INFO_KEYS = BaseGeometry.MESH_INFO_KEYS + ['face_indices']

    @staticmethod
    @abc.abstractmethod
    def adaptor2Geom(adaptor: Union[BRepAdaptor_Surface, GeomAdaptor_Surface]):
        pass

    def __init__(self, geom: Geom_Surface, topods_orientation: int = 0):
        super().__init__(geom, topods_orientation=topods_orientation)

    def _getPointNormalParamFromProjector(self, projector, normal_tol=1e-3):
        proj_point = projector.NearestPoint()
        u, v = projector.LowerDistanceParameters()
        normal = gp_Dir()
        r = geomlib_NormEstim(self._geom, gp_Pnt2d(u, v),  normal_tol, normal)
        if self._orientation == 1:
            normal.Reverse()
        return proj_point.Coord(), normal.Coord(), (u, v)

    def projectPointsOnGeometry(self, points: list):
        proj_points = []
        proj_normals = []
        proj_params = []

        if len(points) == 0:
            return [], [], []

        projector = GeomAPI_ProjectPointOnSurf()

        projector.Init(gp_Pnt(*(points[0])), self._geom)

        pt, nr, pr = self._getPointNormalParamFromProjector(projector)
        
        proj_points.append(pt)
        proj_normals.append(nr)
        proj_params.append(pr)

        for i in range(1, len(points)):
            projector.Perform(gp_Pnt(*(points[i])))

            pt, nr, pr = self._getPointNormalParamFromProjector(projector)
        
            proj_points.append(pt)
            proj_normals.append(nr)
            proj_params.append(pr)
                
        return proj_points, proj_normals, proj_params
    
    def computeMeshNormals(self, normalized=True):
        self._mesh.compute_vertex_normals(normalized)
        #self._mesh.vertex_normals = o3d.utility.Vector3dVector(-np.asarray(self._mesh.vertex_normals))
    
    def setMeshByGlobal(self, global_mesh: o3d.geometry.TriangleMesh, mesh_info: dict):
        res = super().setMeshByGlobal(global_mesh, mesh_info)

        if res == 0:
            return res
        
        if len(mesh_info['vert_indices']) == 0 or len(mesh_info['face_indices']) == 0:
            return 1
                
        vert_indices = np.asarray(mesh_info['vert_indices'], dtype=np.uint64)
        reverse_vert_map = dict([(vi, i) for i, vi in enumerate(vert_indices)])
        face_indices = np.asarray(mesh_info['face_indices'], dtype=np.uint64)
        faces_local = np.vectorize(reverse_vert_map.get)(np.asarray(global_mesh.triangles)[face_indices])

        self._mesh = o3d.geometry.TriangleMesh()
        self._mesh.vertices = o3d.utility.Vector3dVector(np.asarray(global_mesh.vertices)[vert_indices])
        self._mesh.triangles = o3d.utility.Vector3iVector(faces_local)
        #TODO: add if for the other possible data from global_mesh
    
        if not self._mesh.has_vertex_normals():
            self.computeMeshNormals()
        
        return 4

    def validateMesh(self, dtol: float = 1e-6, atol: float = 10):
        if self._mesh_info is None or self._mesh is None:
            return False
        
        if not self._mesh.has_vertex_normals():
            self.computeMeshNormals()
        
        vertices = np.asarray(self._mesh.vertices)
        normals = np.asarray(self._mesh.vertex_normals)
        params = np.asarray(self._mesh_info['vert_parameters'])

        p_vertices, p_normals, p_params = self.projectPointsOnGeometry(self._mesh.vertices)

        p_vertices = np.asarray(p_vertices)
        p_normals = np.asarray(p_normals)
        p_params = np.asarray(p_params)

        distances = distanceDeviation(vertices, p_vertices)
        dist_erros = distances[distances > dtol]

        deviations = angleDeviation(normals, p_normals)
        dev_errors = deviations[deviations > atol]

        #ERROR
        ret = True
        if len(dist_erros) > 0:
            ret = False
            mean_error = float(np.mean(dist_erros))
            percent_error = (len(dist_erros)/len(distances))
            print(f'[ERROR] Vertices on {self.getType()}: error of {percent_error:.2%} and {mean_error:.8f} m')
        
        if len(dev_errors) > 0:
            ret = False
            mean_error = float(np.mean(dev_errors))
            percent_error = (len(dev_errors)/len(deviations))
            normals_with_error = np.hstack((normals[deviations > atol], p_normals[deviations > atol]))
            print(f'[ERROR] Normals on {self.getType()}: error of {percent_error:.2%} and {mean_error:.2f}° \n {normals_with_error}')
        
        return ret
            

        



class BaseElementarySurface(BaseSurface, metaclass=abc.ABCMeta):

    # def _fixOrientation(self):
    #     if self._orientation == 1:
    #         old_loc = np.array(self.getLocation())
    #         old_xaxis = np.array(self.getXAxis())
    #         old_yaxis = np.array(self.getYAxis())
    #         self._geom.Mirror(gp_Ax2(self._geom.Location(), self._geom.XAxis().Direction(), self._geom.Axis().Direction()))
    #         self._geom.Mirror(gp_Ax2(self._geom.Location(), self._geom.YAxis().Direction(), self._geom.Axis().Direction()))
    #         new_loc = np.array(self.getLocation())
    #         new_xaxis = np.array(self.getXAxis())
    #         new_yaxis = np.array(self.getYAxis())
            
    #         assert np.all(np.isclose(old_xaxis, -new_xaxis)) and  \
    #                np.all(np.isclose(old_yaxis, -new_yaxis)) and  \
    #                np.all(np.isclose(old_loc, new_loc)), \
    #                f'Sanity Check Failed: problem in reversing a {self.getType()}. ' \
    #                f'\n\t\t~~~~~ {old_xaxis} != {-new_xaxis} or ' \
    #                f'{old_yaxis} != {-new_yaxis} or ' \
    #                f'{old_loc} != {new_loc} ~~~~~'
    
    def getLocation(self):
        return self._geom.Position().Location().Coord()

    def getCoefficients(self):
        return list(self._geom.Coefficients())
    
    def getXAxis(self):
        return self._geom.Position().XDirection().Coord()

    def getYAxis(self):
        return self._geom.Position().YDirection().Coord()
    
    def getZAxis(self):
        return self._geom.Position().Direction().Coord()

    def toDict(self):       
        features = super().toDict()
                       
        features['location'] = self.getLocation()
        features['x_axis'] = self.getXAxis()
        features['y_axis'] = self.getYAxis()
        features['z_axis'] = self.getZAxis()
        features['coefficients'] = self.getCoefficients()
            
        return features

class BaseBoundedSurface(BaseSurface, metaclass=abc.ABCMeta):
 
    # def _fixOrientation(self):
    #     if self._orientation == 1:
    #         old_lower_bound = np.array(self.getLowerBound())
    #         old_upper_bound = np.array(self.getUpperBound())
    #         self._geom.UReverse()
    #         self._geom.VReverse()
    #         new_lower_bound = np.array(self.getLowerBound())
    #         new_upper_bound = np.array(self.getUpperBound())
            
    #         assert np.all(np.isclose(old_lower_bound, new_upper_bound)) and \
    #                np.all(np.isclose(old_upper_bound, new_lower_bound)), \
    #                f'Sanity Check Failed: problem in reversing a {self.getType()}. ' \
    #                f'\n\t\t~~~~~ {old_lower_bound} != {new_upper_bound} or' \
    #                f'{old_upper_bound} != {np.flip(new_lower_bound)} ~~~~~'
        
    def getLowerBound(self):
        return tuple(self._geom.Bounds()[2:])

    def getUpperBound(self):
        return tuple(self._geom.Bounds()[:2])

    def toDict(self):
        features = super().toDict()
            
        return features
    
class BaseSweptSurface(BaseSurface, metaclass=abc.ABCMeta):
         
    # def _fixOrientation(self):
    #     pass

    def getCurve(self):
        return CurveFactory.fromGeom(self._geom.BasisCurve(), 
                                     topods_orientation=self._orientation)

    def toDict(self):
        features = super().toDict()

        print(self.getCurve())
        features['curve'] = self.getCurve().toDict()
            
        return features