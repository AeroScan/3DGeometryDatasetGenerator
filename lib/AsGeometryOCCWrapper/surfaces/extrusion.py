from typing import Union

from OCC.Core.GeomAdaptor import GeomAdaptor_Surface
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.gp import gp_Trsf
from OCC.Core.Geom import Geom_SurfaceOfLinearExtrusion

from .base_surfaces import BaseSweptSurface
from ..curves import CurveFactory

class Extrusion(BaseSweptSurface):

    @staticmethod
    def getType():
        return 'Extrusion'
    
    @staticmethod
    def adaptor2Geom(adaptor):
        return Geom_SurfaceOfLinearExtrusion(CurveFactory.adaptor2Geom(adaptor.BasisCurve()), adaptor.Direction())

    def getDirection(self):
        return self._geom.Direction().Coord()

    def toDict(self):
        features = super().toDict()

        features['direction'] = self.getDirection()

        return features