from OCC.Core.TColgp import TColgp_Array2OfPnt
from OCC.Core.TColStd import TColStd_Array2OfReal

from .base_surfaces import BaseBoundedSurface

class BSplineSurface(BaseBoundedSurface):

    @staticmethod
    def getType():
        return 'BSpline'
    
    @staticmethod
    def adaptor2Geom(adaptor):
        return adaptor.BSpline()
    
    def getPoles(self):
        k_degree = TColgp_Array2OfPnt(1, self._geom.NbUPoles(), 1, self._geom.NbVPoles())
        self._geom.Poles(k_degree)
        columns = [list(list(k_degree.Value(i+1, j+1).Coord()) for j in range(k_degree.RowLength())) for i in range(k_degree.ColLength())]
        return columns

    def getUKnots(self):
        u_knots = [knots for _, knots in enumerate(self._geom.UKnots())]
        return u_knots

    def getVKnots(self):
        v_knots = [knots for _, knots in enumerate(self._geom.VKnots())]
        return v_knots

    def getWeights(self):
        k_degree = TColStd_Array2OfReal(1, self._geom.NbUPoles(), 1, self._geom.NbVPoles())
        self._geom.Weights(k_degree)
        columns = [list(k_degree.Value(i+1, j+1) for j in range(k_degree.RowLength())) for i in range(k_degree.ColLength())]
        return columns
    
    def getIsURational(self):
        return self._geom.IsURational()

    def getIsVRational(self):
        return self._geom.IsVRational()
    
    def getIsUClosed(self):
        return self._geom.IsUClosed()
    
    def getIsVClosed(self):
        return self._geom.IsVClosed()
    
    def getContinuity(self):
        return self._geom.Continuity()
    
    def getUDegree(self):
        return self._geom.UDegree()
    
    def getVDegree(self):
        return self._geom.VDegree()
        
    def toDict(self):
        features = super().toDict()
        
        features['u_rational'] = self.getIsURational()
        features['v_rational'] = self.getIsVRational()
        features['u_closed'] = self.getIsUClosed()
        features['v_closed'] = self.getIsVClosed()
        features['continuity'] = self.getContinuity()
        features['u_degree'] = self.getUDegree()
        features['v_degree'] = self.getVDegree()
        features['poles'] = self.getPoles()
        features['u_knots'] = self.getUKnots()
        features['v_knots'] = self.getVKnots()
        features['weights'] = self.getWeights()

        return features