from .base_curves import BaseConicCurve

class Circle(BaseConicCurve):

    @staticmethod
    def getType():
        return 'Circle'
    
    def getRadius(self):
        return self._shape.Radius()

    def toDict(self):        
        features = super().toDict()
        
        features['radius'] = self.getRadius()

        return features