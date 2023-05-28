from OCC.Core.Geom import Geom_Circle

from .base_curves import BaseConicCurve

class Circle(BaseConicCurve):

    @staticmethod
    def getType():
        return 'Circle'

    @staticmethod
    def adaptor2Geom(adaptor):
        return Geom_Circle(adaptor.Circle())
    
    def getRadius(self):
        return self._geom.Radius()

    def toDict(self):        
        features = super().toDict()
        
        features['radius'] = self.getRadius()

        return features