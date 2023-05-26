from .base_surfaces import BaseElementarySurface

class Torus(BaseElementarySurface):

    @staticmethod
    def getName():
        return 'Torus'
    
    def getCoefficients(self):    
        return []
    
    def getMajorRadius(self):    
        return self._shape.MajorRadius()
    
    def getMinorRadius(self):    
        return self._shape.MinorRadius()

    def toDict(self):
        features = super().toDict()

        features['max_radius'] = self.getMajorRadius()
        features['min_radius'] = self.getMinorRadius()

        return features