from OCC.Core.Geom import Geom_ConicalSurface

from .base_surfaces import BaseElementarySurface

class Cone(BaseElementarySurface):

    @staticmethod
    def getType():
        return 'Cone'
    
    @staticmethod
    def adaptor2Geom(adaptor):
        return Geom_ConicalSurface(adaptor.Cone())

    def getRadius(self):
        return self._geom.RefRadius()
    
    def getSemiAngle(self):
        return self._geom.SemiAngle()
    
    def getApex(self):
        return self._geom.Apex().Coord()
    
    def toDict(self):   
        features = super().toDict()

        features['radius'] = self.getRadius()
        features['angle'] = self.getSemiAngle()
        features['apex'] = self.getApex()

        return features