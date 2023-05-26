import numpy as np

from .base_surfaces import BaseElementarySurface

class Sphere(BaseElementarySurface):

    @staticmethod
    def getName():
        return 'Sphere'
    
    def getRadius(self):
        return self._shape.Radius()
    
    def getZAxis(self):
        x_axis = np.array(self.getXAxis())
        y_axis = np.array(self.getYAxis())
        return tuple(np.cross(x_axis, y_axis))

    def toDict(self):   
        features = super().toDict()

        features['radius'] = self.getRadius()

        return features