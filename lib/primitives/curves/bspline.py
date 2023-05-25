from OCC.Core.TColStd import TColStd_Array1OfReal
from OCC.Core.TColgp import TColgp_Array1OfPnt

from .base_curves import BaseBoundedCurve

class BSpline(BaseBoundedCurve):

    @staticmethod
    def getName():
        return 'BSpline'

    @classmethod
    def toDict(cls, adaptor, mesh_data=None, transforms=None, shape_orientation=0):        
        
        shape, features = super().toDict(adaptor, mesh_data=mesh_data,
                                         transforms=transforms, shape_orientation=shape_orientation)
        
        features['rational'] = shape.IsRational()
        features['closed'] = shape.IsClosed()
        features['continuity'] = shape.Continuity()
        features['degree'] = shape.Degree()
        features['poles'] = BSpline._getPoles(shape)
        features['knots'] = BSpline._getKnots(shape=shape)
        features['weights'] = BSpline._getWeights(shape=shape)

        return features
    
    @staticmethod
    def _getPoles(shape):
        k_degree = TColgp_Array1OfPnt(1, shape.NbPoles())
        shape.Poles(k_degree)
        points = [list(k_degree.Value(i+1).Coord() for i in range(k_degree.Length()))]
        return points

    @staticmethod
    def _getKnots(shape):
        k_degree = TColStd_Array1OfReal(1, shape.NbPoles() + shape.Degree() + 1)
        shape.KnotSequence(k_degree)
        knots = [k_degree.Value(i+1) for i in range(k_degree.Length())]
        return knots

    @staticmethod
    def _getWeights(shape):
        k_degree = TColStd_Array1OfReal(1, shape.NbPoles())
        shape.Weights(k_degree)
        weights = [k_degree.Value(i+1) for i in range(k_degree.Length())]
        return weights