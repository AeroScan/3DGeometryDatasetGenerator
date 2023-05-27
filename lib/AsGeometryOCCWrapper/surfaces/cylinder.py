from .base_surfaces import BaseElementarySurface

class Cylinder(BaseElementarySurface):

    @staticmethod
    def getType():
        return 'Cylinder'
    
    def getRadius(self):
        return self._shape.Radius()

    def toDict(self):   
        features = super().toDict()

        features['radius'] = self.getRadius()

        return features