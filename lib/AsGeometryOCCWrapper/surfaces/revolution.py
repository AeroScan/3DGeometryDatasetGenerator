from typing import Union

from OCC.Core.Geom import Geom_SurfaceOfRevolution
from OCC.Core.GeomAdaptor import GeomAdaptor_Surface
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.gp import gp_Trsf

from .base_surfaces import BaseSweptSurface
from ..curves import CurveFactory

class Revolution(BaseSweptSurface):

    @staticmethod
    def getType():
        return 'Revolution'
    
    @staticmethod
    def adaptor2Geom(adaptor):
        return Geom_SurfaceOfRevolution(CurveFactory.adaptor2Geom(adaptor.BasisCurve())[0], adaptor.AxeOfRevolution())

    def getXAxis(self):
        return self._geom.ReferencePlane().XDirection().Coord()
    
    def getYAxis(self):
        return self._geom.ReferencePlane().YDirection().Coord()

    def getZAxis(self):
        return self._geom.Direction().Coord()
    
    def getLocation(self):
        return self._geom.Location().Coord()

    def toDict(self):
        features = super().toDict()

        features['location'] = self.getLocation()
        features['x_axis'] = self.getXAxis()
        features['y_axis'] = self.getYAxis()
        features['z_axis'] = self.getZAxis()

        return features