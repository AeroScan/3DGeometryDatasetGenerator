from OCC.Core.TColStd import TColStd_Array1OfReal
from OCC.Core.TColgp import TColgp_Array1OfPnt

from .base_curves import BaseBoundedCurve

class BSpline(BaseBoundedCurve):

    @staticmethod
    def getName():
        return 'BSpline'
    
    def getIsRational(self):
        return self._shape.IsRational()
    
    def getIsClosed(self):
        return self._shape.IsClosed()
    
    def getContinuity(self):
        return self._shape.Continuity()
    
    def getDegree(self):
        return self._shape.Degree()
    
    def getPoles(self):
        k_degree = TColgp_Array1OfPnt(1, self._shape.NbPoles())
        self._shape.Poles(k_degree)
        points = [list(k_degree.Value(i+1).Coord() for i in range(k_degree.Length()))]
        return points

    def getKnots(self):
        k_degree = TColStd_Array1OfReal(1, self._shape.NbPoles() +
                                        self._shape.Degree() + 1)
        self._shape.KnotSequence(k_degree)
        knots = [k_degree.Value(i+1) for i in range(k_degree.Length())]
        return knots

    def getWeights(self):
        k_degree = TColStd_Array1OfReal(1, self._shape.NbPoles())
        self._shape.Weights(k_degree)
        weights = [k_degree.Value(i+1) for i in range(k_degree.Length())]
        return weights

    def toDict(self):        
        features = super().toDict()
        
        features['rational'] = self.getIsRational()
        features['closed'] = self.getIsClosed()
        features['continuity'] = self.getContinuity()
        features['degree'] = self.getDegree()
        features['poles'] = self.getPoles()
        features['knots'] = self.getKnots()
        features['weights'] =self.getWeights()

        return features