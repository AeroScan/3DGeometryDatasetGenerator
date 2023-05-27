from typing import Union

from OCC.Core.GeomAdaptor import GeomAdaptor_Surface
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.gp import gp_Trsf

from .base_surfaces import BaseSweptSurface

class Extrusion(BaseSweptSurface):

    @staticmethod
    def getType():
        return 'Extrusion'
    
    def _generateInternalData(self, adaptor: Union[GeomAdaptor_Surface, BRepAdaptor_Surface]):
        super()._generateInternalData(adaptor)
        self._direction = adaptor.Direction()

    def doTransformOCC(self, trsf: gp_Trsf):
        super().doTransformOCC(trsf)
        self._direction.Transform(trsf)

    def getDirection(self):
        return self._direction.Coord()

    def toDict(self):
        features = super().toDict()

        features['direction'] = self.getDirection()

        return features