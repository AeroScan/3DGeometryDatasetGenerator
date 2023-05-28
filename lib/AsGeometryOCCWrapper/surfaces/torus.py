from OCC.Core.Geom import Geom_ToroidalSurface

from .base_surfaces import BaseElementarySurface

class Torus(BaseElementarySurface):

    @staticmethod
    def getType():
        return 'Torus'
    
    @staticmethod
    def adaptor2Geom(adaptor):
        return Geom_ToroidalSurface(adaptor.Torus())
    
    def getCoefficients(self):    
        return []
    
    def getMajorRadius(self):    
        return self._geom.MajorRadius()
    
    def getMinorRadius(self):    
        return self._geom.MinorRadius()

    def toDict(self):
        features = super().toDict()

        features['max_radius'] = self.getMajorRadius()
        features['min_radius'] = self.getMinorRadius()

        return features