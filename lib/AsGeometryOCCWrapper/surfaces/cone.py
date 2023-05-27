from .base_surfaces import BaseElementarySurface

class Cone(BaseElementarySurface):

    @staticmethod
    def getType():
        return 'Cone'

    def getRadius(self):
        return self._shape.RefRadius()
    
    def getSemiAngle(self):
        return self._shape.SemiAngle()
    
    def getApex(self):
        return self._shape.Apex().Coord()
    
    def toDict(self):   
        features = super().toDict()

        features['radius'] = self.getRadius()
        features['angle'] = self.getSemiAngle()
        features['apex'] = self.getApex()

        return features