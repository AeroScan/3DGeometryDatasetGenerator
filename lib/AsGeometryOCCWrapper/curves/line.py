from OCC.Core.Geom import Geom_Line

from .base_curves import BaseCurve

class Line(BaseCurve):
    
    @staticmethod
    def getType():
        return 'Line'
    
    @staticmethod
    def adaptor2Geom(adaptor):
        return Geom_Line(adaptor.Line())
    
    def getLocation(self):
        return self._geom.Position().Location().Coord()
    
    def getDirection(self):
        return self._geom.Position().Direction().Coord()

    def toDict(self):
        features = super().toDict()
                       
        features['location'] = self.getLocation()
        features['direction'] = self.getDirection()
            
        return features