from .base_curves import BaseConicCurve

class Ellipse(BaseConicCurve):

    @staticmethod
    def getName():
        return 'Ellipse'
    
    def getFocus1(self):
        return self._shape.Focus1().Coord()
    
    def getFocus2(self):
        return self._shape.Focus2().Coord()
    
    def getMinorRadius(self):
        return self._shape.MinorRadius()
    
    def getMajorRadius(self):
        return self._shape.MajorRadius()

    def toDict(self):        
        features = super().toDict()
        
        features['focus1'] = self.getFocus1()
        features['focus2'] = self.getFocus2()
        features['x_radius'] = self.getMinorRadius()
        features['y_radius'] = self.getMajorRadius()

        return features