import abc
from typing import Union

from OCC.Core.gp import gp_Ax2, gp_Trsf, gp_Pnt, gp_Dir, gp_Pnt2d
from OCC.Core.GeomAdaptor import GeomAdaptor_Surface
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.GeomAPI import GeomAPI_ProjectPointOnSurf
from OCC.Core.GeomLib import geomlib_NormEstim
from OCC.Core.Geom import Geom_Surface

import numpy as np

from ..geometry.base_geometry import BaseGeometry
from ..curves import CurveFactory

class BaseSurface(BaseGeometry, metaclass=abc.ABCMeta):

    @staticmethod
    @abc.abstractmethod
    def adaptor2Geom(adaptor: Union[BRepAdaptor_Surface, GeomAdaptor_Surface]):
        pass

    def __init__(self, geom: Geom_Surface, topods_orientation: int = 0):
        super().__init__(geom, topods_orientation=topods_orientation)

    def projectPointsOnGeometry(self, points: list):
        proj_points = []
        normals = []
        uvs = []
        if len(points) == 0:
            return proj_points, normals, uvs

        geom_surf = self._getGeomOCC()

        t = gp_Trsf()
        self._geom.Mirror(self._geom.Position().Ax2())
        t.SetMirror(geom_surf.Position().Ax2())
        #print(geom_surf.Axis().Direction().Coord())
        geom_surf.Transform(t)
        print(geom_surf.Axis().Direction().Coord())
        #self.geom_surf.Mirror(self._geom.Position().Ax2())


        projector = GeomAPI_ProjectPointOnSurf()

        projector.Init(gp_Pnt(*(points[0])), geom_surf)
        proj_point = projector.NearestPoint()
        u, v = projector.LowerDistanceParameters()
        normal = gp_Dir()
        r = geomlib_NormEstim(geom_surf, gp_Pnt2d(u, v),  1e-6, normal)
        print(normal.Coord())
        print()



        proj_points.append(list(proj_point.Coord()))
        normals.append(list(normal.Coord()))
        uvs.append([u, v])

        for i in range(1, len(points)):
            projector.Perform(gp_Pnt(*(points[i])))

            proj_point = projector.NearestPoint()
            u, v = projector.LowerDistanceParameters()
            normal = gp_Dir()
            r = geomlib_NormEstim(geom_surf, gp_Pnt2d(u, v),  1e-6, normal)

            proj_points.append(list(proj_point.Coord()))
            normals.append(list(normal.Coord()))
            uvs.append([u, v])
                
        return proj_points, normals, uvs

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

        features['curve'] = self.getCurve().toDict()
            
        return features