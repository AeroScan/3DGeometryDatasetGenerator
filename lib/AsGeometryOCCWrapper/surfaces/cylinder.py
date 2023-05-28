from OCC.Core.Geom import Geom_CylindricalSurface

from .base_surfaces import BaseElementarySurface

class Cylinder(BaseElementarySurface):

    @staticmethod
    def getType():
        return 'Cylinder'
    
    @staticmethod
    def adaptor2Geom(adaptor):
        return Geom_CylindricalSurface(adaptor.Cylinder())
    
    def getRadius(self):
        return self._geom.Radius()

    def toDict(self):   
        features = super().toDict()

        features['radius'] = self.getRadius()

        return features