from OCC.Core.Geom import Geom_Ellipse

from .base_curves import BaseConicCurve

class Ellipse(BaseConicCurve):

    @staticmethod
    def getType():
        return 'Ellipse'
    
    @staticmethod
    def adaptor2Geom(adaptor):
        return Geom_Ellipse(adaptor.Ellipse())
    
    def getFocus1(self):
        return self._geom.Focus1().Coord()
    
    def getFocus2(self):
        return self._geom.Focus2().Coord()
    
    def getMinorRadius(self):
        return self._geom.MinorRadius()
    
    def getMajorRadius(self):
        return self._geom.MajorRadius()

    def toDict(self):        
        features = super().toDict()
        
        features['focus1'] = self.getFocus1()
        features['focus2'] = self.getFocus2()
        features['x_radius'] = self.getMinorRadius()
        features['y_radius'] = self.getMajorRadius()

        return features