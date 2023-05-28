from OCC.Core.Geom import Geom_SphericalSurface

import numpy as np

from .base_surfaces import BaseElementarySurface

class Sphere(BaseElementarySurface):

    @staticmethod
    def getType():
        return 'Sphere'
    
    @staticmethod
    def adaptor2Geom(adaptor):
        return Geom_SphericalSurface(adaptor.Sphere())
    
    def getRadius(self):
        return self._geom.Radius()

    def toDict(self):   
        features = super().toDict()

        features['radius'] = self.getRadius()

        return features