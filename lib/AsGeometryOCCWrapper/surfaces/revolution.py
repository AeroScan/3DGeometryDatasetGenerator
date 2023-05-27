from typing import Union

from OCC.Core.GeomAdaptor import GeomAdaptor_Surface
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.gp import gp_Trsf

from .base_surfaces import BaseSweptSurface

class Revolution(BaseSweptSurface):

    @staticmethod
    def getType():
        return 'Revolution'
    
    def _generateInternalData(self, adaptor: Union[GeomAdaptor_Surface, BRepAdaptor_Surface]):
        super()._generateInternalData(adaptor)
        self._axe_of_revolution = adaptor.AxeOfRevolution()

    def doTransformOCC(self, trsf: gp_Trsf):
        super().doTransformOCC(trsf)
        self._axe_of_revolution.Transform(trsf)

    def getZAxis(self):
        return self._axe_of_revolution.Direction().Coord()
    
    def getLocation(self):
        return self._axe_of_revolution.Location().Coord()

    def toDict(self):
        features = super().toDict()

        features['location'] = self.getLocation()
        features['z_axis'] = self.getZAxis()

        return features